import os
import json
from kafka import KafkaProducer

class PublisherSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            bootstrap_servers = os.environ.get(
                "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
            ).split(",")
            self._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8")
            )
            self._initialized = True

    def send(self, topic: str, value: dict):
        print("message sent")
        self._producer.send(topic, value)

publisher = PublisherSingleton()