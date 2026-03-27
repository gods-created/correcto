from serializers import SolutionSerializer
from services import CheckerService, get_db_url_service
from os import getenv
from json import dumps
import websockets

APP_HOST=getenv('APP_HOST', 'localhost')
APP_WS_PORT=getenv('APP_WS_PORT', 8001)

async def check_solution_task(id: str) -> None:
    serializer = SolutionSerializer(
        data={'id': id},
        db_url=get_db_url_service('python')
    )

    checker = CheckerService()
    response = serializer.check(checker=checker)

    uri = f'ws://{APP_HOST}:{APP_WS_PORT}/solutions/ws'
    async with websockets.connect(uri) as websocket:
        await websocket.send(dumps(response))
        await websocket.recv()