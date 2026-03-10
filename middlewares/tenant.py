from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable, Awaitable

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        url = request.url
        if not str(url).replace('/', '').endswith('api'):
            return await call_next(request)

        host = request.url.hostname
        
        try:
            subdomain, domain = str(host).split('.')
            request.state.tenant = subdomain
        except:
            pass 

        return await call_next(request)