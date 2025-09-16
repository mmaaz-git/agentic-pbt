#!/usr/bin/env python3
"""Property-based tests for fixit.upgrade module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import libcst as cst
from fixit.upgrade.deprecated_testcase_keywords import FixitDeprecatedTestCaseKeywords
from fixit.upgrade.remove_rule_suffix import FixitRemoveRuleSuffix
from fixit.upgrade.deprecated_import import FixitDeprecatedImport
from fixit import LintRule
import re


# Test 1: FixitDeprecatedTestCaseKeywords - CodeRange calculation
@given(
    line=st.integers(min_value=1, max_value=10000),
    column=st.integers(min_value=0, max_value=200)
)
def test_coderange_calculation_preserves_position(line, column):
    """Test that CodeRange conversion preserves line/column information correctly"""
    
    # Create a test case with line and column
    code = f"""
from fixit import InvalidTestCase
InvalidTestCase(
    "print('hello')",
    line={line},
    column={column},
)
"""
    
    # Parse and apply the rule
    module = cst.parse_module(code)
    rule = FixitDeprecatedTestCaseKeywords()
    wrapper = cst.MetadataWrapper(module)
    
    # Visit the module
    rule.visit_Module(wrapper.module)
    
    # The rule should convert line/column to CodeRange
    # Expected format: CodeRange(start=CodePosition(line, column), end=CodePosition(1 + line, 0))
    # This property verifies the mathematical relationship is maintained
    for violation in wrapper.resolve(rule).violations:
        if violation.replacement:
            new_code = module.code_for_node(violation.replacement)
            # Check that the CodeRange contains the correct values
            assert f"CodePosition({line}, {column})" in new_code
            assert f"CodePosition({1 + line}, 0)" in new_code


# Test 2: FixitRemoveRuleSuffix - Only removes suffix from LintRule subclasses
@given(
    class_name=st.text(
        alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"], min_codepoint=65),
        min_size=1,
        max_size=50
    ).filter(lambda x: x[0].isalpha() and x.isidentifier()),
    has_rule_suffix=st.booleans(),
    inherits_from_lintrule=st.booleans()
)
def test_rule_suffix_removal_correctness(class_name, has_rule_suffix, inherits_from_lintrule):
    """Test that Rule suffix is only removed from LintRule subclasses"""
    
    # Construct class name
    if has_rule_suffix and not class_name.endswith("Rule"):
        class_name = class_name + "Rule"
    elif not has_rule_suffix and class_name.endswith("Rule"):
        class_name = class_name[:-4] + "Foo"  # Avoid accidental Rule suffix
    
    # Create code based on whether it inherits from LintRule
    if inherits_from_lintrule:
        code = f"""
from fixit import LintRule
class {class_name}(LintRule):
    pass
"""
    else:
        code = f"""
class {class_name}:
    pass
"""
    
    # Parse and apply the rule
    module = cst.parse_module(code)
    rule = FixitRemoveRuleSuffix()
    wrapper = cst.MetadataWrapper(module)
    
    violations = list(wrapper.resolve(rule).violations)
    
    # Property: Rule suffix should only be removed if:
    # 1. Class inherits from LintRule
    # 2. Class name ends with "Rule"
    if inherits_from_lintrule and class_name.endswith("Rule"):
        # Should have a violation with replacement
        assert len(violations) == 1
        assert violations[0].replacement
        # The replacement should be the name without "Rule"
        expected_name = class_name[:-4]
        replacement_code = module.code_for_node(violations[0].replacement)
        assert replacement_code == expected_name
    else:
        # Should have no violations
        assert len(violations) == 0


# Test 3: FixitDeprecatedImport - Correct import replacement
@given(
    deprecated_name=st.sampled_from(["CstLintRule", "CSTLintRule", "InvalidTestCase", "ValidTestCase"]),
    use_alias=st.booleans()
)
def test_deprecated_import_replacement(deprecated_name, use_alias):
    """Test that deprecated imports are correctly replaced"""
    
    # Map deprecated names to their replacements
    replacements = {
        "CstLintRule": "LintRule",
        "CSTLintRule": "LintRule", 
        "InvalidTestCase": "Invalid",
        "ValidTestCase": "Valid"
    }
    
    # Create import statement
    if use_alias:
        alias = replacements[deprecated_name]  # Use the new name as alias
        code = f"from fixit import {deprecated_name} as {alias}"
    else:
        code = f"from fixit import {deprecated_name}"
    
    # Parse and apply the rule
    module = cst.parse_module(code)
    rule = FixitDeprecatedImport()
    wrapper = cst.MetadataWrapper(module)
    
    violations = list(wrapper.resolve(rule).violations)
    
    # Should have exactly one violation
    assert len(violations) == 1
    violation = violations[0]
    assert violation.replacement
    
    # The replacement should use the new name
    new_name = replacements[deprecated_name]
    replacement_code = module.code_for_node(violation.replacement)
    
    if use_alias:
        # When alias matches new name, it should be removed
        assert replacement_code == new_name
    else:
        assert replacement_code == new_name


# Test 4: Multiple imports in one statement
@given(
    imports=st.lists(
        st.sampled_from(["CstLintRule", "CSTLintRule", "InvalidTestCase", "ValidTestCase", "LintRule", "Valid", "Invalid"]),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_multiple_imports_handling(imports):
    """Test handling of multiple imports in one statement"""
    
    # Create import statement
    import_list = ", ".join(imports)
    code = f"from fixit import {import_list}"
    
    # Parse and apply the rule  
    module = cst.parse_module(code)
    rule = FixitDeprecatedImport()
    wrapper = cst.MetadataWrapper(module)
    
    violations = list(wrapper.resolve(rule).violations)
    
    # Count how many deprecated imports we have
    deprecated = {"CstLintRule", "CSTLintRule", "InvalidTestCase", "ValidTestCase"}
    deprecated_count = sum(1 for imp in imports if imp in deprecated)
    
    # Should have one violation per deprecated import
    assert len(violations) == deprecated_count


# Test 5: Edge case - parsing complex CodeRange expressions
@given(
    line=st.integers(min_value=1, max_value=10000),
    column=st.integers(min_value=0, max_value=200),
    has_config=st.booleans(),
    has_filename=st.booleans(),
    has_kind=st.booleans()
)
def test_coderange_with_extra_params(line, column, has_config, has_filename, has_kind):
    """Test CodeRange conversion with additional deprecated parameters"""
    
    params = [f'line={line}', f'column={column}']
    if has_config:
        params.append('config=None')
    if has_filename:
        params.append('filename="test.py"')
    if has_kind:
        params.append('kind="X123"')
    
    params_str = ",\n    ".join(params)
    
    code = f"""
from fixit import InvalidTestCase
InvalidTestCase(
    "print('hello')",
    {params_str}
)
"""
    
    # Parse and apply the rule
    module = cst.parse_module(code)
    rule = FixitDeprecatedTestCaseKeywords()
    wrapper = cst.MetadataWrapper(module)
    
    rule.visit_Module(wrapper.module)
    
    violations = list(wrapper.resolve(rule).violations)
    
    # Should have exactly one violation
    assert len(violations) == 1
    
    if violations[0].replacement:
        new_code = module.code_for_node(violations[0].replacement)
        
        # Check that deprecated params are removed
        assert "config=" not in new_code
        assert "filename=" not in new_code
        assert "kind=" not in new_code
        assert "line=" not in new_code
        assert "column=" not in new_code
        
        # Check that CodeRange is added
        assert "range" in new_code
        assert "CodeRange" in new_code
        assert f"CodePosition({line}, {column})" in new_code
        assert f"CodePosition({1 + line}, 0)" in new_code


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])