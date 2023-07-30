
# Fast Hot Reload for FastAPI

This package provides client-side hot reload functionality for FastAPI applications. 

## Installation

```
pip install fast-hot-reload
```

## Usage

Import `FastHotReload` and instantiate it, passing your FastAPI app instance:

```python
from fastapi import FastAPI
from fast_hot_reload import FastHotReload

app = FastAPI()

# Basic usage
FastHotReload(app)

# If not connecting, try alternate config:
FastHotReload(app=app, use_alternate_config=True)

# For non-standard, proxies or remote dev servers
FastHotReload(
    app,
    ws_host_override="custom_host",
    ws_port_override=8000,
)

# Note: use_alternate_config is incompatible with host/port overrides
```

Now when you run your app with `uvicorn --reload`, changes will trigger an automatic browser reload.

## Options

- `on_reload`: Callback invoked when a reload is triggered
- `use_alternate_config`: Try this if reload is not working as expected 
- `ws_host_override`: Websocket host if using a proxy
- `ws_port_override`: Websocket port if using a custom port

## Advanced Usage
The `FastHotReload` constructor accepts serveral advanced keyword arguments to further customize event language:
Here is a section on the advanced kwargs usage:

```python
FastHotReload(
  app,

  # Custom messaging
  ws_message_prefix="[Hot Reload]",
  ws_connected_message="Connected!",
  ws_reconnect_message="Reconnecting in ${reconnectInterval} seconds...",
  
  # Performance
  _ws_reconnect_interval=5, # seconds
)
```

- `ws_message_prefix` - Prefix for websocket messages
- `ws_connected_message` - Message on initial connect 
- `ws_reconnect_message` - Message on reconnect. `${reconnectInterval}` is dynamically replaced.
- `_ws_reconnect_interval` - Interval in sec between reconnect attempts

These can be used to integrate with a non-standard dev server setup.

## How it works

- Implements a FastAPI middleware 
- Opens a websocket connection to the dev server 
- Listens for file change events
- Triggers browser reload when changes are detected

## Contributing

Contributions welcome! Please open issues and/or PRs.

## License

MIT