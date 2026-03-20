from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable, Awaitable

class Error500Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        if response.status_code == 500:
            return HTMLResponse(
                content=open('./templates/serverError.html', mode='r').read(),
                status_code=500
            )
        
        return response