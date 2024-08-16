from . import TestClass, compare_type, compare_values


class PlotChecker(TestClass):
    def __init__(self, fig):
        self.fig = fig
        self.ca = self.fig.axes[-1]
        super().__init__()

    def test_function(self, func: callable, line_index=-1):

        line = self.ca.lines[line_index]
        result, msg = compare_values(line.get_ydata(), func(line.get_xdata()))
        self.add_result(result, msg)
        
    def test_x(self, x_vals):
        pass
        
    def test_y(self, y_vals):
        pass