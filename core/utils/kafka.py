from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json



class KafkaConsumer:
    def __init__(self, broker: str, topic: str, group_id: str):
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.broker,
            group_id=self.group_id,
        )
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        if self.consumer:
            async for message in self.consumer:
                # Handle message (deserialize)
                message_value = json.loads(message.value.decode())
                print(f"Received message: {message_value}")

# Usage example:
# kafka_consumer = KafkaConsumer(broker="localhost:9092", topic="your_topic", group_id="your_group")
# await kafka_consumer.start()
# await kafka_consumer.consume()




class KafkaProducer:
    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.broker)
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send(self, message: dict):
        if self.producer:
            await self.producer.send_and_wait(self.topic, json.dumps(message).encode())

# Usage example:
# kafka_producer = KafkaProducer(broker="localhost:9092", topic="your_topic")
# await kafka_producer.start()
# await kafka_producer.send({"key": "value"})
# await kafka_producer.stop()

# | User Service Action      | Kafka Event Produced      | Consumed By                 |
# | ------------------------ | ------------------------- | --------------------------- |
# | User signed up           | `UserCreated`             | Notification, Analytics     |
# | User updated profile     | `UserUpdated`             | Recommendation, Analytics   |
# | User logged in/out       | `UserLogin`, `UserLogout` | Audit, Security, Analytics  |
# | User deleted/deactivated | `UserDeleted`             | Account management services |

API Gateway: Auth, routing, throttling

Services (microservices or modular monolith):

User Service: Auth, registration, JWT

Product Service: Catalog, search (with optional Elasticsearch)

Order Service: Checkout, order lifecycle

Payment Service: Integrations with Stripe/PayPal
Notification Service: Email/SMS using Kafka or RabbitMQ
Analytics Service:


{
  "user_events": [
    "user.created",
    "user.verified",
    "user.activated",
    "user.deactivated",
    "user.deleted",
    "user.banned",
    "user.unbanned",

    "user.updated",
    "user.email.changed",
    "user.email.verified",
    "user.phone.changed",
    "user.phone.verified",
    "user.password.changed",
    "user.username.changed",
    "user.role.changed",

    "user.logged_in",
    "user.logged_out",
    "user.login_failed",
    "user.mfa.enabled",
    "user.mfa.disabled",
    "user.session.expired",
    "user.account.locked",
    "user.account.unlocked",

    "user.subscribed_to_newsletter",
    "user.unsubscribed_from_newsletter",
    "user.accepted_terms",
    "user.revoked_consent",

    "user.invited",
    "user.invitation.accepted",
    "user.joined_organization",
    "user.left_organization",
    "user.plan.upgraded",
    "user.plan.downgraded"
  ]
}
