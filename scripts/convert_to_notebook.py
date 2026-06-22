"""Convert Python files to Jupyter notebook format."""

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_notebook


def py_to_ipynb(py_path: Path, ipynb_path: Path):
    """Convert a Python file to Jupyter notebook format."""
    with open(py_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Create a new notebook
    notebook = new_notebook()

    # Split code into cells (simplified approach)
    lines = code.split('\n')
    current_cell = []

    for line in lines:
        # Simple heuristic: new cell on empty lines or comments
        if line.strip() == '' or line.strip().startswith('#'):
            if current_cell:
                notebook.cells.append(new_code_cell('\n'.join(current_cell)))
                current_cell = []
            if line.strip().startswith('#'):
                notebook.cells.append(new_code_cell(line))
        else:
            current_cell.append(line)

    if current_cell:
        notebook.cells.append(new_code_cell('\n'.join(current_cell)))

    # Write notebook
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)

    print(f"Converted {py_path} to {ipynb_path}")


if __name__ == "__main__":
    notebooks_dir = Path(__file__).parent.parent / "code" / "remote" / "notebooks"

    for py_file in notebooks_dir.glob("*.py"):
        ipynb_file = py_file.with_suffix('.ipynb')
        py_to_ipynb(py_file, ipynb_file)
