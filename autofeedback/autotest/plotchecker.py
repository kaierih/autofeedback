from . import TestClass, compare_type, compare_values, get_deviation
import numpy as np
import matplotlib.pyplot as plt

def check_plot_curve(line, func, atol=1e-6, rtol=1e-3):
    x_data = line.get_xdata()
    y_data = line.get_ydata()

    ref_ydata = func(x_data)

    deviation = 0.0
    if np.allclose(y_data, ref_ydata, rtol=rtol, atol=atol, equal_nan=True):
        result = True
    else:
        result = False
        deviation, _ = get_deviation(y_data, ref_ydata, rtol=rtol, atol=atol)
    return result, deviation

class PlotChecker(TestClass):
    def __init__(self, fig):
        self.fig = fig
        if len(self.fig.axes) < 1:
            self.add_result(False, "No plot detected.", wgt=1.0)
            self.ca = None
        else:
            self.ca = self.fig.axes[-1]
        self.ca = self.fig.axes[-1]
        super().__init__()


    def check_num_lines(self, expected_num_lines: int, wgt=1.0):
        """
        Check if the number of lines in the plot matches the expected number.
        
        Parameters:
        - expected_num_lines: Expected number of lines in the plot.
        - wgt: Weight for the result (default is 1.0).
        """
        if self.ca is None:
            return False

        actual_num_lines = len(self.ca.lines)
        if actual_num_lines == 0:
            self.add_result(False, "No lines found in the plot.", wgt=wgt)
            return False
        elif actual_num_lines == expected_num_lines:
            self.add_result(True, f"Number of lines matches: {actual_num_lines}.", wgt=wgt)
            return True
        else:
            self.add_result(False, f"Expected {expected_num_lines} lines, but found {actual_num_lines}.", wgt=wgt)
            return True


    def test_function(self, func: callable, line_index=-1, atol=1e-6, rtol=1e-3, wgt=1.0):
        """
        Test if the y-data of the specified line matches the function values.
        
        Parameters:
        - func: A callable function that takes x-data and returns y-data.
        - line_index: Index of the line to test (default is the last line).
        - atol: Absolute tolerance for comparison (default is 1e-6).
        - rtol: Relative tolerance for comparison (default is 1e-3).
        """
        if self.ca is None:
            return

        line = self.ca.lines[line_index]
        result, deviation = check_plot_curve(line, func, atol=atol, rtol=rtol)
        
        if result:
            msg = f"Line {line_index} matches the expected function values."
        else:
            msg = f"Line {line_index} does not match the expected function values. Deviation: {deviation:.3f}"
        
        self.add_result(result, msg, wgt=wgt)

    def test_function_set(self, func_set: list[callable], labels: list[str], atol=1e-6, rtol=1e-3, wgt=1.0):
        """
        Test if the y-data of the specified line matches any function in the function set.
        
        Parameters:
        - func_set: A list of callable functions.
        - line_index: Index of the line to test (default is the last line).
        """
        if self.ca is None:
            return

        line_indices = set(range(len(self.ca.lines)))
        
        for func_idx, func in enumerate(func_set):
            deviation = float('inf')
            match_found = False
            closest_match_index = -1
            # Check if the function is callable
            if not callable(func):
                raise Exception(f"Function {func.__name__} is not callable.")
            

            for line_index in line_indices:
                line = self.ca.lines[line_index]
                
                # Compare the y-data with the function values
                result, err = check_plot_curve(line, func, atol=atol, rtol=rtol)

                if err < deviation:
                    deviation = err
                    closest_match_index = line_index

                
                if result:
                    match_found=True
                    closest_match_index = line_index
                    break
            label = self.ca.lines[closest_match_index].get_label()
            label = label if label[0:5] != "_child" else label.strip("_child")
            if match_found:
                self.add_result(True, f"Curve {label} follows the correct path for {labels[func_idx]}.", wgt=wgt)
            else:
                self.add_result(False, f"No match found for {labels[func_idx]}. Closest match is curve {label} which deviates by up to {deviation:.3f}.", wgt=wgt)
        
