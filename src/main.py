# online/src/main.py
import asyncio
import yaml
import time
import numpy as np
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

#logging.basicConfig(
#    format="%(asctime)s %(levelname)s %(name)s │ %(message)s",
#    level=logging.DEBUG
#)
#logging.getLogger('websockets.protocol').setLevel(logging.DEBUG)

from .utils.log_helper import setup_logger
from .lsl_receiver import LSLReceiver
from .preprocess import Preprocessor, extract_feats
from .onnx_runner import ONNXRunner
from .websocket_server import WebSocketServer
from .mqtt_publisher import MQTTPublisher
from .api_rest import update_last

# P0 Requirement: Initialize ThreadPoolExecutor for async Φ computation
phi_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="phi_compute")

def calc_phi_and_send(eeg_chunk, timestamp, websocket_server, logger):
    """
    P0 Requirement: Async Φ computation and broadcasting
    Calculate Φ in background thread and send update via WebSocket
    """
    try:
        # Import here to avoid circular imports
        from .phi_estimator import PhiEstimator
        
        # Initialize Φ estimator with fast method for real-time
        phi_estimator = PhiEstimator(method='mock')  # Use mock for performance
        
        # Compute Φ on limited channels for performance
        phi_value = phi_estimator.estimate_phi(eeg_chunk[:8])  # First 8 channels
        
        # Prepare Φ update message
        phi_update = {
            'type': 'phi_update',
            'payload': {
                'timestamp': timestamp,
                'phi': float(phi_value),
                'method': 'mock'
            }
        }
        
        # Send async update via WebSocket
        asyncio.create_task(websocket_server.broadcast(phi_update))
        logger.debug(f"Φ computed and sent: {phi_value:.4f}")
        
    except Exception as e:
        logger.error(f"Φ computation failed: {e}")
        # Send error notification
        error_update = {
            'type': 'phi_error',
            'payload': {
                'timestamp': timestamp,
                'phi': 0.0,
                'error': str(e)
            }
        }
        asyncio.create_task(websocket_server.broadcast(error_update))

async def infer_loop(cfg, logger):
    """
    Main inference loop:
      1. Pull data from LSL
      2. Preprocess (bandpass + standardization)
      3. Extract features
      4. Run ONNX model inference
      5. Broadcast results via WebSocket and MQTT
      6. Update REST API cache
    """
    # Initialize modules
    lsl = LSLReceiver(cfg['sampling_rate'], cfg['window_size'], cfg['n_channels'], logger)
    threading.Thread(target=lsl.start, daemon=True).start()

    pre = Preprocessor(cfg['sampling_rate'], cfg['bandpass']['low'], cfg['bandpass']['high'])
    # P0 Requirement: GPU/CPU auto-switching
    runner = ONNXRunner(cfg['model_path'], use_gpu=cfg.get('use_gpu', True))
    ws = WebSocketServer(cfg['websocket']['host'], cfg['websocket']['port'], logger)
    mqtt = MQTTPublisher(cfg['mqtt']['broker'], cfg['mqtt']['port'], cfg['mqtt']['topic'], logger)

    # Start WebSocket server
    server = ws.start()
    asyncio.ensure_future(server)

    # Compute window length and step size in samples
    length = int(cfg['sampling_rate'] * cfg['window_size'])

    while True:
        # 1) Fetch the latest window of data
        data = lsl.ring.get(length)  # shape: (n_samples, n_channels)
        # 2) Preprocess
        filtered = pre.transform(data)
        # 3) Extract features consistent with offline pipeline
        spec3, de_vec = extract_feats(filtered.T, cfg['sampling_rate'])
        # Reshape for model input
        spec3 = spec3[np.newaxis, ...]  # shape: (1, 3, 224, 224)
        de_vec = de_vec[np.newaxis, :]  # shape: (1, 26)
        # 4) Perform model inference
        out = runner.predict(spec3, de_vec)[0]
        current_timestamp = time.time()

        # P0 Requirement: Print predictions with Φ computing message
        logger.info(f"Predicted VA → valence={out[0]:.3f}, arousal={out[1]:.3f}, Φ=computing...")

        # P0 Requirement: Prepare result JSON with Φ field
        result = {
            'ts': current_timestamp,
            'valence': float(out[0]),
            'arousal': float(out[1]),
            'phi': 0.0,  # Placeholder - updated by async computation
            'version': cfg['version']
        }

        # P0 Requirement: Prepare frontend data with Φ field  
        frontend_data = {
            'type': 'bci_data',
            'payload': {
                'valence': float(out[0]),
                'arousal': float(out[1]),
                'phi': 0.0,  # Placeholder
                'sessionId': 'live_session'
            }
        }

        # P0 Requirement: Submit async Φ computation
        phi_executor.submit(calc_phi_and_send, filtered.T, current_timestamp, ws, logger)

        # 7) Broadcast and publish with Φ field
        update_last(result)
        await ws.broadcast(result)
        await ws.send_to_frontend(frontend_data)
        mqtt.publish(result)
        # Wait until the next step
        await asyncio.sleep(cfg['step_size'])

if __name__ == '__main__':
    # Set up logging
    logger = setup_logger(__name__)
    # Load configuration
    with open('config/runtime.yaml') as f:
        cfg = yaml.safe_load(f)
    cfg['n_channels'] = 62
    # Run the inference loop
    asyncio.run(infer_loop(cfg, logger))