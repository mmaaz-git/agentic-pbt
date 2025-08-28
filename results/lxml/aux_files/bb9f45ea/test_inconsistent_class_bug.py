"""
Test for inconsistent element class assignment due to repeated lookup calls
"""

from lxml import etree, pyclasslookup
import random


class RandomElement1(etree.ElementBase):
    class_name = "RandomElement1"


class RandomElement2(etree.ElementBase):
    class_name = "RandomElement2"


class InconsistentLookup(pyclasslookup.PythonElementClassLookup):
    """A lookup that returns different classes on repeated calls"""
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.assignments = {}
    
    def lookup(self, doc, element):
        self.call_count += 1
        
        # For root, always return None (default)
        if self.call_count == 1:
            return None
        
        # For other elements, alternate between two custom classes
        # This simulates a lookup that might return different results
        # based on some external state
        if self.call_count % 2 == 0:
            chosen_class = RandomElement1
        else:
            chosen_class = RandomElement2
        
        # Track what we assigned
        key = f"{element.tag}_{self.call_count}"
        self.assignments[key] = chosen_class.__name__
        
        return chosen_class


def test_inconsistent_class_assignment():
    """
    Test if repeated iterations can cause the same element 
    to have different classes due to repeated lookup calls
    """
    
    xml = '<root><child1/><child2/></root>'
    
    lookup = InconsistentLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    result = etree.XML(xml, parser)
    
    print("First iteration - checking element classes:")
    first_iter_classes = []
    for elem in result.iter():
        elem_class = type(elem).__name__
        first_iter_classes.append((elem.tag, elem_class))
        print(f"  {elem.tag}: {elem_class}")
    
    print("\nSecond iteration - checking if classes remain consistent:")
    second_iter_classes = []
    for elem in result.iter():
        elem_class = type(elem).__name__
        second_iter_classes.append((elem.tag, elem_class))
        print(f"  {elem.tag}: {elem_class}")
    
    print("\nThird iteration:")
    third_iter_classes = []
    for elem in result.iter():
        elem_class = type(elem).__name__
        third_iter_classes.append((elem.tag, elem_class))
        print(f"  {elem.tag}: {elem_class}")
    
    print(f"\nTotal lookup calls: {lookup.call_count}")
    print(f"Lookup assignments: {lookup.assignments}")
    
    # Check consistency
    print("\nConsistency check:")
    for i, (tag, cls) in enumerate(first_iter_classes):
        if i < len(second_iter_classes):
            tag2, cls2 = second_iter_classes[i]
            tag3, cls3 = third_iter_classes[i]
            if cls != cls2 or cls != cls3:
                print(f"  INCONSISTENCY: {tag} had classes {cls}, {cls2}, {cls3}")
            else:
                print(f"  {tag}: Consistent class {cls}")
    
    # The issue: the same element can have different classes across iterations
    # because lookup is called again and might return different results
    
    # Check if child elements changed classes
    child1_classes = [cls for tag, cls in first_iter_classes + second_iter_classes + third_iter_classes if tag == 'child1']
    child2_classes = [cls for tag, cls in first_iter_classes + second_iter_classes + third_iter_classes if tag == 'child2']
    
    unique_child1_classes = set(child1_classes)
    unique_child2_classes = set(child2_classes)
    
    print(f"\nchild1 had classes: {unique_child1_classes}")
    print(f"child2 had classes: {unique_child2_classes}")
    
    if len(unique_child1_classes) > 1 or len(unique_child2_classes) > 1:
        print("\nBUG FOUND: Elements can have inconsistent class assignment across iterations!")
        return True
    
    return False


class StatefulLookup(pyclasslookup.PythonElementClassLookup):
    """A lookup that changes behavior based on state"""
    def __init__(self):
        super().__init__()
        self.state = "initial"
        self.call_count = 0
    
    def lookup(self, doc, element):
        self.call_count += 1
        
        # Change state after some calls
        if self.call_count == 3:
            self.state = "changed"
        
        # Return different classes based on state
        if self.state == "initial":
            if element.tag == "important":
                return RandomElement1
        else:
            if element.tag == "important":
                return RandomElement2
        
        return None


def test_stateful_lookup_issue():
    """Test if stateful lookups can cause issues"""
    
    xml = '<root><important/><other/></root>'
    
    lookup = StatefulLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    result = etree.XML(xml, parser)
    
    print("Testing stateful lookup behavior:")
    
    # First access
    important = result[0]
    print(f"  First access - important element class: {type(important).__name__}")
    initial_class = type(important).__name__
    
    # Trigger more lookups to change state
    _ = list(result.iter())
    
    # Access important element again
    important_again = result[0]
    print(f"  Second access - important element class: {type(important_again).__name__}")
    second_class = type(important_again).__name__
    
    # Check if the same element reference has consistent class
    print(f"  Same reference check: {type(important).__name__} vs {type(important_again).__name__}")
    
    # They should be the same object
    print(f"  Same object? {important is important_again}")
    
    return initial_class, second_class


if __name__ == "__main__":
    print("=" * 60)
    print("Testing for inconsistent element class assignment")
    print("=" * 60)
    
    bug_found = test_inconsistent_class_assignment()
    
    print("\n" + "=" * 60)
    print("Testing stateful lookup issue")
    print("=" * 60)
    
    initial, second = test_stateful_lookup_issue()
    
    if bug_found:
        print("\n" + "=" * 60)
        print("CRITICAL BUG: Elements can have different classes across iterations!")
        print("This violates the principle of consistent object behavior.")
        print("=" * 60)