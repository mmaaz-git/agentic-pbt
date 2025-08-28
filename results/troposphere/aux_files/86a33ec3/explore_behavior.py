import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import frauddetector

# Test basic instantiation
print("Testing basic instantiation:")
try:
    # EntityType requires Name
    entity = frauddetector.EntityType("MyEntity", Name="test_entity")
    print(f"EntityType created: {entity.title}, props: {entity.properties}")
except Exception as e:
    print(f"EntityType error: {e}")

try:
    # Label requires Name
    label = frauddetector.Label("MyLabel", Name="test_label")
    print(f"Label created: {label.title}, props: {label.properties}")
except Exception as e:
    print(f"Label error: {e}")

try:
    # Variable requires multiple required fields
    var = frauddetector.Variable("MyVar", 
                                  Name="test_var",
                                  DataSource="EVENT",
                                  DataType="STRING",
                                  DefaultValue="default")
    print(f"Variable created: {var.title}, props: {var.properties}")
except Exception as e:
    print(f"Variable error: {e}")

# Test to_dict method
print("\nTesting to_dict:")
entity = frauddetector.EntityType("MyEntity", Name="test_entity", Description="Test description")
print(f"EntityType.to_dict(): {entity.to_dict()}")

# Test if List class conflicts with built-in list
print("\nTesting List class:")
try:
    mylist = frauddetector.List("MyList", Name="test_list")
    print(f"List created: {mylist.title}, type: {type(mylist)}")
    print(f"List.to_dict(): {mylist.to_dict()}")
except Exception as e:
    print(f"List error: {e}")