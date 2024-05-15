from . import TestClass, compare_type, compare_values


class VariableTests(TestClass):
    """
    Example usage:
    ----------------------------------
    test_obj = VariableTests()
    test_obj.compare(x1, y1, rtol=?, atol=?)
    test_obj.compare(x2, y2, rtol=?, atol=?)
    erc...
    test_obj.get_summary()*cell_points
    """

    def __init__(self):
        super().__init__()
        self.type_tests = []
        self.type_wgt = 0.2 # Configurable?

    def compare(self, x, y, name: str = None, rtol=1e-2, atol=1e-8):
        same_type = compare_type(x, y)
        if not same_type:
            msg = "variable '%s' is type %s and not %s."%(name, type(x).__name__, type(y).__name__)
            self.add_result(False, msg)
            self.type_tests.append(True)
        else:
            msg = "variable '%s' is the correct type (%s)."%(name, type(x).__name__)
            self.add_result(True, msg)
            self.type_tests.append(True)

            same_value, compare_msg = compare_values(x, y, rtol=rtol, atol=atol)
            msg = f"variable '{name}' is a "+compare_msg
            self.add_result(same_value, msg)
            self.type_tests.append(False)

    def get_results(self):
        single_type_wgt = self.type_wgt/sum(self.type_tests)
        for i in range(len(self.type_tests)):
            if self.type_tests[i]:
                self.score.weights[i] = single_type_wgt
        score = super().get_results()
        return score