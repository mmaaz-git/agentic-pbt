"""Comprehensive test showing the subdirectory None bug."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages")

from copier._template import Template

def test_subdirectory_with_none():
    """Test that subdirectory property violates its type annotation."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "template"
        template_dir.mkdir()
        
        # Test case 1: Empty value in YAML
        config_file = template_dir / "copier.yml"
        config_file.write_text("_subdirectory: ")
        
        template = Template(url=str(template_dir))
        
        # The type annotation says this returns str, but it returns None
        assert template.subdirectory is None, "Empty YAML value becomes None"
        assert not isinstance(template.subdirectory, str), "Violates type annotation"
        
        # Test case 2: Explicit null in YAML
        config_file.write_text("_subdirectory: null")
        
        # Need to create a new template to clear the cached property
        template = Template(url=str(template_dir))
        
        assert template.subdirectory is None, "Null YAML value becomes None"
        assert not isinstance(template.subdirectory, str), "Violates type annotation"
        
        # Test case 3: Compare with templates_suffix which handles this correctly
        config_file.write_text("_templates_suffix: null\n_subdirectory: null")
        
        template = Template(url=str(template_dir))
        
        # templates_suffix handles None correctly
        assert isinstance(template.templates_suffix, str), "templates_suffix handles None correctly"
        assert template.templates_suffix == ".jinja", "Returns default value"
        
        # subdirectory doesn't handle None
        assert template.subdirectory is None, "subdirectory returns None"
        assert not isinstance(template.subdirectory, str), "Violates type annotation"
        
        print("Bug confirmed: Template.subdirectory returns None instead of empty string")
        print("  This violates its type annotation (-> str)")
        print("  The templates_suffix property handles this case correctly")

if __name__ == "__main__":
    test_subdirectory_with_none()