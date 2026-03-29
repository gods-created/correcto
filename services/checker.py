from ast import NodeVisitor, parse, literal_eval
from typing import Optional, Any, List, Union, Callable
from subprocess import run, CalledProcessError
from os.path import exists
from loguru import logger
from google import genai
from google.genai.errors import ClientError, ServerError
from os import getenv

class BaseDescriptor:
    def __init__(self, field: str):
        self.field = field

    def __get__(self, instance: object, *args, **kwargs) -> Optional[Any]:
        return instance.__dict__.get(self.field)
    
class WhileDescriptor(BaseDescriptor):
    pass

class ForDescriptor(BaseDescriptor):
    pass

class IfDescription(BaseDescriptor):
    pass

class Checker(NodeVisitor):
    while_ = WhileDescriptor('_while')
    for_ = ForDescriptor('_for')
    if_ = IfDescription('_if')

    def __init__(self):
        self._while = False
        self._for = False
        self._if = False

        self._visit_schema = {
            'while': (self.visit_While, '_while'),
            'for': (self.visit_For, self._for),
            'if': (self.visit_If, self._if),
        }

    def _validate_path_to_file(self, path_to_file: str) -> None:
        if not exists(path_to_file):
            raise FileNotFoundError('File didn\'t find')

        if not path_to_file.endswith('.py'):
            raise ValueError('Invalid python file extension')
        
    def _open_file(self, path_to_file: str) -> str:
        with open(path_to_file, mode='r') as file: 
            return file.read()
        
    def _validated_returns(self, return_values: List[Any]) -> List[Any]:
        validated = []
        for value in return_values:
            try:
                validated.append(literal_eval(value))
            except (ValueError, SyntaxError, TypeError):
                if isinstance(value, str): value = value.replace(' ', '')
                validated.append(value)

        return validated

    def create_node(self, path_to_file: str) -> Optional[Any]:
        try:
            self._validate_path_to_file(path_to_file)
            code = self._open_file(path_to_file)
            return parse(code)
        
        except ValueError as e:
            logger.error(f'ValueError: {str(e)}')
        
        except FileNotFoundError as e:
            logger.error(f'FileNotFoundError: {str(e)}')

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return None

    def run_process(self, path_to_file: str, return_values: List[Any]) -> Optional[bool]:
        try:
            self._validate_path_to_file(path_to_file)
            
            try:
                result = run(
                    ['python3.12', path_to_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            except TimeoutError as e:
                Exception(e.strerror)

            output = result.stdout \
                .replace('\n', ',') \
                .replace(' ', '') or None
            
            validated_returns = self._validated_returns(return_values)
            process_response = False

            try:
                output = literal_eval(output) if output is not None else output

            except:
                pass 
            
            if output in validated_returns:
                process_response = True 

            logger.info(f'Solution was running due to subprocess')

            return process_response

        except ValueError as e:
            logger.error(f'ValueError: {str(e)}')

        except FileNotFoundError as e:
            logger.error(f'FileNotFoundError: {str(e)}')

        except CalledProcessError as e:
            logger.error(f'Code failed with exit code {e.returncode}. Error: {e.stderr}')

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return None
    
    def as_import(self, path_to_file: str, return_values: List[Any]) -> Optional[bool]:
        response = False

        try:
            self._validate_path_to_file(path_to_file)
            
            namespace = {}
  
            with open(path_to_file, mode='r') as f:
                exec(f.read(), namespace)

            for obj_name, obj in namespace.items():
                if not callable(obj):
                    continue
                
                logger.debug(f'Callable object name is \'{obj_name}\'')

                try:
                    return_value = obj()
                
                except TimeoutError as e:
                    logger.error(e.strerror)
                    continue
                
                if return_value in self._validated_returns(return_values):
                    response = True 
                    break
            
            namespace.clear()

            logger.info(f'Solution was running through import')
            
            return response
        
        except FileNotFoundError as e:
            logger.error(f'FileNotFoundError: {str(e)}')

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return None
    
    def send_to_helper(self, path_to_file: str, return_values: List[Any], task_description: Optional[str]) -> Optional[Union[Callable, bool]]:
        try:
            self._validate_path_to_file(path_to_file)
            code = self._open_file(path_to_file)
            prompt = '''
                You are a strict Python code validator.

                You will receive:
                1) A task description.
                2) Expected return values (what the function must return).
                3) A Python code solution.

                Your job is to verify whether the provided Python code FULLY and EXACTLY satisfies the task description and returns the required return values.

                Validation rules:
                - The logic must correctly implement the task description.
                - The function must return exactly the required return values.
                - The function signature must match the task requirements (if specified).
                - No missing return statements.
                - No incorrect return types.
                - No extra behavior that contradicts the task.
                - The solution must be valid Python syntax.
                - If the task requires a specific loop, condition, or keyword, it must be present.

                Output rules (STRICT):
                - Return ONLY "1" if the solution is completely correct.
                - Return ONLY "0" if the solution is incorrect in ANY way.
                - Do NOT return explanations.
                - Do NOT return comments.
                - Do NOT return formatting.
                - Do NOT return code blocks.
                - Do NOT return anything except a single character: 1 or 0.

                Now evaluate the following:

                Task Description:
                {0}

                Expected Return Values:
                {1}

                Python Code:
                {2}
            '''.format(
                task_description,
                return_values,
                code
            )
            client = genai.Client(api_key=getenv('GEMINI_API_KEY'))
            response = client.models.generate_content(
                model=getenv('GEMINI_MODEL'),
                contents=prompt,
                config={
                    'temperature': 0,
                }
            )
            output = response.text
            
            if not output or not output.isdigit():
                return self.send_to_helper(path_to_file, return_values, task_description) 
            
            logger.info(f'Solution was checking using Gemini')
            return True if output == '1' else False

        except ValueError as e:
            logger.error(f'ValueError: {str(e)}')

        except FileNotFoundError as e:
            logger.error(f'FileNotFoundError: {str(e)}')

        except ClientError as e:
            logger.error(f'ClientError: {e.message}')

        except ServerError as e:
            logger.error(f'ServerError: {e.message}')

        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {str(e)}')

        return None
    
    def visiter(self, node: Any, tags: Optional[List[str]] = None) -> Optional[bool]:
        response = False 

        if tags is None:
            return None

        for tag in tags:
            tag = tag.lower()
            schema = self._visit_schema.get(tag, [])
            if not schema or len(schema) != 2:
                continue

            visit, condition = schema
            visit(node)
            response = self.__dict__.get(condition, False)

        return response

    def visit_While(self, node: Any) -> None:
        self._while = True
        self.generic_visit(node)

    def visit_For(self, node: Any) -> Any:
        self._for = True 
        self.generic_visit(node)

    def visit_If(self, node: Any):
        self._if = True 
        self.generic_visit(node)
