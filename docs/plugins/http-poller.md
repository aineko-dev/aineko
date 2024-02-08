# HTTPPoller Node

The HTTPPoller plugin can be installed using poetry with the following command `poetry add aineko[http-poller]` or by adding the following to `pyproject.toml` and running `poetry install`:
:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.3.2", extras=["http-poller"]}
    ```

## API Reference

::: aineko_plugins.nodes.http_poller.http_poller.HTTPPoller
::: aineko_plugins.nodes.http_poller.http_poller.ParamsHTTPPoller