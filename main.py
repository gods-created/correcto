from fastapi import FastAPI, Request, status
from fastapi.responses import Response, JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException 
from middlewares import InterceptIPMiddleware, TenantMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from uvicorn import run
from dotenv import load_dotenv
from serializers import TenantSerializer
from configs import TENANTS
from loguru import logger

load_dotenv()

correcto = FastAPI(
    title='Correcto',
    description='Correcto API general requests',
    version='0.0.1',
    docs_url=None,
    redoc=None,
)

correcto.add_middleware(InterceptIPMiddleware)
correcto.add_middleware(TenantMiddleware)

@correcto.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc) -> Response:
    return JSONResponse(
        content={'err_description': str(exc.detail)},
        status_code=exc.status_code
    )

@correcto.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f'Validation Error Object: \'{exc.errors()[0]}\'')

    error = exc.errors()[0].get('msg')

    if ',' in error:
        error = error.split(', ')[1]

    return JSONResponse(
        content={'err_description': error},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

tenant = None

@correcto.get('/api', name='api', include_in_schema=False, response_class=HTMLResponse)
async def api_page(request: Request):
    global tenant 

    tenant_error_response = HTMLResponse(
        content=open('./templates/tenantError.html', mode='r').read(),
        status_code=302
    )

    tenant = request.state.tenant if hasattr(request.state, 'tenant') else None
    if not tenant or not tenant in TENANTS:
        return tenant_error_response
    
    serializer = TenantSerializer(data={'tenant': tenant})
    
    if not serializer.if_exist():
        return tenant_error_response
    
    routers = TENANTS[tenant]['routers']
    for router in routers:
        correcto.include_router(router)
    
    return get_swagger_ui_html(
        openapi_url=correcto.openapi_url or '',
        title=correcto.title,
    )

if __name__ == '__main__':
    run('main:correcto', host='localhost', port=8001, reload=True)