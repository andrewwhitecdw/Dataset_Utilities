import ast
import os


def test_read_function_uses_context_manager():
    """Ensure setup.read() closes the README file after reading it."""
    setup_path = os.path.join(os.path.dirname(__file__), os.pardir, "setup.py")
    with open(setup_path) as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "read":
            assert len(node.body) == 1
            stmt = node.body[0]
            assert isinstance(stmt, ast.With), (
                "read() must use a with-statement to close the file handle"
            )
            ctx = stmt.items[0].context_expr
            assert isinstance(ctx, ast.Call)
            assert ctx.func.id == "open"
            return

