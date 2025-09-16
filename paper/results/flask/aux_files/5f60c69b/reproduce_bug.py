import flask.sansio.scaffold

# According to the docstring, get_root_path should:
# "If it cannot be found, returns the current working directory."
# But for built-in modules, it raises RuntimeError instead

try:
    result = flask.sansio.scaffold.get_root_path('sys')
    print(f"Success: {result}")
except RuntimeError as e:
    print(f"BUG: Function raised RuntimeError instead of returning cwd")
    print(f"Error message: {e}")