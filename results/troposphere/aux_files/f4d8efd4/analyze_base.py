from troposphere import AWSObject, AWSProperty
import inspect

print('=== AWSObject methods ===')
for name in dir(AWSObject):
    if not name.startswith('_') and callable(getattr(AWSObject, name)):
        print(name)

print('\n=== AWSProperty methods ===')
for name in dir(AWSProperty):
    if not name.startswith('_') and callable(getattr(AWSProperty, name)):
        print(name)