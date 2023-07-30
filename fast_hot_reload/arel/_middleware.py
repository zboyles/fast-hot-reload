import asyncio
import functools
import logging
import pathlib
import string
import textwrap
import warnings
import pkg_resources

from typing import Callable, List, Sequence

from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send
from starlette.websockets import WebSocket

from ._models import Path, ArelClient
from ._types import ReloadFunc
from ._watch import ChangeSet, FileWatcher

logger = logging.getLogger(__name__)

SCRIPT_TEMPLATE_PATH = pathlib.Path(pkg_resources.resource_filename(package_or_requirement=__name__, resource_name="data/client.js"))
assert SCRIPT_TEMPLATE_PATH.exists()



class _Template(string.Template):
    delimiter = "$arel::"


class HotReloadMiddleware(ArelClient):
    use_alternate_config: bool
    host: str
    port: int

    def __init__(self, app: Callable, *, paths: Sequence[Path] = (), **kwargs) -> None:
        super().__init__(**kwargs)
        self._app = app

        self._watchers = [
            FileWatcher(
                path,
                on_change=functools.partial(
                    self._on_changes, on_reload=on_reload),  # , host=host, port=port),  # type: ignore
            )
            for path, on_reload, use_alternate_config, host, port in paths
        ]
        for path, on_reload, use_alternate_config, host, port in paths:
            self.use_alternate_config = use_alternate_config
            self.host = host or ""
            self.port = port or 0

    async def _on_changes(
        self, changeset: ChangeSet, *, on_reload: List[ReloadFunc]
    ) -> None:
        description = ", ".join(
            f"file {event} at {', '.join(f'{event!r}' for event in changeset[event])}"
            for event in changeset
        )
        logger.warning("Detected %s. Triggering reload...", description)

        # Run server-side hooks first.
        for callback in on_reload:
            await callback()

        await self._ws_notify_hot_reload.notify()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
        else:
            assert scope["type"] == "http"
            await self._handle_http(scope, receive, send)

    async def _startup(self) -> None:
        try:
            for watcher in self._watchers:
                await watcher.startup()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while starting hot reload: %r", exc)
            raise

    async def _shutdown(self) -> None:
        try:
            for watcher in self._watchers:
                await watcher.shutdown()
        except BaseException as exc:  # pragma: no cover
            logger.error("Error while stopping hot reload: %r", exc)
            raise

    async def _handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        async def wrapped_receive() -> Message:
            message = await receive()

            if message["type"] == "lifespan.startup":
                await self._startup()

            if message["type"] == "lifespan.shutdown":
                await self._shutdown()

            return message

        await self._app(scope, wrapped_receive, send)

    async def _watch_reloads(self, ws: WebSocket) -> None:
        async for _ in self._ws_notify_hot_reload.watch():
            await ws.send_text("reload")

    async def _wait_client_disconnect(self, ws: WebSocket) -> None:
        async for _ in ws.iter_text():
            pass  # pragma: no cover

    async def _handle_websocket(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["path"].rstrip("/") != self._ws_path:
            await self._app(scope, receive, send)
            return

        ws = WebSocket(scope, receive, send)

        await ws.accept()

        tasks = [
            asyncio.create_task(self._watch_reloads(ws)),
            asyncio.create_task(self._wait_client_disconnect(ws)),
        ]
        (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        [task.cancel() for task in pending]
        [task.result() for task in done]

    def _get_script(self, scope: Scope) -> bytes:
        if not hasattr(self, "_script_template"):
            self._script_template = _Template(SCRIPT_TEMPLATE_PATH.read_text())

        scheme = {
            "http": "ws",
            "https": "wss",
        }[scope["scheme"]]
        # NOTE: 'server' is optionaly in the ASGI spec. In practice,
        # we assume it is effectively provided by server implementations.
        host, port = scope["server"]
        path = self._ws_path
        try:
            host = self.host if self.host is not None and not self.host == "" else host
        except:
            pass
        try:
            port = self.port if self.port is not None and not self.port == 0 else port
        except:
            pass

        if self.use_alternate_config:
            try:
                _host = ""
                for header in scope["headers"]:
                    if header[0] == b"host":
                        _host = header[1].decode("utf-8")
                        break
                if _host == "":
                    raise Exception("no host found in headers")
                full_host = _host.split(":")
                host = full_host[0].strip()
                port = full_host[1].strip()
            except:
                print("error parsing host from headers")

        url = f"{scheme}://{host}:{port}{path}"

        js = self._script_template.substitute(
            {
                "WS_URL": url,
                "WS_RECONNECT_INTERVAL": self._ws_reconnect_interval,
                "WS_MESSAGE_PREFIX": self._ws_message_prefix,
                "WS_CONNECTED_MESSAGE": self._ws_connected_message,
                "WS_RECONNECT_MESSAGE": self._ws_reconnect_message,
            }
        )
        config_message = f"\t  HotReloadMiddleware configuration:\n\t   use_alternate_config: {self.use_alternate_config}\n\t   -host: {host}\n\t   -port: {port}\n\t   -path: {path}"
        print(config_message)

        return f'<script type="text/javascript">{js}</script>'.encode("utf-8")

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        script = self._get_script(scope)
        inject_script = False

        async def wrapped_send(message: Message) -> None:
            nonlocal inject_script

            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message["headers"])

                if headers.get("content-type", "").partition(";")[0] != "text/html":
                    # This is not HTML.
                    await send(message)
                    return

                if headers.get("transfer-encoding") == "chunked":
                    # Ignore streaming responses.
                    await send(message)
                    return

                if headers.get("content-encoding"):
                    msg = textwrap.dedent(
                        f"""
                        Cannot inject reload script into response encoded as {headers['content-encoding']!r}.

                        HINT: 'HotReloadMiddleware' must be placed inside any content-encoding middleware, such as:

                        middleware = [
                            Middleware(GZipMiddleware),
                            Middleware(HotReloadMiddleware, ...),
                        ]
                        """  # noqa: E501
                    )
                    warnings.warn(msg)

                    await send(message)
                    return

                inject_script = True

                if "content-length" in headers:
                    new_length = int(headers["content-length"]) + len(script)
                    headers["content-length"] = str(new_length)

                await send(message)

            else:
                assert message["type"] == "http.response.body"

                if not inject_script:
                    await send(message)
                    return

                if message.get("more_body", False):
                    raise RuntimeError("Unexpected streaming response")

                body: bytes = message["body"]

                try:
                    start = body.index(b"</body>")
                except ValueError:
                    await send(message)
                    return

                head = body[:start]
                tail = body[start:]

                message["body"] = head + script + tail
                await send(message)

        await self._app(scope, receive, wrapped_send)
