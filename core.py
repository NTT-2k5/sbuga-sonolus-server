import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.datastructures import State
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from helpers.repository_map import repo
from helpers.api import SbugaAPI
from locales.locale import Loc, Locale
from helpers.config_loader import get_config
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, ParamSpec, Callable

config = get_config()

R = TypeVar("R")
P = ParamSpec("P")


class SonolusFastAPI(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = kwargs["debug"]

        self.executor = ThreadPoolExecutor(max_workers=16)

        self.config = config["sonolus"]
        self.api_config = config["api"]
        self.base_url = kwargs["base_url"]

        self.remove_config_queries = [
            "localization",
            "showspoilers",
            "levelbg",
        ]

        self.repository = repo

        self.exception_handlers.setdefault(HTTPException, self.http_exception_handler)
        self.exception_handlers.setdefault(Exception, self.general_exception_handler)

        self.api: SbugaAPI

    async def run_blocking(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, lambda: func(*args, **kwargs)
        )

    def get_items_per_page(self, route: str) -> int:
        return self.config["items-per-page"].get(
            route, self.config["items-per-page"].get("default")
        )

    async def http_exception_handler(self, request: Request, exc: HTTPException):
        if exc.status_code != 500:
            return JSONResponse(
                content={"message": exc.detail}, status_code=exc.status_code
            )
        else:
            import traceback

            print(
                "-" * 100
                + f"\nerror 500: {request.method} {str(request.url)}\n"
                + traceback.format_exc()
                + "-" * 100
            )
            return JSONResponse(content={}, status_code=exc.status_code)

    async def general_exception_handler(self, request: Request, exc: Exception):
        import traceback

        print(
            "-" * 100
            + f"\nerror 500: {request.method} {str(request.url)}\n"
            + traceback.format_exc()
            + "-" * 100
        )
        return JSONResponse(content={}, status_code=500)

    def include_router(self, router, *args, **kwargs):
        for route in router.routes:
            if isinstance(route, APIRoute):
                route.response_model_exclude_none = True

        return super().include_router(router, *args, **kwargs)


class _RequestState(State):
    localization: str
    show_spoilers: bool
    levelbg: str
    loc: Loc


class SonolusRequest(Request):
    state: _RequestState
    app: SonolusFastAPI


class SonolusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: SonolusRequest, call_next):
        request.state.localization = request.query_params.get(
            "localization", "en"
        ).lower()

        show_spoilers_raw = request.query_params.get("showspoilers", "0")
        request.state.show_spoilers = show_spoilers_raw == "1"

        levelbg = request.query_params.get("levelbg", "v3")
        request.state.levelbg = levelbg if levelbg in ("v3", "v1", "black") else "v3"

        request.state.loc, request.state.localization = Locale.get_messages(
            request.state.localization
        )

        query_params = dict(request.query_params)
        for item in request.app.remove_config_queries:
            query_params.pop(item, None)
        request.state.query_params = query_params
        response = await call_next(request)
        response.headers["Sonolus-Version"] = request.app.config[
            "required-client-version"
        ]
        return response
