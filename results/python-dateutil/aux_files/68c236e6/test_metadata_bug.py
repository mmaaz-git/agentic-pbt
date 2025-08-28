import json
from io import BytesIO
from tarfile import TarFile, TarInfo
import dateutil.zoneinfo


def test_invalid_json_metadata_bug():
    """Reproduce the bug where invalid JSON in METADATA file causes crash"""
    
    # Create a tar file with invalid JSON in METADATA file
    tar_bytes = BytesIO()
    with TarFile.open(mode='w:gz', fileobj=tar_bytes) as tf:
        # Add METADATA file with invalid JSON content
        invalid_json = b"This is not valid JSON!"
        meta_info = TarInfo(name='METADATA')
        meta_info.size = len(invalid_json)
        tf.addfile(meta_info, BytesIO(invalid_json))
    
    tar_bytes.seek(0)
    
    # Try to create ZoneInfoFile - this will crash
    try:
        zif = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes)
        print(f"ERROR: Should have raised JSONDecodeError but got: {zif.metadata}")
    except json.JSONDecodeError as e:
        print(f"BUG CONFIRMED: JSONDecodeError raised: {e}")
        print(f"Error at line {e.lineno}, column {e.colno}")
        return True
    
    return False


def test_empty_metadata_bug():
    """Test with empty METADATA file"""
    tar_bytes = BytesIO()
    with TarFile.open(mode='w:gz', fileobj=tar_bytes) as tf:
        # Add empty METADATA file
        empty_content = b""
        meta_info = TarInfo(name='METADATA')
        meta_info.size = len(empty_content)
        tf.addfile(meta_info, BytesIO(empty_content))
    
    tar_bytes.seek(0)
    
    # Try to create ZoneInfoFile
    try:
        zif = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes)
        print(f"ERROR: Should have raised JSONDecodeError but got: {zif.metadata}")
    except json.JSONDecodeError as e:
        print(f"BUG CONFIRMED (empty): JSONDecodeError raised: {e}")
        return True
    
    return False


if __name__ == "__main__":
    print("Testing invalid JSON metadata bug...")
    bug1 = test_invalid_json_metadata_bug()
    print("\nTesting empty metadata bug...")
    bug2 = test_empty_metadata_bug()
    
    if bug1 or bug2:
        print("\n✅ Bug found in dateutil.zoneinfo.ZoneInfoFile!")
        print("The module doesn't handle invalid JSON in METADATA file gracefully.")