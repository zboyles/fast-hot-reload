import fastapi

from typing import Any, Callable, Dict, Optional

from fastapi.middleware import Middleware
from fast_hot_reload.arel import Path, HotReloadMiddleware


class BaseHotReload:
    app: Optional[fastapi.FastAPI]
    on_reload: Callable[[], None]
    use_alternate_config: bool
    ws_host_override: Optional[str]
    ws_port_override: Optional[int]

    @staticmethod
    def register_middleware(
        app: fastapi.FastAPI,
        *,
        on_reload: Callable[[], None] = lambda: None,
        use_alternate_config: bool = False,
        ws_host_override: Optional[str] = None,
        ws_port_override: Optional[int] = None,
        **kwargs: Dict[str, Any]
    ) -> fastapi.FastAPI:
        app.user_middleware.append(
            Middleware(
                cls=HotReloadMiddleware,
                paths=[
                    Path(
                        path="./",
                        on_reload=[on_reload],
                        use_alternate_config=use_alternate_config,
                        host=ws_host_override,
                        port=ws_port_override,
                    )
                ],
                **kwargs
            )
        )
        return app

class FastHotReload(BaseHotReload):
    """Add client-side hot reload to FastAPI

        Parameters:
            app: An optional app object if using an existing parent FastAPI application.
            on_reload: An optional callback function that is executed when changes are detected.
            use_alternate_config: If hot reload is not working, try setting this to True. Note: Not intended for use with 'ws_host_override' or 'ws_port_override'.
            ws_host_override: The host of the hot reload websocket endpoint. This is only needed if dev server uses a proxy or named host.
            ws_port_override: The port of the hot reload websocket endpoint. This is only needed if dev server uses a proxy or named host.
        Example:
            # site.py
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse
            
            app = FastAPI()
            
            @app.get("/")
            async def index():
                return HTMLResponse("<html><body>Hello Hot Reload</body></html>")
            
            FastHotReload(app=app)
            # Run `uvicorn site:app --reload`
        """

    def __init__(
        self,
        app: Optional[fastapi.FastAPI] = None,
        *,
        on_reload: Callable[[], None] = lambda: None,
        use_alternate_config: bool = False,
        ws_host_override: Optional[str] = None,
        ws_port_override: Optional[int] = None,
        **kwargs: Dict[str, Any]
    ) -> None:
        """Add client-side hot reload to FastAPI"""
        super().__init__()
        self.app = app if isinstance(app, fastapi.FastAPI) else fastapi.FastAPI()
            
        self.on_reload = on_reload
        self.use_alternate_config = use_alternate_config
        self.ws_host_override = ws_host_override
        self.ws_port_override = ws_port_override
        self.app = self.register_middleware(
            app=self.app,
            on_reload=self.on_reload,
            use_alternate_config=self.use_alternate_config,
            ws_host_override=self.ws_host_override,
            ws_port_override=self.ws_port_override,
            **kwargs
        )

    def __call__(self, *args: Any, **kwds: Any) -> fastapi.FastAPI:
        return self.app


