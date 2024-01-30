# WebSocketClient Node

The WebSocketClient extra node can be used by adding the following to `pyproject.toml`

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.2.7", extras=["websocket_client"]}
    ```

## API Reference

::: aineko.extras.connectors.websocket_client.WebSocketClient
::: aineko.extras.connectors.websocket_client.ParamsWebSocketClient