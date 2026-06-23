"""Fix notebook files to be Databricks-executable."""

import json
from pathlib import Path


def fix_notebook(ipynb_path: Path):
    """Fix a notebook file to be Databricks-executable."""
    with open(ipynb_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Add metadata if missing
    if not notebook.get('metadata'):
        notebook['metadata'] = {}
    if not notebook['metadata'].get('language_info'):
        notebook['metadata']['language_info'] = {'name': 'python'}
    
    # Fix cells
    new_cells = []
    execution_count = 1
    
    i = 0
    while i < len(notebook['cells']):
        cell = notebook['cells'][i]
        
        # Combine docstring cells into markdown
        if cell['cell_type'] == 'code' and cell['source']:
            source_str = ''.join(cell['source']).strip()
            if source_str.startswith('"""') and source_str.endswith('"""'):
                # This is a docstring, convert to markdown
                docstring_content = source_str[3:-3].strip()
                if i + 1 < len(notebook['cells']):
                    next_cell = notebook['cells'][i + 1]
                    if next_cell['cell_type'] == 'code' and next_cell['source']:
                        next_source_str = ''.join(next_cell['source']).strip()
                        if next_source_str.startswith('"') and next_source_str.endswith('"'):
                            # Combine with next cell
                            docstring_content += '\n' + next_source_str[1:-1].strip()
                            i += 1
                
                # Create markdown cell with %md magic command
                new_cells.append({
                    'cell_type': 'code',
                    'execution_count': execution_count,
                    'id': cell.get('id'),
                    'metadata': {},
                    'outputs': [],
                    'source': ['%md\n', docstring_content]
                })
                execution_count += 1
                i += 1
                continue
        
        # Fix comment-only cells to markdown with %md
        if cell['cell_type'] == 'code' and cell['source']:
            source_str = ''.join(cell['source']).strip()
            if source_str.startswith('#'):
                # This is a comment, convert to markdown
                new_cells.append({
                    'cell_type': 'code',
                    'execution_count': execution_count,
                    'id': cell.get('id'),
                    'metadata': {},
                    'outputs': [],
                    'source': ['%md\n', source_str[1:].strip()]
                })
                execution_count += 1
                i += 1
                continue
        
        # Fix code cells
        if cell['cell_type'] == 'code':
            cell['execution_count'] = execution_count
            execution_count += 1
            if not cell.get('outputs'):
                cell['outputs'] = []
            new_cells.append(cell)
            i += 1
            continue
        
        # Keep other cells as is
        new_cells.append(cell)
        i += 1
    
    notebook['cells'] = new_cells
    
    # Write back
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"Fixed {ipynb_path}")


if __name__ == "__main__":
    notebooks_dir = Path(__file__).parent.parent / "code" / "remote" / "notebooks"
    
    for ipynb_file in notebooks_dir.glob("*.ipynb"):
        if ipynb_file.name != "step2_silver_table.ipynb":  # Skip already fixed
            fix_notebook(ipynb_file)
