import nbformat

import os
from base64 import b64decode
from nbgrader.preprocessors import Execute, ClearHiddenTests, GetGrades
from nbgrader.utils import is_grade, determine_grade
from nbconvert import HTMLExporter
from IPython.display import Markdown, display

from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor, ClearMetadataPreprocessor
# Config Options
output_dir = "test_results"

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

    # 2. Copy hidden tests from metadata to cell body
    for cell_data in nb['cells']:
        if cell_data['cell_type'] == 'code':
            if 'distributed_autograding' in cell_data['metadata']:
                test_string = b64decode(cell_data['metadata']['distributed_autograding']['test_code']).decode('utf-8')
                cell_data['source'] += "\n### BEGIN HIDDEN TESTS\n"+test_string+"\n### END HIDDEN TESTS"

    # 3. Execute entire notebook sequentially with hidden tests
    resources = {}
    Execute(timeout=30, kernel_name='python3').preprocess(nb, resources)

    # 4. Get student score
    points = 0
    max_points = 0
    for cell in nb.cells:
        if is_grade(cell):
        #    max_points += get_max_points(cell)
        #    points += get_points(cell)
            cell_points, cell_max_points = determine_grade(cell)
            points += cell_points
            max_points += cell_max_points
            cell.metadata.nbgrader['score'] = cell_points
            cell.metadata.nbgrader['points'] = cell_max_points
    resources['nbgrader']={'score': points, 'max_score': max_points, "late_penalty": 0.0}
    
    # 5. Remove hidden tests
    ClearHiddenTests().preprocess(nb, resources)

    ClearMetadataPreprocessor().preprocess(nb, resources)
    #GetGrades().preprocess(nb, None)
    CSSHTMLHeaderPreprocessor().preprocess(nb, resources)

    # 6. Export notebook with test outputs to html file
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    extra_static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'components', 'bootstrap', 'css'))
    print(template_path)
    html_exporter = HTMLExporter(template_name="feedback", 
                                 extra_template_basedirs = [template_path], 
                                 extra_template_paths = [extra_static_path])
    
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
    total_score = 0
    max_score = 0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for notebook in notebook_list:
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
        """Finished grading all tasks! Final score: %s/%s.""" %
        (str(total_score),
         str(max_score))
    ))