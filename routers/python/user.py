from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from serializers import UserSerializer
from pydantic import BaseModel, EmailStr, field_validator
from json import loads
from services import get_db_url_service
from typing import Optional

router = APIRouter(
    prefix='/users',
    tags=['PYTHON', 'USER'],
    default_response_class=JSONResponse
)
     
class UserSchema(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, fullname: str) -> str:
        if fullname and len(fullname) > 150:
            raise ValueError('Fullname mustn\'t have more than 150 characters')
        
        return fullname

@router.get('', response_class=JSONResponse)
def get_users(request: Request) -> JSONResponse:
    user_id = request.query_params.get('id')
    serializer = UserSerializer(
        data={'id': user_id},
        db_url=get_db_url_service('python')

    )
    users = serializer.get()

    return JSONResponse(
        content={'users': users},
        status_code=status.HTTP_200_OK
    )

@router.post('', response_class=JSONResponse)
def create_user(user: UserSchema) -> JSONResponse:
    response = {}
    serializer = UserSerializer(
        data=loads(user.model_dump_json(indent=2)),
        db_url=get_db_url_service('python')

    )

    response = serializer.create()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_201_CREATED if 'user' in response else status.HTTP_400_BAD_REQUEST
    )

@router.put(path='/{id}', response_class=JSONResponse)
def update_user(
    id: str, 
    user: UserSchema
) -> JSONResponse:
    response = {}
    serializer = UserSerializer(
        data={
            'id': id, 
            **loads(user.model_dump_json(indent=2))
        },
        db_url=get_db_url_service('python')
    )

    response = serializer.update()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK if not 'err_description' in response else status.HTTP_400_BAD_REQUEST
    )

@router.delete('/{id}', response_class=JSONResponse)
def delete_user(id: str, request: Request) -> JSONResponse:
    serializer = UserSerializer(
        data={'id': id},
        db_url=get_db_url_service('python')

    )

    serializer.delete()

    return JSONResponse(
        content={},
        status_code=status.HTTP_200_OK
    )