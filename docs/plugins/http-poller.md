# HTTPPoller Node

The HTTPPoller extra node can be used by adding the following to `pyproject.toml`

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.3.0", extras=["http-poller"]}
    ```

## API Reference

::: aineko_plugins.nodes.http_poller.http_poller.HTTPPoller
::: aineko_plugins.nodes.http_poller.http_poller.ParamsHTTPPoller