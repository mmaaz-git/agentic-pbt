import json
from io import BytesIO
from tarfile import TarFile, TarInfo
from hypothesis import given, strategies as st, settings
import dateutil.zoneinfo


@given(st.binary())
@settings(max_examples=100)
def test_metadata_parsing_robustness(metadata_content):
    """Property: ZoneInfoFile should handle any binary content in METADATA file without crashing"""
    
    # Create a tar file with arbitrary binary content in METADATA file
    tar_bytes = BytesIO()
    with TarFile.open(mode='w:gz', fileobj=tar_bytes) as tf:
        # Add METADATA file with arbitrary content
        meta_info = TarInfo(name='METADATA')
        meta_info.size = len(metadata_content)
        tf.addfile(meta_info, BytesIO(metadata_content))
    
    tar_bytes.seek(0)
    
    # ZoneInfoFile should either:
    # 1. Successfully parse valid JSON
    # 2. Gracefully handle invalid JSON (e.g., set metadata to None)
    # But it should NEVER crash with an unhandled exception
    
    # This will raise JSONDecodeError for invalid JSON - that's the bug!
    zif = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes)


if __name__ == "__main__":
    import pytest
    
    # Run hypothesis test
    print("Running property-based test for metadata parsing...")
    test_result = test_metadata_parsing_robustness()
    
    # The test will fail quickly due to the bug