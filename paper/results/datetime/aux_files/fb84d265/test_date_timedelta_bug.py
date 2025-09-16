import datetime
from hypothesis import given, strategies as st, settings


# Test that demonstrates the bug
@given(
    st.dates(),
    st.timedeltas(min_value=datetime.timedelta(seconds=1), max_value=datetime.timedelta(hours=23))
)
@settings(max_examples=100)
def test_date_timedelta_loses_time_components(date, td_with_time):
    """
    Bug: When adding a timedelta with time components (hours, minutes, seconds) 
    to a date object, the time components are silently lost.
    
    This violates the principle of least surprise and breaks associativity.
    """
    # Only test timedeltas that have time components but less than a day
    assume(td_with_time.days == 0)
    assume(td_with_time.total_seconds() > 0)
    
    result = date + td_with_time
    
    # The result should either:
    # 1. Raise an error (if time components aren't allowed)
    # 2. Return a datetime object with the time components
    # 3. At minimum, change the date if time rolls over
    
    # But what actually happens: time components are silently discarded
    assert result == date  # This passes but shouldn't!
    
    
def test_specific_case_demonstrating_bug():
    """Specific example showing the bug"""
    d = datetime.date(2024, 1, 1)
    td = datetime.timedelta(hours=23, minutes=59, seconds=59)
    
    result = d + td
    print(f"date(2024, 1, 1) + timedelta(hours=23, minutes=59, seconds=59) = {result}")
    print(f"Expected: Either an error or date(2024, 1, 1, 23, 59, 59) or date(2024, 1, 2)")
    print(f"Actual: {result} (time components lost!)")
    
    # This assertion shows the problem
    assert result == d  # Time components were discarded!
    

def test_associativity_violation():
    """This bug breaks associativity of addition"""
    d = datetime.date(2024, 1, 1)
    td1 = datetime.timedelta(hours=13)  # 13 hours
    td2 = datetime.timedelta(hours=12)  # 12 hours
    
    # These should be equal by associativity
    result1 = (d + td1) + td2  # date + date = date(2024, 1, 1) both times
    result2 = d + (td1 + td2)  # date + timedelta(days=1, hours=1) = date(2024, 1, 2)
    
    print(f"(date + 13h) + 12h = {result1}")
    print(f"date + (13h + 12h) = {result2}")
    print(f"Associativity violated: {result1} != {result2}")
    
    assert result1 != result2  # Associativity is broken!


if __name__ == "__main__":
    print("Testing date + timedelta bug...")
    test_specific_case_demonstrating_bug()
    print()
    test_associativity_violation()