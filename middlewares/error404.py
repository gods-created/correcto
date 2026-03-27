from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi.responses import JSONResponse
from fastapi import status
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable, Awaitable

class Error404Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        if response.status_code == 404:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    'err_description': 'Page didn\'t find'
                }
            )
        
        return response