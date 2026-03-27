from serializers import TenantSerializer
from fastapi.responses import JSONResponse, Response
from fastapi import status
from functools import wraps

def if_tenant_exists(func) -> Response:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        request = kwargs.get('request')
        tenant = request.state.tenant if hasattr(request.state, 'tenant') else None
        serializer = TenantSerializer(data={'tenant': tenant})
        if not serializer.if_exist():
            return JSONResponse(
                content={'err_description': 'Tenant didn\'t find'},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return func(*args, **kwargs)
    
    return wrapper