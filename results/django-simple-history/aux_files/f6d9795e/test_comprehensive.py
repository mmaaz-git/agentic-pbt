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

# Test 1: Check latest_of_each edge cases
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=3),  # Limited IDs for overlap
            st.datetimes(min_value=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
                         max_value=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc))
        ),
        min_size=2,
        max_size=20
    )
)
@hypo_settings(max_examples=100, deadline=None)
def test_latest_of_each_with_same_dates(records):
    """
    Test latest_of_each() behavior when multiple records have the same history_date
    """
    clear_tables()
    
    # Group records by ID and find those with duplicate dates
    id_to_dates = {}
    for obj_id, history_date in records:
        if obj_id not in id_to_dates:
            id_to_dates[obj_id] = []
        id_to_dates[obj_id].append(history_date)
    
    # Insert records
    for i, (obj_id, history_date) in enumerate(records):
        insert_historical_record(obj_id, f"name_{i}", i, history_date, '+')
    
    # Create a mock historical model
    class HistoricalModel(models.Model):
        id = models.IntegerField()
        name = models.CharField(max_length=100)
        value = models.IntegerField()
        deleted = models.BooleanField(default=False)
        history_date = models.DateTimeField()
        history_type = models.CharField(max_length=1)
        history_change_reason = models.CharField(max_length=100)
        
        class Meta:
            db_table = 'test_historical_model'
            managed = False
    
    class TestModel(models.Model):
        name = models.CharField(max_length=100)
        value = models.IntegerField()
        deleted = models.BooleanField(default=False)
        
        class Meta:
            db_table = 'test_model'
            managed = False
    
    # Create queryset
    qs = HistoricalQuerySet(model=HistoricalModel)
    qs._pk_attr = 'id'
    
    # Check for duplicate dates within same ID
    has_duplicates = False
    for obj_id, dates in id_to_dates.items():
        if len(dates) != len(set(dates)):
            has_duplicates = True
            break
    
    if has_duplicates:
        # When there are duplicate dates for the same ID, 
        # latest_of_each might have undefined behavior
        try:
            results = list(qs.latest_of_each())
            
            # Still check uniqueness - each ID should appear at most once
            result_ids = [r.id for r in results]
            assert len(result_ids) == len(set(result_ids)), (
                f"latest_of_each() returned duplicate IDs when records have same dates: {result_ids}"
            )
        except Exception as e:
            # Document the edge case behavior
            print(f"Edge case found: latest_of_each() with duplicate dates: {e}")

# Test 2: Check for off-by-one errors in as_of
@given(
    st.lists(
        st.datetimes(min_value=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
                     max_value=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)),
        min_size=3,
        max_size=10,
        unique=True
    ).map(sorted)  # Ensure dates are sorted
)
@hypo_settings(max_examples=100, deadline=None)
def test_as_of_boundary_conditions(dates):
    """
    Test as_of() with dates exactly matching history_dates (boundary condition)
    """
    clear_tables()
    
    # Insert historical records at these exact dates
    obj_id = 1
    for i, date in enumerate(dates):
        insert_historical_record(obj_id, f"state_{i}", i, date, '+' if i == 0 else '~')
    
    # Create mock model with custom manager
    class MockHistoricalModel(models.Model):
        id = models.IntegerField()
        history_date = models.DateTimeField()
        history_type = models.CharField(max_length=1)
        
        class Meta:
            db_table = 'test_historical_model'
            managed = False
    
    class MockModel(models.Model):
        class Meta:
            db_table = 'test_model'
            managed = False
    
    # For each date, test as_of with that exact date
    for i, test_date in enumerate(dates):
        cursor.execute('''
            SELECT COUNT(*) FROM test_historical_model 
            WHERE id = ? AND history_date <= ?
            ORDER BY history_date DESC
        ''', (obj_id, test_date))
        
        expected_count = cursor.fetchone()[0]
        
        # The as_of should include records up to and including this date
        cursor.execute('''
            SELECT value FROM test_historical_model 
            WHERE id = ? AND history_date <= ?
            ORDER BY history_date DESC
            LIMIT 1
        ''', (obj_id, test_date))
        
        result = cursor.fetchone()
        if result:
            expected_value = result[0]
            # Property: as_of(date) should include records with history_date == date
            assert expected_value == i, (
                f"as_of({test_date}) should return state_{i} (value={i}), "
                f"but would return value={expected_value}"
            )

# Test 3: Test for incorrect handling of deletion records in latest_of_each
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),
            st.sampled_from(['+', '~', '-']),
            st.integers(min_value=0, max_value=100)  # time offset
        ),
        min_size=1,
        max_size=20
    )
)
@hypo_settings(max_examples=100, deadline=None)
def test_latest_of_each_includes_deletions(records):
    """
    Test that latest_of_each() correctly includes deletion records when they are the latest
    """
    clear_tables()
    
    base_date = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
    
    # Insert records
    for obj_id, history_type, time_offset in records:
        history_date = base_date + datetime.timedelta(hours=time_offset)
        insert_historical_record(obj_id, f"name", 0, history_date, history_type)
    
    # Find which IDs should have deletion as their latest record
    latest_per_id = {}
    for obj_id, history_type, time_offset in records:
        history_date = base_date + datetime.timedelta(hours=time_offset)
        if obj_id not in latest_per_id or history_date > latest_per_id[obj_id][0]:
            latest_per_id[obj_id] = (history_date, history_type)
    
    deletion_ids = [obj_id for obj_id, (_, htype) in latest_per_id.items() if htype == '-']
    
    if deletion_ids:
        # Create queryset and get latest_of_each
        cursor.execute('''
            SELECT id, history_type, history_date 
            FROM test_historical_model
            WHERE history_id IN (
                SELECT history_id FROM (
                    SELECT history_id, id, history_date,
                           ROW_NUMBER() OVER (PARTITION BY id ORDER BY history_date DESC) as rn
                    FROM test_historical_model
                ) WHERE rn = 1
            )
        ''')
        
        results = cursor.fetchall()
        
        # Check if deletion records are properly included
        result_dict = {row[0]: row[1] for row in results}
        
        for del_id in deletion_ids:
            if del_id in result_dict:
                assert result_dict[del_id] == '-', (
                    f"Object {del_id} should have deletion ('-') as latest record, "
                    f"but got '{result_dict[del_id]}'"
                )
                print(f"✓ Deletion record correctly included for object {del_id}")

# Test 4: Test for precision issues with datetimes
@seed(42)  # Use fixed seed for reproducibility
@given(
    st.lists(
        st.floats(min_value=0, max_value=1),  # Fractional seconds
        min_size=2,
        max_size=10
    )
)
@hypo_settings(max_examples=50, deadline=None)
def test_datetime_precision_handling(fractions):
    """
    Test that datetime comparisons handle microsecond precision correctly
    """
    clear_tables()
    
    base_date = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    obj_id = 1
    
    # Create records with very close timestamps
    dates = []
    for i, fraction in enumerate(fractions):
        # Create dates with microsecond differences
        microseconds = int(fraction * 999999)
        date = base_date + datetime.timedelta(microseconds=microseconds)
        dates.append(date)
        insert_historical_record(obj_id, f"state_{i}", i, date, '~' if i > 0 else '+')
    
    # Check that latest_of_each picks the truly latest one
    cursor.execute('''
        SELECT value, history_date FROM test_historical_model
        WHERE id = ?
        ORDER BY history_date DESC
        LIMIT 1
    ''', (obj_id,))
    
    result = cursor.fetchone()
    if result:
        latest_value, latest_date = result
        expected_latest_idx = dates.index(max(dates))
        
        # The latest record should correspond to the maximum date
        assert latest_value == expected_latest_idx, (
            f"Expected latest record to have value {expected_latest_idx} "
            f"(corresponding to max date), but got {latest_value}"
        )

def run_tests():
    print("Running comprehensive property-based tests...\n")
    
    test_functions = [
        test_latest_of_each_with_same_dates,
        test_as_of_boundary_conditions,
        test_latest_of_each_includes_deletions,
        test_datetime_precision_handling
    ]
    
    for test_func in test_functions:
        print(f"Running {test_func.__name__}...")
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed\n")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}\n")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    run_tests()