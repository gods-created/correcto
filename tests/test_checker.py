from unittest import TestCase
from os import getcwd, remove
from os.path import join
from textwrap import dedent
from dotenv import load_dotenv
import services

class TestChecket(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.node = None

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
        self.return_values = [6, True]
        self.tags = ['while']
        self.checker = services.CheckerService()

    def test_1_create_node_method(self):
        node = self.checker.create_node(self.path_to_file)
        self.checker.visit_While(node)
        assert self.checker.while_ == True

        type(self).node = node 

    def test_2_visitor_method(self):
        response = self.checker.visiter(type(self).node, self.tags)
        assert response == True

    def test_3_run_process_method(self):
        response = self.checker.run_process(self.path_to_file, self.return_values)
        assert response is None 

    def test_4_as_import_method(self):
        response = self.checker.as_import(self.path_to_file, self.return_values)
        assert response == True

    # def test_5_send_to_helper_method(self):
    #     load_dotenv()
    #     response = self.checker.send_to_helper(self.path_to_file, self.return_values, self.task_description)
    #     assert response is not None
    #     assert response == True

    def tearDown(self) -> None:
        remove(self.path_to_file)