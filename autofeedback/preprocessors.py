from nbgrader import utils
from nbgrader.preprocessors import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Tuple
from base64 import b64decode, b64encode
from traitlets import Unicode, Bool
from textwrap import dedent

hidden_test_tag = "autofeedback"
plot_tag = "plot_task"
test_code_tag = "test_code"


class TagPlotCells(NbGraderPreprocessor):
    """A preprocessor for identifying solution cells with plot outputs and tagging them"""

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        if utils.is_solution(cell):
            for output in cell['outputs']:
                if output['output_type'] == 'display_data' and hasattr(output['data'], 'image/png'):
                    if hidden_test_tag in cell['metadata'].keys():
                        cell['metadata'][hidden_test_tag][plot_tag] = True
                    else:
                        cell['metadata'][hidden_test_tag] = {plot_tag: True}
        return cell, resources

class PreservePlots(NbGraderPreprocessor):
    """A preprocessor for making sure a plot object created by a plotting task is available in variable 'fig'."""
    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        if utils.is_solution(cell):
            if cell['metadata'].get(hidden_test_tag, False) and cell['metadata'][hidden_test_tag].get(plot_tag, False):
                lines = cell.source.split("\n")
                new_lines = []

                # Remove any calls to plt.show()
                for line in lines:
                    if ".show(" not in line:
                        new_lines.append(line)

                # Make sure gcf() is available
                new_lines.insert(0, "from matplotlib.pyplot import gcf")

                # Add active figure to variable "fig"
                new_lines.append("fig = gcf()")

                cell.source = "\n".join(new_lines)

        return cell, resources

class RemoveGCF(NBGraderPreprocessor):
    """A preprocessor for making sure a plot object created by a plotting task is available in variable 'fig'."""
    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        if utils.is_solution(cell):
            if cell['metadata'].get(hidden_test_tag, False) and cell['metadata'][hidden_test_tag].get(plot_tag, False):
                lines = cell.source.split("\n")
                if "from matplotlib.pyplot import gcf" in lines[0] and "fig = gcf()" in lines[-1]:
                    cell.source = "\n".join(lines[1:-1])

        return cell, resources

class NoCellsDeletable(NbGraderPreprocessor):
    """A preprocessor to tag every cell in the assignment as "deletable": false"""
    
    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        
        cell['metadata']['deletable'] = False
            
        return cell, resources

class LockMarkdownCells(NbGraderPreprocessor):
    """A preprocessor to make every mardkown cell read-only"""
    def preprocess_cell(self, 
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        
        if cell.cell_type == 'markdown':
            cell['metadata']['editable'] = False
            
        return cell, resources


class InsertHiddenTests(NbGraderPreprocessor):
    """A preprocessor for making sure a plot object created by a plotting task is available in variable 'fig'."""
    
    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        if cell.cell_type == 'code' and utils.is_grade(cell):
            if cell['metadata'].get(hidden_test_tag, False) and cell['metadata'][hidden_test_tag].get(test_code_tag, False):
                test_string = b64decode(cell['metadata'][hidden_test_tag][test_code_tag]).decode('utf-8')
                cell['source'] += "\n### BEGIN HIDDEN TESTS\n"+test_string+"\n### END HIDDEN TESTS"

        return cell, resources


class ObfuscateHiddenTests(NbGraderPreprocessor):

    begin_test_delimeter = Unicode(
        "BEGIN HIDDEN TESTS",
        help="The delimiter marking the beginning of hidden tests cases"
    ).tag(config=True)

    end_test_delimeter = Unicode(
        "END HIDDEN TESTS",
        help="The delimiter marking the end of hidden tests cases"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing hidden test regions
            are not marked as grade cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    def _remove_hidden_test_region(self, cell: NotebookNode) -> bool:
        """Find a region in the cell that is delimeted by
        `self.begin_test_delimeter` and `self.end_test_delimeter` (e.g.  ###
        BEGIN HIDDEN TESTS and ### END HIDDEN TESTS). Remove that region
        depending the cell type.

        This modifies the cell in place, and then returns True if a
        hidden test region was removed, and False otherwise.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        test_lines = []
        in_test = False
        removed_test = False

        for line in lines:
            # begin the test area
            if self.begin_test_delimeter in line:

                # check to make sure this isn't a nested BEGIN HIDDEN TESTS
                # region
                if in_test:
                    raise RuntimeError(
                        "Encountered nested begin hidden tests statements")
                in_test = True
                removed_test = True

            # end the solution area
            elif self.end_test_delimeter in line:
                in_test = False

            # add lines as long as it's not in the hidden tests region
            elif in_test:
                test_lines.append(line)
            elif not in_test:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END HIDDEN TESTS statment
        if in_test:
            raise RuntimeError("No end hidden tests statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        if removed_test:
            test_string = "\n".join(test_lines)
            test_string_encoded = b64encode(bytes(test_string, 'utf8')).decode('utf-8')
            cell.metadata[hidden_test_tag] = {'test_code': test_string_encoded}

        return removed_test

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        nb, resources = super(ObfuscateHiddenTests, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        # remove hidden test regions
        removed_test = self._remove_hidden_test_region(cell)

        # determine whether the cell is a grade cell
        is_grade = utils.is_grade(cell)

        # check that it is marked as a grade cell if we remove a test
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_grade and removed_test:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Hidden test region detected in a non-grade cell; "
                    "please make sure all solution regions are within "
                    "'Autograder tests' cells."
                )

        return cell, resources
