import troposphere.efs as efs

# Create a simple FileSystem object
fs = efs.FileSystem(title="TestFS")

# Convert to dict
dict_repr = fs.to_dict()
print("to_dict() output:")
print(dict_repr)

# Try to reconstruct from dict - this should fail
try:
    fs_recovered = efs.FileSystem.from_dict("TestFS", dict_repr)
    print("Success - no bug")
except AttributeError as e:
    print(f"\nBug found! Error: {e}")
    print("\nThe issue is that to_dict() adds a 'Type' key but from_dict() doesn't handle it")