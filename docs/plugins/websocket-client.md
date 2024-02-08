# WebSocketClient Node

The WebSocketClient plugin can be installed using poetry with the following command `poetry add aineko[websocket-client]` or by adding the following to `pyproject.toml` and running `poetry install`:

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.3.2", extras=["websocket-client"]}
    ```

## API Reference

::: aineko_plugins.nodes.websocket_client.WebSocketClient
::: aineko_plugins.nodes.websocket_client.websocket_client.ParamsWebSocketClient