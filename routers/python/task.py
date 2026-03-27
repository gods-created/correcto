from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from serializers import TaskSerializer
from pydantic import BaseModel
from typing import List, Any, Optional
from json import loads
from services import get_db_url_service
from decorators import if_tenant_exists

router = APIRouter(
    prefix='/tasks',
    tags=['PYTHON', 'PYTHON-TASK'],
    default_response_class=JSONResponse,
)

class TaskSchema(BaseModel):
    task_description: Optional[str] = None
    tags: Optional[List[str]] = None
    return_values: Optional[List[Any]] = None


@router.get(path='', response_class=JSONResponse)
@if_tenant_exists
def get_tasks(request: Request) -> JSONResponse:
    content = {'tasks': []}
    query_params = request.query_params

    serializer = TaskSerializer(
        data={'id': query_params.get('id')},
        db_url=get_db_url_service('python')
    )

    content['tasks'] = serializer.get()

    return JSONResponse(
        content=content,
        status_code=status.HTTP_200_OK
    )

@router.post(path='', response_class=JSONResponse)
@if_tenant_exists
def create_task(request: Request, task: TaskSchema) -> JSONResponse:
    response = {}
    serializer = TaskSerializer(
        data=loads(task.model_dump_json(indent=2)),
        db_url=get_db_url_service('python')
    )

    response = serializer.create()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_201_CREATED if not 'err_description' in response else status.HTTP_400_BAD_REQUEST
    )

@router.put(path='/{id}', response_class=JSONResponse)
@if_tenant_exists
def update_task(
    request: Request,
    id: str, 
    task: TaskSchema
) -> JSONResponse:
    response = {}
    serializer = TaskSerializer(
        data={
            'id': id, 
            **loads(task.model_dump_json(indent=2))
        },
        db_url=get_db_url_service('python')
    )

    response = serializer.update()

    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK if not 'err_description' in response else status.HTTP_400_BAD_REQUEST
    )

@router.delete(path='/{id}', response_class=JSONResponse)
@if_tenant_exists
def delete_task(id: str, request: Request) -> JSONResponse:
    serializer = TaskSerializer(
        data={'id': id},
        db_url=get_db_url_service('python')
    )

    serializer.delete()

    return JSONResponse(
        content={},
        status_code=status.HTTP_200_OK
    )