# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that a pipeline with the WebSocketClient runs correctly."""
import asyncio
import json
import time
from typing import Dict, Optional

import pytest
import ray
import websockets

from aineko import AbstractNode, DatasetConsumer, Runner

CONNECTED_CLIENTS = set()


async def handle_client(websocket, path):
    """Handle a new client connection.

    Upon connection, add the client to the set of connected clients.
    """
    CONNECTED_CLIENTS.add(websocket)
    try:
        # Keep the connection open
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.remove(websocket)


async def send_messages_periodically(sleep):
    """Send messages to all connected clients periodically."""
    while True:
        # Check if there are any connected clients
        if CONNECTED_CLIENTS:
            message = {
                "message": "Hello World!",
                "timestamp": time.time(),
            }
            formatted_message = json.dumps(message)
            await asyncio.gather(
                *(
                    client.send(formatted_message)
                    for client in CONNECTED_CLIENTS
                )
            )
        await asyncio.sleep(sleep)


async def start_test_websocket_server(host, port, sleep):
    """Start a WebSocket server on the given host and port."""
    server = await websockets.serve(handle_client, host, port)
    await asyncio.gather(
        server.wait_closed(), send_messages_periodically(sleep)
    )


class WebSocketServer(AbstractNode):
    """Node that creates a test WebSocket server."""

    def _pre_loop_hook(self, params: Optional[Dict] = None) -> None:
        """Creates a test WebSocket server."""
        if not params:
            raise ValueError("No params provided to WebSocketServer node.")

        asyncio.run(
            start_test_websocket_server(
                host=params["host"], port=params["port"], sleep=params["sleep"]
            )
        )

    def _execute(self, params: Dict):
        """Does nothing."""
        pass


class WebSocketClientChecker(AbstractNode):
    """Node that checks that the WebSocketClient is running."""

    def _execute(self, params: Dict):
        """Checks that the WebSocketClient is running."""
        results = {}
        for msg_num in range(5):
            test_message = self.consumers["test_messages"].next()
            results[f"message_{msg_num}"] = test_message["message"]["message"]
        self.producers["test_result"].produce(results)
        self.activate_poison_pill()
        time.sleep(5)


@pytest.mark.integration
def test_websocket_client_node(start_service):
    """Integration test to check that WebSocketClient node works.

    Spin up a pipeline containing the WebSocketClient node and a
    WebSocketServer node that creates a test WebSocket server.
    The WebSocketClient node connects to the server and consumes
    messages from it and produces them to the test_messages dataset.
    """
    runner = Runner(
        pipeline_config_file="tests/extras/connectors/test_websocket_client.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="test_result",
            node_name="consumer",
            pipeline_name="test_websocket_client",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        test_results = consumer.next()
        assert test_results["message"] == {
            "message_0": "Hello World!",
            "message_1": "Hello World!",
            "message_2": "Hello World!",
            "message_3": "Hello World!",
            "message_4": "Hello World!",
        }
