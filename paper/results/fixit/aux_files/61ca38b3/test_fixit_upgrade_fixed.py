#!/usr/bin/env python3
"""Property-based tests for fixit.upgrade module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pathlib import Path
import libcst as cst
from fixit.upgrade.deprecated_testcase_keywords import FixitDeprecatedTestCaseKeywords
from fixit.upgrade.remove_rule_suffix import FixitRemoveRuleSuffix
from fixit.upgrade.deprecated_import import FixitDeprecatedImport
from fixit.engine import LintRunner
from fixit.ftypes import Config
import re


# Test 1: FixitRemoveRuleSuffix - idempotence property
@given(
    class_name=st.text(
        alphabet=st.characters(whitelist_categories=["Lu", "Ll"], min_codepoint=65, max_codepoint=122),
        min_size=5,
        max_size=30
    ).filter(lambda x: x[0].isupper() and x.isidentifier() and not x in ['Rule', 'class', 'def', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except'])
)
def test_remove_rule_suffix_idempotence(class_name):
    """Test that applying the rule twice has the same effect as applying it once"""
    
    # Add Rule suffix
    class_name_with_rule = class_name + "Rule"
    
    code = f"""
from fixit import LintRule

class {class_name_with_rule}(LintRule):
    pass
"""
    
    # Apply the rule once
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        # Apply replacements
        first_result = runner.apply_replacements(reports).bytes.decode()
        
        # Apply the rule a second time
        runner2 = LintRunner(path, first_result.encode())
        reports2 = list(runner2.collect_violations([rule], config))
        
        # Property: Second application should have no violations (idempotence)
        assert len(reports2) == 0, f"Rule is not idempotent for {class_name_with_rule}"
        
        # The result should have the Rule suffix removed
        assert class_name in first_result
        assert class_name_with_rule not in first_result


# Test 2: FixitDeprecatedImport - consistent replacement mapping
@given(
    deprecated_name=st.sampled_from(["CstLintRule", "CSTLintRule", "InvalidTestCase", "ValidTestCase"])
)
def test_deprecated_import_consistent_mapping(deprecated_name):
    """Test that the replacement mapping is consistent"""
    
    replacements = {
        "CstLintRule": "LintRule",
        "CSTLintRule": "LintRule", 
        "InvalidTestCase": "Invalid",
        "ValidTestCase": "Valid"
    }
    
    code = f"from fixit import {deprecated_name}"
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitDeprecatedImport()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        expected = replacements[deprecated_name]
        
        # Property: The correct replacement should be in the result
        assert expected in result, f"Expected {expected} in result for {deprecated_name}"
        assert deprecated_name not in result, f"Deprecated {deprecated_name} should not be in result"


# Test 3: CodeRange calculation edge cases
@given(
    line=st.integers(min_value=1, max_value=10000),
    column=st.integers(min_value=0, max_value=200)
)
def test_coderange_line_calculation(line, column):
    """Test that CodeRange end position is always line+1"""
    
    code = f"""
from fixit import InvalidTestCase
InvalidTestCase(
    "test",
    line={line},
    column={column},
)
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitDeprecatedTestCaseKeywords()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        
        # Property: The end position should always be line+1
        # Check that the formula matches expectation
        if "CodeRange" in result:
            # Extract the CodePosition values
            pattern = r"CodePosition\((\d+),\s*(\d+)\)"
            positions = re.findall(pattern, result)
            
            if len(positions) >= 2:
                start_line = int(positions[0][0])
                start_col = int(positions[0][1])
                end_line = int(positions[1][0])
                
                # Properties to verify
                assert start_line == line, f"Start line should be {line}, got {start_line}"
                assert start_col == column, f"Start column should be {column}, got {start_col}"
                assert end_line == line + 1, f"End line should be {line + 1}, got {end_line}"


# Test 4: Multiple imports preservation
@given(
    imports=st.lists(
        st.sampled_from(["LintRule", "Valid", "Invalid"]),
        min_size=2,
        max_size=4,
        unique=True
    ),
    include_deprecated=st.sampled_from(["CstLintRule", "InvalidTestCase", "ValidTestCase"])
)
def test_multiple_imports_preservation(imports, include_deprecated):
    """Test that non-deprecated imports are preserved when fixing deprecated ones"""
    
    # Add the deprecated import to the list
    all_imports = imports + [include_deprecated]
    import_str = ", ".join(all_imports)
    
    code = f"from fixit import {import_str}"
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitDeprecatedImport()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        
        # Property: All non-deprecated imports should still be present
        for imp in imports:
            assert imp in result, f"Non-deprecated import {imp} should be preserved"
        
        # The deprecated import should be replaced
        assert include_deprecated not in result


# Test 5: Empty class name edge case
@given(
    prefix=st.text(
        alphabet=st.characters(whitelist_categories=["Lu"], min_codepoint=65, max_codepoint=90),
        min_size=1,
        max_size=1
    )
)
def test_rule_suffix_removal_short_names(prefix):
    """Test edge case where class name is just 'Rule' or very short"""
    
    # Test with just "Rule" preceded by a letter
    class_name = prefix + "Rule"
    
    code = f"""
from fixit import LintRule

class {class_name}(LintRule):
    pass
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        
        # Property: Should remove "Rule" suffix even for short names
        expected_name = prefix
        assert f"class {expected_name}(" in result, f"Should have class {expected_name}"
        assert f"class {class_name}(" not in result, f"Should not have class {class_name}"


# Test 6: Test parsing edge cases with unusual but valid Python identifiers
@given(
    suffix_variations=st.sampled_from(["rule", "RULE", "RuLe", "ruLE"])
)
def test_case_sensitive_rule_suffix(suffix_variations):
    """Test that the rule is case-sensitive for 'Rule' suffix"""
    
    class_name = f"MyClass{suffix_variations}"
    
    code = f"""
from fixit import LintRule

class {class_name}(LintRule):
    pass
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    
    # Property: Only exact "Rule" suffix should be removed, not other cases
    if suffix_variations == "Rule":
        assert len(reports) == 0  # Already correct, no Rule suffix
    else:
        # These should not trigger the rule since they don't end with exact "Rule"
        assert len(reports) == 0, f"Should not remove suffix '{suffix_variations}'"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])