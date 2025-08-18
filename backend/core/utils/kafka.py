from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
import socket
from core.database import get_elastic_db
from core.config import logging
# Kafka Availability Check
def is_kafka_available(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logging.critical((f"[Kafka Check] Connection failed: {e}")
        return False


# Kafka Consumer
class KafkaConsumer:
    def __init__(self, broker: str, topic: str, group_id: str, es):
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.es = None
        self.consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.broker,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self.consumer.start()
        logging.info("[Kafka Consumer] Started.")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logging.info("[Kafka Consumer] Stopped.")

    async def consume(self):
        try:
            if not self.consumer:
                raise RuntimeError("Consumer has not been started.")

            async for message in self.consumer:
                try:
                    payload = json.loads(message.value.decode())
                    logging.info(f"[Kafka Consumer] Received message: {payload}")

                    if payload.get("action") == "create":
                        product_data = payload.get("product")
                        if product_data:
                            self.es = await get_elastic_db()
                            
                            await self.es.index(
                                index="products",
                                id=product_data["id"],
                                document=product_data
                            )
                            logging.info(f"[Kafka Consumer] Indexed product {product_data['id']} into Elasticsearch.")
                except Exception as inner_ex:
                    logging.error(f"[Kafka Consumer] Error processing message: {inner_ex}")
        except Exception as e:
            logging.critical(f"[Kafka Consumer] Fatal error: {e}")


# Kafka Producer
class KafkaProducer:
    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.broker)
        await self.producer.start()
        logging.info("[Kafka Producer] Started.")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logging.info("[Kafka Producer] Stopped.")

    async def send(self, message: dict):
        if not self.producer:
            raise RuntimeError("Producer is not started.")
        try:
            await self.producer.send_and_wait(self.topic, json.dumps(message).encode())
            logging.info(f"[Kafka Producer] Message sent.-> {message}")
        except Exception as e:
            logging.error(f"[Kafka Producer] Failed to send message: {e}")
            raise


# Helper function to send Kafka messages
async def send_kafka_message(kafka_producer: KafkaProducer, message: dict):
    try:
        await kafka_producer.send(message)
        logging.info("[Kafka Helper] Message sent successfully.")
    except Exception as e:
        logging.error(f"[Kafka Helper] Error sending message: {e}")
