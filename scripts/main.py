# online/src/main.py
import asyncio
import yaml
import time
import numpy as np
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from pylsl import resolve_stream, StreamInlet

#logging.basicConfig(
#    format="%(asctime)s %(levelname)s %(name)s │ %(message)s",
#    level=logging.DEBUG
#)
#logging.getLogger('websockets.protocol').setLevel(logging.DEBUG)

from .tools.log_helper import setup_logger
from .lsl_receiver import LSLReceiver
from .preprocess import Preprocessor, extract_feats
from .onnx_runner import ONNXRunner
# Removed WebSocket and MQTT for Express server integration
# from .websocket_server import WebSocketServer
# from .mqtt_publisher import MQTTPublisher
# from .api_rest import update_last

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
    logger.info("Initializing LSL receiver for EEG device connection...")
    try:
        lsl = LSLReceiver(cfg['sampling_rate'], cfg['window_size'], cfg['n_channels'], logger)
        threading.Thread(target=lsl.start, daemon=True).start()
        logger.info("LSL receiver started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LSL receiver: {e}")
        logger.error("Please ensure an EEG device is connected and streaming via LSL")
        raise e

    pre = Preprocessor(cfg['sampling_rate'], cfg['bandpass']['low'], cfg['bandpass']['high'])
    # P0 Requirement: GPU/CPU auto-switching
    runner = ONNXRunner(cfg['model_path'], use_gpu=cfg.get('use_gpu', True))
    
    logger.info("Real-time EEG analysis initialized, waiting for device data...")

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

        # P0 Requirement: Submit async Φ computation (commented out for Express integration)
        # phi_executor.submit(calc_phi_and_send, filtered.T, current_timestamp, ws, logger)

        # 7) Send to Express server via HTTP API
        try:
            # Send data to Express server's broadcast endpoint
            import requests
            broadcast_response = requests.post('http://localhost:5000/api/bci/broadcast', 
                json={
                    'valence': float(out[0]),
                    'arousal': float(out[1]),
                    'phi': 0.0,  # Placeholder
                    'timestamp': current_timestamp,
                    'type': 'bci_data'
                }, timeout=1)
            
            if broadcast_response.status_code == 200:
                logger.debug(f"Data broadcasted to Express server: V={out[0]:.3f}, A={out[1]:.3f}")
            else:
                logger.warning(f"Failed to broadcast to Express server: {broadcast_response.status_code}")
                
        except Exception as e:
            logger.error(f"Error broadcasting to Express server: {e}")
        
        # Wait until the next step
        await asyncio.sleep(cfg['step_size'])

if __name__ == '__main__':
    # Set up logging
    logger = setup_logger(__name__)
    # Load configuration
    with open('configs/runtime.yaml') as f:
        cfg = yaml.safe_load(f)
    
    # Dynamic channel detection from LSL stream
    try:
        logger.info("Detecting EEG stream channels dynamically...")
        streams = resolve_stream('type', 'EEG', timeout=10.0)
        if not streams:
            logger.warning("No EEG stream found for channel detection, using default 8 channels")
            cfg['n_channels'] = 8  # Default for X.on
        else:
            inlet = StreamInlet(streams[0])
            detected_channels = inlet.info().channel_count()
            cfg['n_channels'] = detected_channels
            logger.info(f"Detected {detected_channels} channels from LSL stream: {streams[0].name()}")
            inlet.__del__()  # Clean up detection inlet
    except Exception as e:
        logger.warning(f"Channel detection failed: {e}. Using default 8 channels for X.on")
        cfg['n_channels'] = 8
    
    # Run the inference loop
    asyncio.run(infer_loop(cfg, logger))