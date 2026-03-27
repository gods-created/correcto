from abc import ABC
from sqlalchemy import select, delete, update
from sqlalchemy.exc import (
    SQLAlchemyError, 
    OperationalError, 
    InterfaceError, 
    IntegrityError,
    NoResultFound
)
from models import (
    Tenant as TenantModel,
    Task as TaskModel,
    User as UserModel,
    Solution as SolutionModel,
    Admin as AdminModel
)
from loguru import logger
from typing import Optional, List
from json import dumps
from starlette.datastructures import UploadFile as StarletteUploadFile
from os.path import join, exists
from os import getenv, remove
from string import ascii_letters, digits
from random import choice
from services import CheckerService
from cryptography.fernet import Fernet
from jwt import encode, decode
from configs import TENANTS

class BaseSerializer(ABC):
    db_session = None

    def __init__(self, data: dict, db_url: Optional[str] = None):
        self.data = data
        self._db_url = db_url

    def db_connect(self):
        from os import getenv
        from sqlalchemy.orm import Session
        from sqlalchemy import create_engine

        DB_URL = self._db_url or getenv('BASE_DB_URL')

        try:
            self.db_session = Session(
                bind=create_engine(
                    url=DB_URL or '',
                    echo=False
                )
            )

        except OperationalError as e:
            logger.error(f'Operational error: {e}')

        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')

    def db_disconnect(self):
        if self.db_session:
            self.db_session.close()

class TenantSerializer(BaseSerializer):
    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
    
    def if_exist(self) -> bool:
        response = False 

        self.db_connect()
        if not self.db_session:
            return response 

        try:
            data = self.data
            tenant = data.get('tenant')
            
            if not tenant or not tenant in TENANTS:
                return False
            
            stmt = select(TenantModel).where(TenantModel.domain == tenant)
            for item in self.db_session.scalars(stmt):
                if item is not None:
                    response = not response
                    break
                continue
        
        except SQLAlchemyError as e:
            logger.error(f'An SQLAlchemy error occurred: {e}')

        self.db_disconnect()
        return response

class TaskSerializer(BaseSerializer):
    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
    
    def get(self) -> List[dict]:
        tasks = []

        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            stmt = select(TaskModel)
            task_id = self.data.get('id')
            if task_id is not None and task_id.isdigit():
                stmt = stmt.where(TaskModel.id == int(task_id))

            for task in self.db_session.scalars(stmt):
                tasks.append(task.to_json())

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return tasks
    
    def create(self) -> dict:
        response = {}
        
        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            task_description, tags, return_values, = (
                self.data.get('task_description'),
                self.data.get('tags', []),
                self.data.get('return_values', []),
            )

            if not task_description:
                raise ValueError('Task description can\'t to be empty')

            if  len(task_description) > 256:
                raise ValueError('Task description mustn\'t have more than 256 characters')

            if len(return_values) == 0:
                raise ValueError('Return values mustn\'t have less than 1 value')

            task = TaskModel(
                task_description=task_description, 
                tags=dumps(tags),
                return_values=dumps(return_values)
            )
            self.db_session.add(task)
            self.db_session.commit()
            response['task'] = task.to_json()

        except ValueError as e:
            response['err_description'] = str(e)

        except IntegrityError as e:
            e = str(e)
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar row is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        return response
    
    def update(self):
        response = {}

        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            task_id = self.data.get('id')

            stmt = select(TaskModel).filter_by(id=task_id)
            task = self.db_session.scalars(stmt).one()
            for key, value in self.data.items():
                if not hasattr(task, key) or not value:
                    continue

                if key == 'task_description':
                    task.task_description = value

                if key == 'tags':
                    task.tags = dumps(value)
                
                if key == 'return_values' and len(value) > 0:
                    task.return_values = dumps(value)

            self.db_session.commit()
            response['task'] = task.to_json()

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        except IntegrityError as e:
            e = str(e)
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar row is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except NoResultFound as e:
            response['err_description'] = 'No row was found when one was required'

        return response

    def delete(self) -> None:
        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            stmt = delete(TaskModel)
            task_id = self.data.get('id')
            if task_id is not None and task_id.isdigit():
                stmt = stmt.where(TaskModel.id == int(task_id))

            self.db_session.execute(stmt)
            self.db_session.commit()

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

class UserSerializer(BaseSerializer):
    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

    def get(self) -> List[dict]:
        users = []

        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            stmt = select(UserModel)
            user_id = self.data.get('id')
            if user_id is not None and user_id.isdigit():
                stmt = stmt.where(UserModel.id == int(user_id))

            for user in self.db_session.scalars(stmt):
                users.append(user.to_json())

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return users
        
    def create(self) -> dict:
        response = {}

        try:
            self.db_connect()

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            fullname, email, = (
                self.data.get('fullname'),
                self.data.get('email'),
            )

            if not fullname or not email:
                raise ValueError('Fullname and email are required fields')

            user = UserModel(**self.data)
            self.db_session.add(user)
            self.db_session.commit()
            response['user'] = user.to_json()

        except ValueError as e:
            response['err_description'] = str(e)

        except IntegrityError as e:
            e = str(e)
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar user is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        except Exception as e:
            response['err_description'] = str(e)

        return response
    
    def update(self) -> dict:
        response = {}

        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            user_id = self.data.get('id')

            stmt = select(UserModel).filter_by(id=user_id)
            user = self.db_session.scalars(stmt).one()
            for key, value in self.data.items():
                if not hasattr(user, key) or not value:
                    continue

                if key == 'fullname':
                    user.fullname = value

                if key == 'email':
                    user.email = value
                
            self.db_session.commit()
            response['user'] = user.to_json()

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        except IntegrityError as e:
            e = str(e)
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar user is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except NoResultFound as e:
            response['err_description'] = 'No row was found when one was required'

        return response
    
    def delete(self) -> None:
        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            stmt = delete(UserModel)
            user_id = self.data.get('id')
            if user_id is not None and user_id.isdigit():
                stmt = stmt.where(UserModel.id == int(user_id))

            self.db_session.execute(stmt)
            self.db_session.commit()

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

class SolutionSerializer(BaseSerializer):
    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self._solution_store = './assets/solutions'

    def _rename_filename(self, filename: str) -> str:
        prefix = ''.join(choice(ascii_letters + digits) for _ in range(4))
        return f'{prefix}_{filename}'

    def _create_file(self, file: StarletteUploadFile) -> str:
        filename = str(file.filename)

        if not filename.endswith('.py'):
            raise ValueError('Incorrect file extension. Accepting only PY files')

        while True:
            full_path = join(self._solution_store, filename)

            if not exists(full_path):
                break

            filename = self._rename_filename(filename)

        file.file.seek(0)
        content = file.file.read()
        with open(full_path, mode='wb') as f:
            f.write(content)

        return full_path
    
    def _update_mark(self, mark: float) -> Optional[str]:
        error = None 

        try:
            stmt = update(SolutionModel) \
                .where(SolutionModel.id == int(self.data.get('id'))) \
                .values(mark=mark, checked=True)
            
            self.db_session.execute(stmt)
            self.db_session.commit()

        except InterfaceError as e:
            error = 'Unsupported type one of the fields'

        except IntegrityError as e:
            e = str(e)

            if 'NOT NULL constraint failed' in e:
                error = 'Constraint for operation due to invalid field'

        except NoResultFound as e:
            error = 'No row was found when one was required'

        except Exception as e:
            error = f'{e.__class__.__name__}: {str(e)}'

        return error or None

    def get(self) -> List[dict]:
        solutions = []

        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            stmt = select(SolutionModel)

            solution_id, user_id, task_id = (
                self.data.get('id'), 
                self.data.get('user_id'),
                self.data.get('task_id'),
            )

            if solution_id is not None and solution_id.isdigit():
                stmt = stmt.where(SolutionModel.id == int(solution_id))
            
            if user_id is not None and user_id.isdigit():
                stmt = stmt.where(SolutionModel.user_id == int(user_id))
            
            if task_id is not None and task_id.isdigit():
                stmt = stmt.where(SolutionModel.task_id == int(task_id))

            for user in self.db_session.scalars(stmt):
                solutions.append(user.to_json())

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return solutions
    
    def create(self) -> dict:
        response = {}

        try:
            self.db_connect()

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            file, user_id, task_id = (
                self.data.get('file'),
                self.data.get('user_id'),
                self.data.get('task_id'),
            )

            try:
                filename = self._create_file(file)

            except ValueError as e:
                raise Exception(str(e))

            solution = SolutionModel(
                filename=filename,
                user_id=int(user_id),
                task_id=int(task_id)
            )

            self.db_session.add(solution)
            self.db_session.commit()
            response['solution'] = solution.to_json()

        except ValueError as e:
            response['err_description'] = str(e)

        except IntegrityError as e:
            e = str(e)
            
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar solution filename is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        except Exception as e:
            response['err_description'] = str(e)

        return response
    
    def delete(self) -> None:
        try:
            solutions = self.get()
            if not solutions:
                raise Exception('Solution didn\'t find')
            
            solution = solutions[0]
            filename = solution.get('filename')
            if filename and exists(filename):
                remove(filename)

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            stmt = delete(SolutionModel)
            stmt = stmt.where(SolutionModel.id == int(self.data.get('id')))
            self.db_session.execute(stmt)
            self.db_session.commit()

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

    def check(self, checker: CheckerService) -> dict:
        response = {}

        try:
            solutions = self.get()
            if not solutions:
                raise Exception('Solution didn\'t find')
            
            solution = solutions[0]

            filename = solution.get('filename')
            if not filename or not exists(filename):
                raise Exception('File with solution didn\'t find')
            
            task = solution.get('task', {})

            task_description, tags, return_values = (
                task.get('task_description'),
                task.get('tags'),
                task.get('return_values')
            )

            mark = 1
            node = checker.create_node(filename)

            if (visiter := checker.visiter(node, tags)) is not None and visiter == False:
                    mark -= 0.5

            checker_args = filename, return_values,
            if (result := checker.run_process(*checker_args)) is None:
                result = checker.as_import(*checker_args)

            if result is None:
                result = checker.send_to_helper(*checker_args, task_description)

            if isinstance(result, bool) and result == False:
                mark -= 0.5

            self._update_mark(mark)
            solution['mark'] = mark
            response['solution'] = solution
            
        except Exception as e:
            response['err_description'] = str(e)

        return response

class AdminSerializer(BaseSerializer):
    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.secret_key = getenv('APP_SECRET_KEY')
        self.cipher_suite = Fernet(self.secret_key)

    def sign_in(self) -> dict:
        response = {}
        try:
            self.db_connect()
            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            email, password = (
                self.data.get('email'),
                self.data.get('password'),
            )
            
            stmt = select(AdminModel).filter_by(email=email)
            rows = self.db_session.execute(stmt).one_or_none()
            if not rows:
                raise Exception('Admin doesn\'t exist')
            
            admin, *_ = rows
            plain_password = self.cipher_suite.decrypt(admin.password).decode('utf-8')
            if not password == plain_password:
                raise Exception('Incorrect password')
            
            payload = admin.to_json()
            payload.update({'password': password})
            token = encode(payload, self.secret_key, algorithm='HS256')
            response['token'] = token

        except Exception as e:
            response['err_description'] = str(e)

        return response
        
    def sign_up(self) -> dict:
        response = {}

        try:
            self.db_connect()

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            email, password = (
                self.data.get('email'),
                self.data.get('password'),
            )
            encoded_password = self.cipher_suite \
                .encrypt(
                    password.encode('utf-8')
                )
            admin = AdminModel(email=email, password=encoded_password.decode('utf-8'))
            self.db_session.add(admin)
            self.db_session.commit()
            response['admin'] = admin.to_json()

        except ValueError as e:
            response['err_description'] = str(e)

        except IntegrityError as e:
            e = str(e)
            if 'UNIQUE constraint failed' in e:
                response['err_description'] = 'The similar admin is already existing'

            if 'NOT NULL constraint failed' in e:
                response['err_description'] = 'Constraint for operation due to invalid field'

        except InterfaceError as e:
            response['err_description'] = 'Unsupported type one of the fields'

        except Exception as e:
            response['err_description'] = str(e)

        return response
    
    def delete(self) -> dict:
        try:
            self.db_connect()

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            admin = delete(AdminModel).where(AdminModel.email == self.data['email'])
            self.db_session.execute(admin)
            self.db_session.commit()

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return {}
    
    def check_token(self) -> dict:
        response = {'err_description': '', 'access': False}

        try:
            self.db_connect()

            if not self.db_session:
                raise Exception('Connection with DB is refused')
            
            token = self.data.get('token')
            if not token:
                raise Exception('Invalid token')
            
            payload = decode(token, self.secret_key, algorithms=['HS256'])
            email, password = (
                payload.get('email'),
                payload.get('password')
            )

            if not all((email, password)):
                raise Exception('Invalid parameters encoded in the token')
            
            self.data['email'], self.data['password'] = email, password
            auth_response = self.sign_in()
            if 'err_description' in auth_response:
                raise Exception(auth_response['err_description'])
            
            response['access'] = True

        except Exception as e:
            response['err_description'] = str(e)
        
        return response