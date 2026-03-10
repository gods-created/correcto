from fastapi import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import URL
from typing import Callable, Awaitable
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError, ConnectionTimeoutError
from aiohttp.web_exceptions import HTTPException
from aiohttp.http_exceptions import HttpProcessingError
from redis import Redis
from redis.exceptions import ConnectionError, AuthenticationError
from loguru import logger
from os import getenv 
from datetime import timedelta

async def get_ip(path: URL) -> None:
    redis = None
    
    try:
        async with ClientSession() as session:
            async with session.get('https://v4.ident.me/') as http_request:
                http_request.raise_for_status()
                ip_address = await http_request.text(encoding='utf-8')
        
        redis = Redis(
            host=getenv('REDIS_HOST'),
            port=(getenv('REDIS_PORT', 6379)),
            db=(getenv('REDIS_DB', 0)),
            password=getenv('REDIS_PASSWORD')
        )

        if not redis.get(ip_address):
            logger.debug(f'Request called ({path}) by {ip_address}')
            redis.set(ip_address, '1', ex=timedelta(minutes=10).seconds)

    except ClientError as e:
        logger.error(f'Client Error (InterceptIPMiddleware): {str(e)}')

    except HTTPException as e:
        logger.error(f'Web Error (InterceptIPMiddleware): {e.text}')

    except HttpProcessingError as e:
        logger.error(f'HTTP Error (InterceptIPMiddleware): {e.message}')

    except (ConnectionError, AuthenticationError, ) as e:
        logger.error(f'Redis Connection Error (InterceptIPMiddleware): {str(e)}')

    finally:
        if redis:
            redis.close()

class InterceptIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.background = BackgroundTasks()
        response.background.add_task(get_ip, path=request.url)
        return response
