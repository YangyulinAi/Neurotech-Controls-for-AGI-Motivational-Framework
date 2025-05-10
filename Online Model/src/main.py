# online/src/main.py
import asyncio
import yaml
import time
import numpy as np
import threading
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s │ %(message)s",
    level=logging.DEBUG
)
logging.getLogger('websockets.protocol').setLevel(logging.DEBUG)

from .utils.log_helper import setup_logger
from .lsl_receiver import LSLReceiver
from .preprocess import Preprocessor, extract_feats
from .onnx_runner import ONNXRunner
from .websocket_server import WebSocketServer
from .mqtt_publisher import MQTTPublisher
from .api_rest import update_last

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
    runner = ONNXRunner(cfg['model_path'])
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

        # Print predictions to console
        #logger.info(f"Predicted VA → valence={out[0]:.3f}, arousal={out[1]:.3f}")

        # 5) Prepare result JSON
        result = {
            'ts': time.time(),
            'valence': float(out[0]),
            'arousal': float(out[1]),
            'version': cfg['version']
        }

        # 6) Broadcast and publish
        update_last(result)

        await ws.broadcast(result)
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
    cfg['version'] = 'va-regressor@1.3.0'
    # Run the asynchronous inference loop
    asyncio.run(infer_loop(cfg, logger))
