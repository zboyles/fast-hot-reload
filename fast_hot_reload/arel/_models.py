from typing import NamedTuple, Sequence, Union, Callable

from ._types import ReloadFunc
from ._notify import Notify


class Path(NamedTuple):
    path: str
    on_reload: Sequence[ReloadFunc] = ()
    use_alternate_config: bool = False
    host: Union[str, None] = None
    port: Union[int, None] = None


_ws_reconnect_interval_key: str = "_ws_reconnect_interval"
_ws_path_key: str = "_ws_path"
_ws_notify_hot_reload_key: str = "_ws_notify_hot_reload"
_ws_message_prefix_key: str = "_ws_message_prefix"
_ws_connected_message_key: str = "_ws_connected_message"
_ws_reconnect_message_key: str = "_ws_reconnect_message"

_WS_RECONNECT_INTERVAL_DEFAULT: float = 1.0
_WS_PATH_DEFAULT: str = "/__arel__"
_WS_NOTIFY_HOT_RELOAD_FN_DEFAULT: Callable[[], Notify] = lambda: Notify()
_WS_MESSAGE_PREFIX_DEFAULT: str = "[arel]"
_WS_CONNECTED_MESSAGE: str = "Connected."
_WS_RECONNECT_MESSAGE: str = "WebSocket reconnecting in ${reconnectInterval} seconds..."

class ArelClient:

    def __init__(self, **kwargs):
        """
        Initialize the client.

        Supported kwargs:

        - _ws_reconnect_interval (float): Time in secs between reconnections. Default 1.0.
        - _ws_path (str): Path to connect websocket. Default "/__arel__".
        - _ws_notify_hot_reload (Callable): Function to notify hot reload.
        - _ws_message_prefix (str): Prefix for websocket messages. 
        - _ws_connected_message (str): Message on connect.
        - _ws_reconnect_message (str): Message on reconnect. Use '${reconnectInterval}' for dynamic reconnect interval.
        """
        VALID_KWARG_KEYS = {
            _ws_reconnect_interval_key,
            _ws_path_key,
            _ws_notify_hot_reload_key,
            _ws_message_prefix_key,
            _ws_connected_message_key,
            _ws_reconnect_message_key,
        }

        # Validate keys
        invalid_keys = set(kwargs) - set(VALID_KWARG_KEYS)
        if invalid_keys:
            raise ValueError(f"Invalid kwargs: {invalid_keys}")

        # Set defaults
        self._ws_reconnect_interval: float = kwargs.pop(_ws_reconnect_interval_key, _WS_RECONNECT_INTERVAL_DEFAULT)
        self._ws_path: str = kwargs.pop(_ws_path_key, _WS_PATH_DEFAULT)  # No collision risk with user routes.
        self._ws_notify_hot_reload: Notify = kwargs.pop(_ws_notify_hot_reload_key, _WS_NOTIFY_HOT_RELOAD_FN_DEFAULT())
        self._ws_message_prefix: str = kwargs.pop(_ws_message_prefix_key, _WS_MESSAGE_PREFIX_DEFAULT)
        self._ws_connected_message: str = kwargs.pop(_ws_connected_message_key, _WS_CONNECTED_MESSAGE)
        self._ws_reconnect_message: str = kwargs.pop(_ws_reconnect_message_key, _WS_RECONNECT_MESSAGE)


