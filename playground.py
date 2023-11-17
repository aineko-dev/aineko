# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
import time

from confluent_kafka import Consumer, Message, Producer

from aineko.config import DEFAULT_KAFKA_CONFIG


def create_consumer():
    consumer = Consumer(
        {**DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG"), "group.id": "test"}
    )
    consumer.subscribe(["test"])


def consume(consumer):
    consumer.poll(timeout=0)
    return


producer = Producer(
    {**DEFAULT_KAFKA_CONFIG.get("PRODUCER_CONFIG"), "group.id": "test"}
)
for i in range(1000):
    producer.produce("test", value=str(i).encode("utf-8"))
    producer.flush()

start = time.time()
for i in range(1000):
    create_consumer()
print(f"create_consumer: {time.time() - start}")


consumer = Consumer(
    {**DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG"), "group.id": "test"}
)
consumer.subscribe(["test"])
start = time.time()
for i in range(1000):
    consume(consumer)
print(f"consume: {time.time() - start}")
