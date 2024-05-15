from . import TestClass, print2str
import re
from unittest.mock import patch


class CodeCellTests(TestClass):
    """
    Test class to check execution and output of code cell.
    """

    def __init__(self, code_cell_contents: str, init_wgt=0.1):
        super().__init__()
        self.source = code_cell_contents
        self.test_exec(wgt=init_wgt)

    def test_exec(self, wgt=None):
        _, N_tests = self.score.get_ratio()
        msg_intro = f"Test {N_tests + 1}"
        self.student_print = ""
        try:
            with patch(f'{__name__}.print') as mock_print:
                exec(self.source)
            for call in mock_print.mock_calls:
                self.student_print += print2str(*call.args, **call.kwargs)
        except Exception as e:
            feedback = "answer cell could not execute: " + e.args[0]
            self.score.process_result(False, wgt)
            self.log.append(msg_intro + " failed: " + feedback)
        else:
            feedback = "answer cell executed without errors"
            self.score.process_result(True, wgt)
            self.log.append(msg_intro + " passed: " + feedback)

    def test_output(self, desired_output: str, sample=None, wgt=None, ignore_code_match=True):
        passed = False
        content_match = re.search(desired_output, self.source)

        if content_match is not None and ignore_code_match == False:
            feedback = "code cell appears to contain solution, indicating output is not the result of calculations using python"
        else:
            output_match = re.search(desired_output, self.student_print)
            if output_match is not None:
                feedback = f"'{output_match.group()}' in printed message matches desired output."
                passed = True
            else:
                feedback = "no match for desired output found in printed message."

        _, N_tests = self.score.get_ratio()
        msg_intro = f"Test {N_tests + 1}"

        self.score.process_result(passed, wgt)
        if passed:
            self.log.append(msg_intro + " passed: " + feedback)
        else:
            self.log.append(msg_intro + " failed: " + feedback)

    def replace(self, pattern: str, replacement: str):
        self.source = re.sub(pattern, replacement, self.source)
        self.test_exec(wgt=0.0)
        self.score.pop(-1)
        self.log.clear(start=-1)
        self.log.append(f"Making adjustment to code: {replacement}")
        # add code to remove logged score/message
        # add check to see if code executed successfully