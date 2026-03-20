from os.path import exists
from loguru import logger
from ast import literal_eval
from json import JSONDecodeError
from models import Task as TaskModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, InterfaceError, DatabaseError
from configs import TENANTS
import pandas as pd

PYTHON_DB_URL = TENANTS.get('python', {}).get('db_url')

def create_tasks(filename: str) -> None:
    try:
        if not exists(filename):
            raise FileNotFoundError('File didn\'t find')
        
        if not filename.endswith('.csv'):
            raise ValueError('Invalid file format')
        
        if PYTHON_DB_URL is None:
            raise ValueError('DB url for connection with DB is absent') 
        
        df = pd.read_csv(filename)
        values = df.iloc[:].astype(str).values.tolist()
        validated_values = [
            value for value in values if len(value) == 3
        ]

        if not validated_values:
            raise ValueError('All rows in CSV table are invalid')

        tasks = []
        for index, value in enumerate(validated_values, 1):
            description, tags, returns = value
            try:
                lst_tags = literal_eval(tags)
                lst_returns = literal_eval(returns)

                if not all((
                    isinstance(lst_tags, list) and len(lst_tags) > 0,
                    isinstance(lst_returns, list) and len(lst_returns) > 0
                )):
                    raise Exception(f'Tags and returns have to be list objects. And you have to specify minim. one value for each other (row #{index})')

            except JSONDecodeError as e:
                logger.error(f'JSON decode error for row #{index}')
                continue

            except SyntaxError as e:
                logger.error(f'Syntax error while decoding for row #{index}')
                continue

            except Exception as e:
                logger.error(str(e))
                continue
            
            task = TaskModel(task_description=description, tags=tags, return_values=returns)
            tasks.append(task)

        if not tasks:
            raise ValueError('All rows in CSV table are invalid')

        try:
            session = Session(
                bind=create_engine(
                    url=PYTHON_DB_URL,
                    echo=False
                )
            )

            session.add_all(tasks)
            session.commit()
            session.close()

            tasks_length = len(tasks)
            info_msg = f'Added {tasks_length} new task'
            logger.info(info_msg + '.' if tasks_length == 1 else info_msg + 's.')

        except (IntegrityError, InterfaceError, DatabaseError, )  as e:
            err_derscription = str(e)
            if 'UNIQUE constraint failed' in err_derscription:
                err_derscription = 'The similar row is already existing.'

            if 'NOT NULL constraint failed' in err_derscription:
                err_derscription = 'Constraint for operation due to invalid field.'
               
            err_derscription += ' No row didn\'t add to table.'
            raise Exception(err_derscription)
                
    except FileNotFoundError as e:
        logger.error(str(e))

    except ValueError as e:
        logger.error(str(e))

    except Exception as e:
        logger.error(str(e))