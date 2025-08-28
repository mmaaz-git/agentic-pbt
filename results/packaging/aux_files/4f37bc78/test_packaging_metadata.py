import packaging.metadata
from hypothesis import given, strategies as st, assume, settings
import re


# Strategy for generating valid metadata field names
field_names = st.sampled_from([
    "Metadata-Version", "Name", "Version", "Summary", "Description",
    "Author", "Author-Email", "Maintainer", "Maintainer-Email",
    "Home-Page", "Download-URL", "License", "Keywords",
    "Classifier", "Platform", "Requires", "Provides", "Obsoletes",
    "Requires-Dist", "Provides-Dist", "Obsoletes-Dist",
    "Requires-Python", "Requires-External", "Project-URL",
    "Description-Content-Type", "Provides-Extra", "Dynamic",
    "License-Expression", "License-File"
])

# Strategy for generating valid field values
field_values = st.text(min_size=1, max_size=100).filter(lambda x: '\n' not in x and '\r' not in x and x.strip())

# Strategy for generating valid version strings
version_strings = st.one_of(
    st.from_regex(r"[0-9]+\.[0-9]+(\.[0-9]+)?", fullmatch=True),
    st.just("1.0.0"),
    st.just("2.1"),
    st.just("0.0.1")
)

# Strategy for generating package names
package_names = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]{0,50}", fullmatch=True)

# Strategy for generating email addresses
email_addresses = st.from_regex(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", fullmatch=True)


@st.composite
def valid_metadata_email(draw):
    """Generate valid metadata in email format."""
    name = draw(package_names)
    version = draw(version_strings)
    
    # Always include required fields
    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}"
    ]
    
    # Optionally add other fields
    if draw(st.booleans()):
        summary = draw(field_values)
        lines.append(f"Summary: {summary}")
    
    if draw(st.booleans()):
        author = draw(st.text(min_size=1, max_size=50).filter(lambda x: '\n' not in x))
        lines.append(f"Author: {author}")
    
    if draw(st.booleans()):
        email = draw(email_addresses)
        lines.append(f"Author-Email: {email}")
    
    if draw(st.booleans()):
        # Add multiple classifiers
        n_classifiers = draw(st.integers(min_value=1, max_value=5))
        for _ in range(n_classifiers):
            classifier = draw(st.sampled_from([
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3",
                "Topic :: Software Development"
            ]))
            lines.append(f"Classifier: {classifier}")
    
    return '\n'.join(lines)


@st.composite
def metadata_with_unknown_fields(draw):
    """Generate metadata that might have unknown or malformed fields."""
    base = draw(valid_metadata_email())
    
    # Add some potentially problematic fields
    if draw(st.booleans()):
        unknown_field = draw(st.from_regex(r"[A-Z][a-z-]{3,20}", fullmatch=True))
        value = draw(field_values)
        base += f"\n{unknown_field}: {value}"
    
    return base


@given(valid_metadata_email())
def test_parse_email_does_not_crash(data):
    """Test that parse_email handles valid metadata without crashing."""
    raw_metadata, unparsed = packaging.metadata.parse_email(data)
    assert isinstance(raw_metadata, dict)
    assert isinstance(unparsed, dict)


@given(valid_metadata_email())
def test_from_email_with_valid_data(data):
    """Test that from_email works with valid metadata."""
    metadata = packaging.metadata.Metadata.from_email(data)
    assert metadata.name is not None
    assert metadata.version is not None
    assert metadata.metadata_version == "2.1"


@given(valid_metadata_email())
def test_parse_and_from_raw_consistency(data):
    """Test that parse_email followed by from_raw gives same result as from_email."""
    # Parse with parse_email and then create Metadata from raw
    raw_metadata, _ = packaging.metadata.parse_email(data)
    
    try:
        metadata1 = packaging.metadata.Metadata.from_raw(raw_metadata)
        metadata2 = packaging.metadata.Metadata.from_email(data)
        
        # Compare key fields
        assert metadata1.name == metadata2.name
        assert metadata1.version == metadata2.version
        assert metadata1.metadata_version == metadata2.metadata_version
        
        # Compare optional fields that might be present
        for field in ['summary', 'author', 'author_email', 'classifiers']:
            assert getattr(metadata1, field) == getattr(metadata2, field)
    except packaging.metadata.InvalidMetadata:
        # If from_raw fails, from_email should also fail
        try:
            packaging.metadata.Metadata.from_email(data)
            assert False, "from_email should have failed if from_raw failed"
        except packaging.metadata.InvalidMetadata:
            pass  # Both failed, which is consistent


@given(metadata_with_unknown_fields())
def test_validation_toggle(data):
    """Test that validate=False is more permissive than validate=True."""
    # Try with validation on
    try:
        metadata_validated = packaging.metadata.Metadata.from_email(data, validate=True)
        validated_success = True
    except (packaging.metadata.InvalidMetadata, ExceptionGroup):
        validated_success = False
    
    # Try with validation off
    try:
        metadata_unvalidated = packaging.metadata.Metadata.from_email(data, validate=False)
        unvalidated_success = True
    except (packaging.metadata.InvalidMetadata, ExceptionGroup):
        unvalidated_success = False
    
    # validate=False should never fail when validate=True succeeds
    if validated_success:
        assert unvalidated_success, "validate=False failed when validate=True succeeded"


@given(valid_metadata_email())
def test_case_sensitivity_in_field_names(data):
    """Test that field names are parsed case-insensitively."""
    # Create a version with lowercase field names
    lines = data.split('\n')
    modified_lines = []
    for line in lines:
        if ':' in line:
            field, value = line.split(':', 1)
            # Convert some fields to lowercase
            if field in ['Name', 'Version', 'Summary', 'Author']:
                modified_lines.append(f"{field.lower()}:{value}")
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)
    
    modified_data = '\n'.join(modified_lines)
    
    # Both should parse successfully
    raw1, _ = packaging.metadata.parse_email(data)
    raw2, _ = packaging.metadata.parse_email(modified_data)
    
    # Should have same fields parsed
    assert set(raw1.keys()) == set(raw2.keys())
    
    # Values should match for common fields
    for key in ['name', 'version']:
        if key in raw1 and key in raw2:
            assert raw1[key] == raw2[key]


@given(st.lists(st.sampled_from([
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Development Status :: 3 - Alpha"
]), min_size=2, max_size=10))
def test_multiple_value_fields(classifiers):
    """Test that fields allowed to appear multiple times are stored as lists."""
    metadata_str = "Metadata-Version: 2.1\nName: test\nVersion: 1.0.0\n"
    for classifier in classifiers:
        metadata_str += f"Classifier: {classifier}\n"
    
    raw_metadata, _ = packaging.metadata.parse_email(metadata_str)
    
    # Classifiers should be stored as a list
    assert 'classifiers' in raw_metadata
    assert isinstance(raw_metadata['classifiers'], list)
    assert len(raw_metadata['classifiers']) == len(classifiers)
    assert set(raw_metadata['classifiers']) == set(classifiers)
    
    # Also test with Metadata object
    metadata = packaging.metadata.Metadata.from_email(metadata_str)
    assert metadata.classifiers == classifiers


@given(st.text(min_size=0, max_size=1000))
def test_parse_email_robustness(data):
    """Test that parse_email doesn't crash on arbitrary input."""
    try:
        raw_metadata, unparsed = packaging.metadata.parse_email(data)
        assert isinstance(raw_metadata, dict)
        assert isinstance(unparsed, dict)
    except Exception as e:
        # Should only raise specific exceptions, not arbitrary errors
        assert isinstance(e, (ValueError, TypeError, UnicodeDecodeError))


@given(st.sampled_from(["Name", "Version", "Summary", "Author"]),
       field_values)
def test_whitespace_handling(field_name, value):
    """Test that leading/trailing whitespace in values is handled correctly."""
    # Add various whitespace
    values_to_test = [
        value,
        f" {value}",
        f"{value} ",
        f"  {value}  ",
        f"\t{value}\t"
    ]
    
    results = []
    for test_value in values_to_test:
        metadata_str = f"Metadata-Version: 2.1\nName: test\nVersion: 1.0.0\n{field_name}: {test_value}"
        raw_metadata, _ = packaging.metadata.parse_email(metadata_str)
        
        field_key = field_name.lower().replace('-', '_')
        if field_key in raw_metadata:
            results.append(raw_metadata[field_key])
    
    # All should parse to the same trimmed value
    if results:
        assert all(r == results[0] for r in results), f"Inconsistent whitespace handling: {results}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])