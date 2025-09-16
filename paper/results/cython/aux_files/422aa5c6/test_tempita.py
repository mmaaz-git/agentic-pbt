import Cython.Tempita
from hypothesis import given, strategies as st, assume, settings
import re


@given(st.text())
def test_no_substitution_identity(text):
    """Text without template markers should pass through unchanged"""
    assume('{{' not in text and '}}' not in text)
    template = Cython.Tempita.Template(text)
    result = template.substitute()
    assert result == text


@given(st.text(), st.text().filter(lambda x: x.isidentifier() and x))
def test_sub_template_equivalence(template_str, var_name):
    """sub() function should behave identically to Template().substitute()"""
    template_with_var = f"prefix {{{{name}}}} middle {{{{name}}}} suffix"
    
    # Using Template class
    template = Cython.Tempita.Template(template_with_var)
    result1 = template.substitute(name=var_name)
    
    # Using sub function
    result2 = Cython.Tempita.sub(template_with_var, name=var_name)
    
    assert result1 == result2


@given(st.text().filter(lambda x: x.isidentifier() and x), st.text())
def test_multiple_substitution_consistency(var_name, value):
    """Multiple occurrences of same variable should all be replaced identically"""
    template_str = f"{{{{{var_name}}}}} and {{{{{var_name}}}}} and {{{{{var_name}}}}}"
    template = Cython.Tempita.Template(template_str)
    result = template.substitute(**{var_name: value})
    
    # All occurrences should be replaced with the same value
    parts = result.split(' and ')
    assert len(parts) == 3
    assert parts[0] == parts[1] == parts[2] == str(value)


@given(st.dictionaries(st.text().filter(lambda x: x.isidentifier() and x), st.text()))
def test_empty_template_invariant(namespace):
    """Empty template always returns empty string regardless of namespace"""
    template = Cython.Tempita.Template('')
    result = template.substitute(**namespace)
    assert result == ''


@given(st.text().filter(lambda x: '{{' not in x and '}}' not in x and '[[' not in x and ']]' not in x),
       st.text().filter(lambda x: x.isidentifier() and x))
def test_delimiter_consistency(plain_text, var_name):
    """Custom delimiters should work equivalently to default delimiters"""
    # Template with default delimiters
    template_default = f"{plain_text} {{{{{var_name}}}}} {plain_text}"
    t1 = Cython.Tempita.Template(template_default)
    result1 = t1.substitute(**{var_name: 'VALUE'})
    
    # Template with custom delimiters
    template_custom = f"{plain_text} [[{var_name}]] {plain_text}"
    t2 = Cython.Tempita.Template(template_custom, delimiters=('[[', ']]'))
    result2 = t2.substitute(**{var_name: 'VALUE'})
    
    assert result1 == result2


@given(st.text().filter(lambda x: x.isidentifier() and x))
def test_undefined_variable_error(var_name):
    """Using undefined variable should raise NameError"""
    template = Cython.Tempita.Template(f"{{{{{var_name}}}}}")
    try:
        result = template.substitute()  # No variables provided
        assert False, "Should have raised NameError"
    except NameError as e:
        assert var_name in str(e)


@given(st.lists(st.text()))
def test_for_loop_length_preservation(items):
    """For loop should produce one output line per item"""
    template_str = """{{for item in items}}{{item}}
{{endfor}}"""
    template = Cython.Tempita.Template(template_str)
    result = template.substitute(items=items)
    
    # Count non-empty lines
    lines = [line for line in result.split('\n') if line]
    assert len(lines) == len(items)


@given(st.integers(), st.integers())
def test_expression_evaluation(x, y):
    """Expressions in templates should evaluate correctly"""
    template = Cython.Tempita.Template('{{x}} + {{y}} = {{x + y}}')
    result = template.substitute(x=x, y=y)
    expected = f"{x} + {y} = {x + y}"
    assert result == expected


@given(st.text())
def test_escaped_delimiters(text):
    """Escaped delimiters should be treated as literal text"""
    # Test that {{ can appear in output if properly handled
    template = Cython.Tempita.Template('${{}}', delimiters=('${{', '}}'))
    result = template.substitute()
    assert result == ''  # Empty expression
    
    
@given(st.text().filter(lambda x: x and not x.isspace()))
def test_whitespace_handling_in_expressions(value):
    """Whitespace around variable names should not affect substitution"""
    template1 = Cython.Tempita.Template('{{value}}')
    template2 = Cython.Tempita.Template('{{ value }}')
    template3 = Cython.Tempita.Template('{{  value  }}')
    
    result1 = template1.substitute(value=value)
    result2 = template2.substitute(value=value)
    result3 = template3.substitute(value=value)
    
    assert result1 == result2 == result3 == str(value)