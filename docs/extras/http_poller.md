# HTTPPoller Node

The HTTPPoller extra node can be used by adding the following to `pyproject.toml`

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.2.7", extras=["http_poller"]}
    ```

## API Reference

::: aineko.extras.connectors.http_poller.HTTPPoller
::: aineko.extras.connectors.http_poller.ParamsHTTPPoller