from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from serializers import AdminSerializer
from pydantic import BaseModel, field_validator
from json import loads
from services import get_db_url_service
from typing import Optional
from decorators import if_tenant_exists
from validators import email as email_validator

router = APIRouter(
    prefix='/admins',
    tags=['PYTHON', 'PYTHON-ADMIN'],
    default_response_class=JSONResponse
)
     
class AdminSchema(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, email: str) -> str:
        if not email_validator(email):
            raise ValueError('Invalid email address')

        if email and len(email) > 150:
            raise ValueError('Email mustn\'t have more than 150 characters')
        
        return email
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not password:
            raise ValueError('Password can\'t to be empty')

        if password and len(password) > 150 or len(password) < 8:
            raise ValueError('Password length have to be between 8 and 150 characters')
        
        return password

@router.post('/sign_in', response_class=JSONResponse)
@if_tenant_exists
def sign_in(admin: AdminSchema, request: Request) -> JSONResponse:
    serializer = AdminSerializer(
        data=loads(admin.model_dump_json(indent=2)),
        db_url=get_db_url_service('python')

    )
    
    response = serializer.sign_in()
    return JSONResponse(
        content=response,
        status_code=status.HTTP_400_BAD_REQUEST if 'err_description' in response else status.HTTP_200_OK
    )

@router.post('/sign_up', response_class=JSONResponse)
@if_tenant_exists
def sign_up(admin: AdminSchema, request: Request) -> JSONResponse:
    serializer = AdminSerializer(
        data=loads(admin.model_dump_json(indent=2)),
        db_url=get_db_url_service('python')

    )

    response = serializer.sign_up()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_400_BAD_REQUEST if 'err_description' in response else status.HTTP_201_CREATED
    )

@router.delete('/delete/{email}', response_class=JSONResponse)
@if_tenant_exists
def delete_admin(email: str, request: Request) -> JSONResponse:
    serializer = AdminSerializer(
        data={'email': email},
        db_url=get_db_url_service('python')
    )

    serializer.delete()

    return JSONResponse(
        content={},
        status_code=status.HTTP_200_OK
    )

@router.get('/check_token/{token}', response_class=JSONResponse)
@if_tenant_exists
def check_token(token: str, request: Request) -> JSONResponse:
    serializer = AdminSerializer(
        data={'token': token},
        db_url=get_db_url_service('python')
    )

    response = serializer.check_token()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_400_BAD_REQUEST if response.get('err_description') else status.HTTP_200_OK
    )