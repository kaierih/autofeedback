import nbformat

import os
import nbgrader
from nbgrader.preprocessors import Execute, ClearHiddenTests
from nbgrader.utils import is_grade, determine_grade
from nbconvert import HTMLExporter
from IPython.display import Markdown, display
from .preprocessors import InsertHiddenTests, PreservePlots, RemoveGCF

#from nbconvert.preprocessors import ClearMetadataPreprocessor
# Config Options
output_dir = "test_results"
test_tag = "autofeedback"

# Functions:
# ----------

def run_tests(filename, output_dir="test_results"):
    """ 
    Function to generate student feedback on code answers present
    in the jupyter notebook "filename" based on hidden tests
    created in nbgrader. Detailed results are written to
    '/<output_dir>/<filename>.html', while acheived points and
    max points are returned as (points, max_points).

    A prerequisite is the preprocessor "ObfuscateHiddenTests" having
    been used to generate the student version rather than the standard
    "ClearHiddenTests".
    """
    # 1. Open notebook file and read to dictionary
    with open(filename, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    resources = {'metadata': {'path': './'}}

    # 2. Copy hidden tests from metadata to cell body
    InsertHiddenTests().preprocess(nb, resources)
    # Consider adding a "uniqueness-check" to nbgrader cell id. 
    # Purpose: avoid unwanted behavior when students copy test cells.

    # 3 Preserve Plots
    PreservePlots().preprocess(nb, resources)

    # 4. Execute entire notebook sequentially with hidden tests
    Execute(timeout=30, kernel_name='python3').preprocess(nb, resources)

    # 5. Get student score
    points = 0
    max_points = 0
    for cell in nb.cells:
        if is_grade(cell):
            cell_points, cell_max_points = determine_grade(cell)
            points += 0 if cell_points is None else cell_points
            max_points += cell_max_points
            cell['metadata']['nbgrader']['score'] = cell_points

    resources['nbgrader'] = {'score': points,
                             'max_score': max_points,
                             'late_penalty': 0.0}

    # 6. Remove hidden tests
    ClearHiddenTests().preprocess(nb, resources)

    # Undo Preserve Plots
    RemoveGCF().preprocess(nb, resources)

    # ClearMetadataPreprocessor().preprocess(nb_new, None)

    # 7. Export notebook with test outputs to html file
    # Setup
    template_name = "feedback"
    nbgrader_path = os.path.dirname(nbgrader.__file__)
    template_dir = os.path.abspath(os.path.join(nbgrader_path, 'server_extensions', 'formgrader', 'templates'))
    extra_static_path = os.path.abspath(os.path.join(nbgrader_path, 'server_extensions', 'formgrader', 'static', 'components', 'bootstrap', 'css'))
    #template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
    #extra_static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'css'))
    
    # Create exporter
    html_exporter = HTMLExporter(
        template_name=template_name,
        extra_template_basedirs=[template_dir],
        extra_template_paths=[extra_static_path],
    )
    
    html_exporter.enable_mathjax = True
    #html_exporter = HTMLExporter(template_name="classic"),
    #(body, resources) = html_exporter.from_notebook_node(nb)

    (body, resources) = html_exporter.from_notebook_node(nb, resources)
    
    with open(output_dir+'/'+filename.split(".")[0]+".html", mode='w', encoding='utf-8') as f:
        f.write(body)
    return points, max_points

def autograde_notebooks(notebook_list):
    """
    Function to run autograding on list of jupyter notebook files.
    Jupyter notebook files are assumed to be assignment files created using
    nbgrader, with the addition of hidden tests being copied to metadata
    for each grade cell.
    """
    student_input = input("Enter problem number to grade, or type 'all' to grade the entire assignment.")

    if student_input.isnumeric() and 1 <= int(student_input) <= len(notebook_list) + 1:
        notebooks_to_grade = [notebook_list[int(student_input) - 1]]
        print(f"Grading problem {notebooks_to_grade[0]}.")
    elif student_input.lower().strip() == 'all':
        notebooks_to_grade = notebook_list
        pring(f"Grading all problems in assignment.")
    else:
        print(f"No valid input detected. Nothing to do.")


    total_score = 0
    max_score = 0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for notebook in notebooks_to_grade:
        notebook_score, notebook_max = run_tests(notebook)
        report_file = notebook.split(".")[0]+".html"
        display(Markdown(
            """%s graded, score: %s/%s. See [%s](test_results/%s) for detailed report.""" %
            (notebook,
             str(notebook_score),
             str(notebook_max),
             report_file,
             report_file)
        ))
        total_score += notebook_score
        max_score += notebook_max
    display(Markdown(
        """Finished grading task(s)! Final score: %s/%s.""" %
        (str(total_score),
         str(max_score))
    ))

# Debugger warnings are disabled by adding -Xfrozen_modules=off to the kernel.json file in /opt/conda/share/jupyter/kernels/python3.