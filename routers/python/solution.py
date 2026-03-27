from fastapi import APIRouter, Request, status, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from serializers import SolutionSerializer, TaskSerializer, UserSerializer
from services import get_db_url_service
from decorators import if_tenant_exists
from tasks import check_solution_task
from json import dumps
from consumers import SolutionConsumer


consumer = SolutionConsumer()
router = APIRouter(
    prefix='/solutions',
    tags=['PYTHON', 'PYTHON-SOLUTION'],
    default_response_class=JSONResponse
)

@router.get('', response_class=JSONResponse)
@if_tenant_exists
def get_solutions(request: Request):
    query_params = request.query_params

    solution_id = query_params.get('id')
    user_id = query_params.get('user_id')
    task_id =  query_params.get('task_id')

    serializer = SolutionSerializer(
        data={
            'id': solution_id,
            'user_id': user_id,
            'task_id': task_id
        },
        db_url=get_db_url_service('python')
    )

    return JSONResponse(
        content={'solutions': serializer.get()},
        status_code=status.HTTP_200_OK
    )

@router.post(path='', response_class=JSONResponse)
@if_tenant_exists
def create_solution(
    request: Request,
    user_id: str = Form(...),
    task_id: str = Form(...), 
    file:  UploadFile = File(...)
) -> JSONResponse:
    data = {
        'user_id': user_id,
        'task_id': task_id,
        'file': file
    }
    db_url = get_db_url_service('python')

    attrs = {
        'data': data,
        'db_url': db_url
    }

    task_serializer = TaskSerializer(data={'id': task_id}, db_url=db_url)
    user_serializer = UserSerializer(data={'id': user_id}, db_url=db_url)
    solution_serializer = SolutionSerializer(**attrs)
    
    task = task_serializer.get()
    user = user_serializer.get()

    if not task or not user:
        raise RequestValidationError([
            {
                'loc': ['id'],
                'msg': 'Task or user doesn\'t exist',
                'type': 'value_error'
            }
        ])

    response = solution_serializer.create()

    status_code = (
        status.HTTP_201_CREATED
        if 'err_description' not in response
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )

    return JSONResponse(
        content=response,
        status_code=status_code
    )

@router.delete(path='/{id}', response_class=JSONResponse)
@if_tenant_exists
def delete_solution(request: Request, id: str) -> JSONResponse:
    serializer = SolutionSerializer(
        data={'id': id},
        db_url=get_db_url_service('python')
    )

    serializer.delete()

    return JSONResponse(
        content={},
        status_code=status.HTTP_200_OK
    )

@router.get(path='/check/{id}', response_class=JSONResponse)
@if_tenant_exists
async def check_solution(id: str, request: Request, background_tasks: BackgroundTasks):
    background_task = BackgroundTasks()
    background_task.add_task(
        check_solution_task,
        id,
    )

    return JSONResponse(
        content={},
        status_code=status.HTTP_200_OK
    )

@router.websocket(path='/ws')
async def ws_check_solution(websocket: WebSocket):
    await consumer.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await consumer.send_personal_message(dumps(data), websocket)

    except WebSocketDisconnect:
        consumer.disconnect(websocket)