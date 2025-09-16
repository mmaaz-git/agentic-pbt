"""Minimal reproduction of Blueprint path inconsistency bug"""

import flask.blueprints as bp
import os

# Create blueprint with relative paths for both static and template folders
blueprint = bp.Blueprint(
    'test_blueprint',
    __name__,
    static_folder='static',
    template_folder='templates'
)

print("Input values:")
print(f"  static_folder: 'static' (relative path)")
print(f"  template_folder: 'templates' (relative path)")

print("\nBlueprint attributes after creation:")
print(f"  blueprint.static_folder: {blueprint.static_folder}")
print(f"  blueprint.template_folder: {blueprint.template_folder}")

print("\nPath type analysis:")
print(f"  static_folder is absolute: {os.path.isabs(blueprint.static_folder)}")
print(f"  template_folder is absolute: {os.path.isabs(blueprint.template_folder) if blueprint.template_folder else False}")

print("\nInconsistency detected:")
print("  static_folder was converted from relative to absolute path")
print("  template_folder remained as relative path")
print("  This violates the principle of least surprise and API consistency")