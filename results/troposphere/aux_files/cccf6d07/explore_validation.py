import troposphere.rds as rds
import troposphere
import inspect

# Look at the validation functions
print("Validation functions in troposphere.rds:")
for name, obj in inspect.getmembers(rds):
    if callable(obj) and 'validate' in name:
        print(f"\n{name}:")
        print(f"  Signature: {inspect.signature(obj)}")
        if obj.__doc__:
            print(f"  Doc: {obj.__doc__[:200]}")
        # Try to get source
        try:
            source = inspect.getsource(obj)
            lines = source.split('\n')[:10]
            print(f"  Source preview:")
            for line in lines[:5]:
                print(f"    {line}")
        except:
            pass

# Test a simple DBParameterGroup creation
print("\n" + "="*60)
print("Testing DBParameterGroup creation:")
try:
    db_param = rds.DBParameterGroup(
        "TestDBParamGroup",
        Description="Test parameter group",
        Family="mysql8.0",
        Parameters={"max_connections": "100"}
    )
    print(f"Successfully created: {db_param}")
    print(f"Dict output: {db_param.to_dict()}")
except Exception as e:
    print(f"Error: {e}")