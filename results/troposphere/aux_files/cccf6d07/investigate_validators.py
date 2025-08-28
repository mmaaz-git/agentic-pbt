import troposphere.rds as rds
import troposphere
import inspect

# Get the actual source of some key validation functions
validators = [
    'validate_backup_retention_period',
    'validate_backtrack_window', 
    'validate_iops',
    'validate_network_port',
    'validate_capacity',
    'validate_v2_capacity',
    'validate_v2_max_capacity',
    'validate_str_or_int'
]

for name in validators:
    func = getattr(rds, name)
    print(f"\n{'='*60}")
    print(f"Function: {name}")
    try:
        source = inspect.getsource(func)
        print(source)
    except:
        print("Could not get source")
        
# Also check what integer_range does
print("\n" + "="*60)
print("Looking for integer_range helper:")
try:
    from troposphere import integer_range
    print(f"integer_range signature: {inspect.signature(integer_range)}")
    source = inspect.getsource(integer_range)
    print(source)
except Exception as e:
    print(f"Could not find integer_range: {e}")