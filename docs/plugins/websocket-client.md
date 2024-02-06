# WebSocketClient Node

The WebSocketClient extra node can be used by adding the following to `pyproject.toml`

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.3.0", extras=["websocket_client"]}
    ```

## API Reference

::: aineko_plugins.nodes.websocket_client.WebSocketClient
::: aineko_plugins.nodes.websocket_client.websocket_client.ParamsWebSocketClient