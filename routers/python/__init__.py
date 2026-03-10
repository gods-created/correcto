from .task import router as task_router
from .user import router as user_router
from .solution import router as solution_router

routers = [task_router, user_router, solution_router, ]