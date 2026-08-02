import ast
import os


def load_setup_ast():
    """Parse the repository's setup.py for static import analysis."""
    root = os.path.dirname(os.path.abspath(__file__))
    setup_path = os.path.join(root, 'setup.py')
    with open(setup_path, 'r', encoding='utf-8') as f:
        return ast.parse(f.read(), filename=setup_path)


def test_no_unused_top_level_imports():
    """Every top-level import in setup.py must be referenced somewhere."""
    tree = load_setup_ast()

    # Map local import names to their original source names.
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                imported[local] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                imported[local] = alias.name

    # Collect every name that is actually loaded (attribute bases are Name
    # loads, so e.g. `os.path.abspath` counts as a use of `os`).
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)

    unused = [name for name in imported if name not in used]
    assert not unused, f"Unused top-level imports in setup.py: {unused}"


def test_command_and_glob_not_imported():
    """The previously removed dead imports must stay gone."""
    tree = load_setup_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'setuptools':
            imported = {alias.name for alias in node.names}
            assert 'Command' not in imported, (
                "setup.py imports unused setuptools.Command"
            )
        if isinstance(node, ast.Import):
            imported_modules = {alias.name for alias in node.names}
            assert 'glob' not in imported_modules, (
                "setup.py imports unused glob"
