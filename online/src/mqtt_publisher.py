# online/src/mqtt_publisher.py
import paho.mqtt.client as mqtt
import json
import logging

class MQTTPublisher:
    def __init__(self, broker, port, topic, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        if not broker:
            self.logger.warning("MQTT broker not configured – skipping MQTT publisher")
            self.client = None
            return
        import paho.mqtt.client as mqtt
        self.client = mqtt.Client()
        try:
            self.client.connect(broker, port)
            self.logger.info(f"Connected to MQTT broker {broker}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            self.client = None

    def publish(self, message: dict):
        if not self.client:
            return
        payload = json.dumps(message)
        self.client.publish(self.topic, payload)
