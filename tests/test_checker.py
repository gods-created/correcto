from unittest import TestCase
from unittest.mock import patch
from os import getcwd, remove
from os.path import join
from textwrap import dedent
from dotenv import load_dotenv
import services

class TestChecket(TestCase):
    def setUp(self) -> None:
        self.code = dedent('''
            def func() -> int:
                response = 0
                i = 3
                while i > 0:
                    response += i
                    i -= 1
                return response
        ''')

        self.path_to_file = join(getcwd(), 'testcode.py')
        with open(self.path_to_file, mode='w') as file:
            file.write(self.code)

        self.task_description = 'Write down a function, which returns sum numbers from 3 to 0 usign while condition'
        self.return_values = [6]
        self.checker = services.CheckerService()

    @patch('services.CheckerService.create_node')
    def test_create_node_method_with_mock(self, mock_object):
        mock_object.return_value = self.code
        response = mock_object(self.path_to_file)
        mock_object.assert_called_once_with(self.path_to_file)
        assert response == self.code

    def test_create_node_method(self):
        node = self.checker.create_node(self.path_to_file)
        self.checker.visit_While(node)
        assert self.checker.while_ == True

    def test_run_process_method(self):
        response = self.checker.run_process(self.path_to_file, self.return_values)
        assert response is None 

    def test_send_to_helper_method(self):
        load_dotenv()
        response = self.checker.send_to_helper(self.path_to_file, self.return_values, self.task_description)
        assert response is not None
        assert response == True

    def tearDown(self) -> None:
        remove(self.path_to_file)