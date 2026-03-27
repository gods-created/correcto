from fastapi import FastAPI, Request, status
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from middlewares import InterceptIPMiddleware, TenantMiddleware, Error500Middleware, Error404Middleware
from uvicorn import run
from dotenv import load_dotenv
from loguru import logger
from decorators import if_tenant_exists
from routers import python_routers
from fastapi.openapi.utils import get_openapi
from configs import TITLE, VERSION, DESCRIPTION
from fastapi.openapi.docs import get_swagger_ui_html

load_dotenv()

correcto = FastAPI(
    title=TITLE,
    description=DESCRIPTION,
    version=VERSION,
    docs_url=None,
    redoc=None,
)

correcto.add_middleware(Error500Middleware)
correcto.add_middleware(Error404Middleware)
correcto.add_middleware(
    CORSMiddleware,
    allow_headers=['*'],
    allow_methods=['*'],
    allow_origins=['*']
)
# correcto.add_middleware(InterceptIPMiddleware)
correcto.add_middleware(TenantMiddleware)

@correcto.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc) -> Response:
    return JSONResponse(
        content={'err_description': str(exc.detail)},
        status_code=exc.status_code
    )

@correcto.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # logger.error(f'Validation Error Object: \'{exc.errors()[0]}\'')

    error = exc.errors()[0].get('msg')

    if ',' in error:
        error_paths = error.split(', ')
        error = error_paths[1] if 1 in range(len(error_paths)) else error_paths[0]

    return JSONResponse(
        content={'err_description': error},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

for router in [*python_routers, ]:
    correcto.include_router(router)

@correcto.get(path='/openapi/{tenant}.json')
@if_tenant_exists
def custom_openapi(tenant: str, request: Request) -> Response:
    openapi_schema = get_openapi(
        title=TITLE + f': {tenant.capitalize()} tenant',
        version=VERSION,
        routes=correcto.routes,
    )

    filtered_paths = {}
    for path, methods in openapi_schema['paths'].items():
        tags = (
            methods.get('get', {}).get('tags', []) or
            methods.get('post', {}).get('tags', []) or
            methods.get('put', {}).get('tags', []) or
            methods.get('delete', {}).get('tags', [])
        )
        
        if tags and tenant in [tag.lower() for tag in tags]:
            filtered_paths[path] = methods

    openapi_schema['paths'] = filtered_paths

    return JSONResponse(openapi_schema)

@correcto.get('/api')
@if_tenant_exists
def api_page(request: Request) -> Response:
    tenant = request.state.tenant

    return get_swagger_ui_html(
        openapi_url=f'/openapi/{tenant}.json',
        title=TITLE + f': {tenant.capitalize()} tenant',
    )

if __name__ == '__main__':
    run('main:correcto', host='localhost', port=8001, reload=True)