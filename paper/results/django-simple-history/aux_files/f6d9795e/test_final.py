import os
import sys
import datetime
import random
import string

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings_v2')

import django
from django.db import models, connection
from django.utils import timezone
django.setup()

from simple_history.models import HistoricalRecords
from simple_history.manager import HistoricalQuerySet, HistoryManager
from hypothesis import given, strategies as st, settings as hypo_settings, assume, seed
import pytest

# Create in-memory test tables
cursor = connection.cursor()

# Simple test model with history
cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_model (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        value INTEGER NOT NULL,
        deleted BOOLEAN DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_historical_model (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        id INTEGER,
        name VARCHAR(100) NOT NULL,
        value INTEGER NOT NULL,
        deleted BOOLEAN DEFAULT 0,
        history_date DATETIME NOT NULL,
        history_change_reason VARCHAR(100),
        history_type VARCHAR(1) NOT NULL,
        history_user_id INTEGER NULL
    )
''')

connection.commit()

def clear_tables():
    cursor.execute("DELETE FROM test_model")
    cursor.execute("DELETE FROM test_historical_model")
    connection.commit()

def insert_historical_record(obj_id, name, value, history_date, history_type, deleted=False):
    cursor.execute('''
        INSERT INTO test_historical_model 
        (id, name, value, deleted, history_date, history_type, history_change_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (obj_id, name, value, deleted, history_date, history_type, ''))
    connection.commit()

# Test 1: Check latest_of_each edge cases with duplicate timestamps
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=3),  # Limited IDs for overlap
            st.integers(min_value=0, max_value=100)  # Time offset in hours
        ),
        min_size=5,
        max_size=20
    )
)
@hypo_settings(max_examples=100, deadline=None)
def test_latest_of_each_duplicate_timestamps(records):
    """
    Test latest_of_each() behavior when multiple records have the same history_date
    This can reveal undefined behavior or bugs in tie-breaking
    """
    clear_tables()
    
    base_date = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    # Insert records, deliberately creating some with identical timestamps
    for i, (obj_id, hours_offset) in enumerate(records):
        # Use integer division to create duplicate timestamps
        rounded_offset = (hours_offset // 10) * 10  # Round to nearest 10 hours
        history_date = base_date + datetime.timedelta(hours=rounded_offset)
        insert_historical_record(obj_id, f"name_{i}", i, history_date, '+')
    
    # Check for records with exactly the same id and timestamp
    cursor.execute('''
        SELECT id, history_date, COUNT(*) as cnt
        FROM test_historical_model
        GROUP BY id, history_date
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"Found {len(duplicates)} cases of duplicate (id, history_date) pairs")
        
        # Test the SQL that latest_of_each() should generate
        cursor.execute('''
            SELECT h1.id, h1.history_id, h1.history_date, h1.value
            FROM test_historical_model h1
            WHERE NOT EXISTS (
                SELECT 1 FROM test_historical_model h2
                WHERE h2.id = h1.id 
                AND h2.history_date > h1.history_date
            )
            ORDER BY h1.id
        ''')
        
        results = cursor.fetchall()
        
        # Check for multiple records per ID (shouldn't happen)
        id_counts = {}
        for row in results:
            obj_id = row[0]
            id_counts[obj_id] = id_counts.get(obj_id, 0) + 1
        
        for obj_id, count in id_counts.items():
            if count > 1:
                print(f"BUG: Object {obj_id} appears {count} times in latest_of_each results!")
                print("This indicates the query doesn't handle timestamp ties correctly")
                
                # Get details of the duplicate records
                cursor.execute('''
                    SELECT history_id, value, history_date
                    FROM test_historical_model
                    WHERE id = ?
                    ORDER BY history_date DESC, history_id DESC
                ''', (obj_id,))
                
                records = cursor.fetchall()
                print(f"  Records for object {obj_id}:")
                for rec in records[:5]:  # Show first 5
                    print(f"    history_id={rec[0]}, value={rec[1]}, date={rec[2]}")
                
                return False  # Bug found
    
    return True

# Test 2: Test for microsecond precision issues
@given(
    st.lists(
        st.integers(min_value=0, max_value=999999),  # Microseconds
        min_size=3,
        max_size=10,
        unique=True
    )
)
@hypo_settings(max_examples=50, deadline=None)
def test_microsecond_precision(microseconds):
    """
    Test that datetime comparisons handle microsecond precision correctly
    """
    clear_tables()
    
    base_date = datetime.datetime(2023, 6, 15, 12, 0, 0)
    obj_id = 1
    
    # Create records with microsecond differences
    dates_and_values = []
    for i, us in enumerate(microseconds):
        date = base_date + datetime.timedelta(microseconds=us)
        dates_and_values.append((date, i))
        insert_historical_record(obj_id, f"state_{i}", i, date, '~' if i > 0 else '+')
    
    # Find the actual latest
    dates_and_values.sort(key=lambda x: x[0])
    expected_latest_value = dates_and_values[-1][1]
    
    # Query what the database thinks is latest
    cursor.execute('''
        SELECT value, history_date FROM test_historical_model
        WHERE id = ?
        ORDER BY history_date DESC
        LIMIT 1
    ''', (obj_id,))
    
    result = cursor.fetchone()
    if result:
        actual_value = result[0]
        
        if actual_value != expected_latest_value:
            print(f"BUG: Microsecond precision issue detected!")
            print(f"  Expected latest value: {expected_latest_value}")
            print(f"  Actual latest value: {actual_value}")
            print(f"  This suggests datetime comparison loses precision")
            return False
    
    return True

# Test 3: Test as_of with boundary conditions
@given(
    st.integers(min_value=1, max_value=100),  # Object ID
    st.lists(
        st.integers(min_value=0, max_value=1000),  # Hours offset
        min_size=3,
        max_size=10,
        unique=True
    )
)
@hypo_settings(max_examples=50, deadline=None)
def test_as_of_boundary(obj_id, hour_offsets):
    """
    Test as_of() with dates that exactly match history_dates
    """
    clear_tables()
    
    base_date = datetime.datetime(2023, 1, 1, 0, 0, 0)
    hour_offsets = sorted(hour_offsets)
    
    # Insert records at specific times
    dates = []
    for i, hours in enumerate(hour_offsets):
        date = base_date + datetime.timedelta(hours=hours)
        dates.append(date)
        insert_historical_record(obj_id, f"state_{i}", i, date, '+' if i == 0 else '~')
    
    # Test as_of with exact dates
    for i, test_date in enumerate(dates):
        # Query what should be returned
        cursor.execute('''
            SELECT value FROM test_historical_model
            WHERE id = ? AND history_date <= ?
            ORDER BY history_date DESC
            LIMIT 1
        ''', (obj_id, test_date))
        
        result = cursor.fetchone()
        if result:
            expected_value = result[0]
            
            # The value should match the state at that exact time
            if expected_value != i:
                print(f"BUG: as_of boundary condition failed!")
                print(f"  as_of({test_date}) should return value={i}")
                print(f"  But would return value={expected_value}")
                
                # Debug: show surrounding records
                cursor.execute('''
                    SELECT value, history_date FROM test_historical_model
                    WHERE id = ?
                    ORDER BY history_date
                ''', (obj_id,))
                
                all_records = cursor.fetchall()
                print("  All records:")
                for rec in all_records:
                    print(f"    value={rec[0]}, date={rec[1]}")
                
                return False
    
    return True

# Test 4: Test bulk_history_create field handling
def test_bulk_history_create_field_corruption():
    """
    Test that bulk_history_create doesn't corrupt field values
    """
    from unittest.mock import Mock, MagicMock
    
    # Create mock objects with various field types
    test_cases = [
        {"name": "test", "value": 123, "flag": True},
        {"name": "test with spaces", "value": -456, "flag": False},
        {"name": "", "value": 0, "flag": None},  # Edge cases
        {"name": "unicode: 🎉", "value": 999999, "flag": True},
    ]
    
    mock_objs = []
    for i, fields in enumerate(test_cases):
        obj = Mock()
        obj.pk = i + 1
        obj._history_user = None
        obj._history_date = None
        for field, value in fields.items():
            setattr(obj, field, value)
        mock_objs.append(obj)
    
    # Create mock model
    mock_model = Mock()
    mock_model.get_default_history_user = Mock(return_value=None)
    
    # Create tracked fields
    tracked_fields = []
    for field_name in ["name", "value", "flag"]:
        field = Mock()
        field.attname = field_name
        tracked_fields.append(field)
    mock_model.tracked_fields = tracked_fields
    
    # Capture created instances
    created_instances = []
    def mock_init(self, **kwargs):
        self.__dict__.update(kwargs)
        created_instances.append(self)
        return None
    
    mock_model.side_effect = mock_init
    mock_model.objects.bulk_create = lambda objs, **kw: objs
    
    # Create manager and call bulk_history_create
    manager = HistoryManager(mock_model, None)
    
    from unittest.mock import patch
    with patch('django.conf.settings.SIMPLE_HISTORY_ENABLED', True):
        with patch('django.utils.timezone.now', return_value=datetime.datetime.now()):
            manager.bulk_history_create(mock_objs, update=False)
    
    # Check for field corruption
    for original, history in zip(mock_objs, created_instances):
        for field_name in ["name", "value", "flag"]:
            original_value = getattr(original, field_name)
            history_value = getattr(history, field_name, None)
            
            if original_value != history_value:
                print(f"BUG: Field corruption in bulk_history_create!")
                print(f"  Field: {field_name}")
                print(f"  Original value: {original_value!r}")
                print(f"  History value: {history_value!r}")
                return False
    
    return True

def run_all_tests():
    print("=" * 60)
    print("Property-Based Testing for simple_history.manager")
    print("=" * 60)
    print()
    
    tests = [
        ("Duplicate Timestamps", test_latest_of_each_duplicate_timestamps),
        ("Microsecond Precision", test_microsecond_precision),
        ("as_of Boundary Conditions", test_as_of_boundary),
        ("bulk_history_create Field Corruption", test_bulk_history_create_field_corruption),
    ]
    
    bugs_found = []
    
    for test_name, test_func in tests:
        print(f"Testing: {test_name}")
        print("-" * 40)
        
        try:
            if test_name == "bulk_history_create Field Corruption":
                # This is not a property test
                result = test_func()
                if result:
                    print(f"✓ {test_name} passed")
                else:
                    bugs_found.append(test_name)
                    print(f"✗ {test_name} revealed a bug!")
            else:
                # Run property test
                test_func()
                print(f"✓ {test_name} passed")
                
        except AssertionError as e:
            bugs_found.append(test_name)
            print(f"✗ {test_name} failed: {e}")
        except Exception as e:
            print(f"⚠ {test_name} error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if bugs_found:
        print(f"Found potential issues in {len(bugs_found)} test(s):")
        for bug in bugs_found:
            print(f"  - {bug}")
    else:
        print("All tests passed! No bugs found.")
    
    return len(bugs_found) == 0

if __name__ == "__main__":
    success = run_all_tests()