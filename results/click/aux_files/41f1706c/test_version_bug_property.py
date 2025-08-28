from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import click.shell_completion as shell_completion


@given(
    major=st.integers(min_value=1, max_value=99),
    minor=st.integers(min_value=0, max_value=99),
    patch_ver=st.integers(min_value=0, max_value=99)
)
@settings(max_examples=1000)
def test_bash_version_comparison_property(major, minor, patch_ver):
    """Version comparison should use numeric comparison, not string comparison"""
    
    version_string = f"{major}.{minor}.{patch_ver}"
    
    # Expected behavior: warn if version < 4.4
    should_warn = (major < 4) or (major == 4 and minor < 4)
    
    # Test actual behavior
    mock_result = MagicMock()
    mock_result.stdout = version_string.encode()
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('shutil.which', return_value='/bin/bash'):
            with patch('click.shell_completion.echo') as mock_echo:
                shell_completion.BashComplete._check_version()
                
                actually_warned = mock_echo.called
                
                # The bug: string comparison causes incorrect warnings
                # This assertion will fail for versions like 4.10, 10.0, etc.
                assert actually_warned == should_warn, \
                    f"Version {version_string}: expected {'warn' if should_warn else 'no warn'}, " \
                    f"got {'warn' if actually_warned else 'no warn'}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])