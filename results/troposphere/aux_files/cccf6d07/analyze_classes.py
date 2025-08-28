import troposphere.rds as rds
import inspect

# Focus on the main classes
main_classes = [
    rds.DBInstance,
    rds.DBCluster,
    rds.DBParameterGroup,
    rds.DBProxy
]

for cls in main_classes:
    print(f"\n{'='*60}")
    print(f"Class: {cls.__name__}")
    print(f"Base classes: {[b.__name__ for b in cls.__bases__]}")
    
    # Get properties
    if hasattr(cls, 'props'):
        print(f"\nProperties ({len(cls.props)}):")
        for prop_name, prop_info in list(cls.props.items())[:10]:
            print(f"  - {prop_name}: {prop_info}")
    
    # Get validation methods
    validation_methods = [m for m in dir(cls) if m.startswith('validate')]
    if validation_methods:
        print(f"\nValidation methods: {validation_methods}")
        
    # Get other methods
    methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m)) and not m.startswith('validate')][:5]
    print(f"\nOther methods: {methods}")