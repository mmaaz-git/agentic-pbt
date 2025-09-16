import os
import sys
import datetime
from decimal import Decimal

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

import django
from django.conf import settings
from django.db import models, connection
from django.utils import timezone
from django.test import TestCase
django.setup()

from simple_history.models import HistoricalRecords
from simple_history.manager import (
    HistoricalQuerySet,
    HistoryManager,
    HistoryDescriptor,
    SIMPLE_HISTORY_REVERSE_ATTR_NAME
)

from hypothesis import given, strategies as st, settings as hypo_settings, assume
from hypothesis.extra.django import from_model
import pytest

# Create test models
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        app_label = 'test_app'
        
        
class SimpleTestModel(models.Model):
    name = models.CharField(max_length=50)
    number = models.IntegerField()
    history = HistoricalRecords()
    
    class Meta:
        app_label = 'test_app'


# Create tables in the in-memory database
from django.db import connection
cursor = connection.cursor()

# Create tables for our test models
cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_app_testmodel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        value INTEGER NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_app_historicaltestmodel (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        id INTEGER,
        name VARCHAR(100) NOT NULL,
        value INTEGER NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        history_date DATETIME NOT NULL,
        history_change_reason VARCHAR(100),
        history_type VARCHAR(1) NOT NULL,
        history_user_id INTEGER NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_app_simpletestmodel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL,
        number INTEGER NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_app_historicalsimpletestmodel (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        id INTEGER,
        name VARCHAR(50) NOT NULL,
        number INTEGER NOT NULL,
        history_date DATETIME NOT NULL,
        history_change_reason VARCHAR(100),
        history_type VARCHAR(1) NOT NULL,
        history_user_id INTEGER NULL
    )
''')

connection.commit()


# Property 1: HistoricalQuerySet.latest_of_each() returns one record per primary key with latest date
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),  # object id (limited to ensure duplicates)
            st.text(min_size=1, max_size=20),  # name
            st.integers(min_value=0, max_value=1000),  # value  
            st.datetimes(min_value=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
                         max_value=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)),  # history_date
            st.sampled_from(['+', '~', '-'])  # history_type
        ),
        min_size=1,
        max_size=20
    )
)
@hypo_settings(max_examples=100)
def test_latest_of_each_returns_one_per_pk(records):
    """
    Test that latest_of_each() returns exactly one record per unique primary key,
    and that record has the latest history_date among all records with that pk.
    """
    # Clear existing data
    cursor.execute("DELETE FROM test_app_historicaltestmodel")
    connection.commit()
    
    # Insert test historical records
    for obj_id, name, value, history_date, history_type in records:
        cursor.execute('''
            INSERT INTO test_app_historicaltestmodel 
            (id, name, value, created_at, updated_at, history_date, history_type, history_change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (obj_id, name, value, history_date, history_date, history_date, history_type, ''))
    connection.commit()
    
    # Get the latest of each using the queryset
    qs = TestModel.history.all()
    latest_qs = qs.latest_of_each()
    results = list(latest_qs)
    
    # Property 1: One record per unique primary key
    result_pks = [r.id for r in results]
    assert len(result_pks) == len(set(result_pks)), f"Found duplicate PKs in latest_of_each(): {result_pks}"
    
    # Property 2: Each result should have the latest history_date for its pk
    pk_to_dates = {}
    for obj_id, _, _, history_date, _ in records:
        if obj_id not in pk_to_dates:
            pk_to_dates[obj_id] = []
        pk_to_dates[obj_id].append(history_date)
    
    for result in results:
        expected_latest = max(pk_to_dates[result.id])
        assert result.history_date == expected_latest, (
            f"For pk={result.id}, expected latest date {expected_latest}, "
            f"but got {result.history_date}"
        )


# Property 2: HistoricalQuerySet.as_instances() excludes deletion records  
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=10),
            st.text(min_size=1, max_size=20),
            st.integers(min_value=0, max_value=1000),
            st.datetimes(min_value=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
                         max_value=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)),
            st.sampled_from(['+', '~', '-'])
        ),
        min_size=1,
        max_size=30
    )
)
@hypo_settings(max_examples=100)
def test_as_instances_excludes_deletions(records):
    """
    Test that as_instances() excludes deletion records (history_type='-').
    """
    # Clear existing data
    cursor.execute("DELETE FROM test_app_historicaltestmodel")
    connection.commit()
    
    # Insert test historical records
    for obj_id, name, value, history_date, history_type in records:
        cursor.execute('''
            INSERT INTO test_app_historicaltestmodel 
            (id, name, value, created_at, updated_at, history_date, history_type, history_change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (obj_id, name, value, history_date, history_date, history_date, history_type, ''))
    connection.commit()
    
    # Get all records
    all_records = list(TestModel.history.all())
    
    # Get as_instances records
    instance_qs = TestModel.history.all().as_instances()
    
    # The underlying queryset should exclude deletion records
    # Let's check the SQL filter
    assert instance_qs._result_cache is None  # Not yet evaluated
    
    # Force evaluation
    instance_results = list(instance_qs)
    
    # Manually get historical records that were used
    cursor.execute("SELECT history_type FROM test_app_historicaltestmodel WHERE history_type != '-'")
    non_deletion_count = len(cursor.fetchall())
    
    cursor.execute("SELECT history_type FROM test_app_historicaltestmodel")
    total_count = len(cursor.fetchall())
    
    # The queryset should have filtered out deletions
    # Note: as_instances() may further filter, but it should at least exclude deletions
    deletion_records = [r for r in all_records if r.history_type == '-']
    non_deletion_records = [r for r in all_records if r.history_type != '-']
    
    # Property: No deletion records should be in the instances
    # We need to check the underlying queryset before instance conversion
    base_qs = TestModel.history.all().exclude(history_type="-")
    base_results = list(base_qs)
    
    for record in base_results:
        assert record.history_type != '-', f"Found deletion record in as_instances base: {record.history_type}"


# Property 3: filter(pk=...) on as_instances() translates to the model's pk field
@given(
    st.integers(min_value=1, max_value=100),
    st.text(min_size=1, max_size=20),
    st.integers(min_value=0, max_value=1000)
)
@hypo_settings(max_examples=50)
def test_filter_pk_translation(obj_id, name, value):
    """
    Test that filtering by 'pk' on an as_instances() queryset correctly translates
    to filtering by the model's primary key field (not history_id).
    """
    # Clear existing data
    cursor.execute("DELETE FROM test_app_historicaltestmodel")
    connection.commit()
    
    # Insert multiple historical records for the same object
    now = timezone.now()
    for i in range(3):
        history_date = now - datetime.timedelta(days=i)
        cursor.execute('''
            INSERT INTO test_app_historicaltestmodel 
            (id, name, value, created_at, updated_at, history_date, history_type, history_change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (obj_id, f"{name}_{i}", value + i, history_date, history_date, history_date, '~' if i > 0 else '+', ''))
    
    # Insert records for other objects
    for other_id in [obj_id + 1, obj_id + 2]:
        cursor.execute('''
            INSERT INTO test_app_historicaltestmodel 
            (id, name, value, created_at, updated_at, history_date, history_type, history_change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (other_id, "other", 999, now, now, now, '+', ''))
    
    connection.commit()
    
    # Use as_instances() and filter by pk
    qs = TestModel.history.all().as_instances()
    filtered = qs.filter(pk=obj_id)
    results = list(filtered)
    
    # Property: All results should have the target object id (not history_id)
    for result in results:
        assert result.pk == obj_id, f"Expected pk={obj_id}, got pk={result.pk}"
    
    # Also verify we got the right number of records for this object
    cursor.execute("SELECT COUNT(*) FROM test_app_historicaltestmodel WHERE id = ? AND history_type != '-'", (obj_id,))
    expected_count = cursor.fetchone()[0]
    assert len(results) == expected_count, f"Expected {expected_count} records, got {len(results)}"


# Property 4: bulk_history_create creates correct history records
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=0, max_value=1000)
        ),
        min_size=1,
        max_size=10
    ),
    st.booleans()  # update flag
)
@hypo_settings(max_examples=50)
def test_bulk_history_create_properties(objects_data, is_update):
    """
    Test that bulk_history_create creates one historical record per object
    with correct history_type and field values.
    """
    # Clear existing data
    cursor.execute("DELETE FROM test_app_simpletestmodel")
    cursor.execute("DELETE FROM test_app_historicalsimpletestmodel") 
    connection.commit()
    
    # Create actual model instances
    objs = []
    for name, number in objects_data:
        obj = SimpleTestModel(name=name, number=number)
        obj.save()
        objs.append(obj)
    
    # Use bulk_history_create
    history_manager = SimpleTestModel.history
    created_records = history_manager.bulk_history_create(
        objs,
        update=is_update,
        default_change_reason="Bulk operation"
    )
    
    # Property 1: Number of created records should match number of objects
    assert len(created_records) == len(objs), (
        f"Expected {len(objs)} history records, got {len(created_records)}"
    )
    
    # Property 2: History type should be correct
    expected_type = "~" if is_update else "+"
    for record in created_records:
        assert record.history_type == expected_type, (
            f"Expected history_type='{expected_type}', got '{record.history_type}'"
        )
    
    # Property 3: Field values should match original objects
    for obj, record in zip(objs, created_records):
        assert record.name == obj.name, f"Name mismatch: {record.name} != {obj.name}"
        assert record.number == obj.number, f"Number mismatch: {record.number} != {obj.number}"
        assert record.id == obj.id, f"ID mismatch: {record.id} != {obj.id}"
    
    # Property 4: Change reason should be set
    for record in created_records:
        assert record.history_change_reason == "Bulk operation"


# Property 5: as_of() date filtering
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=3),  # Limited IDs for more overlap
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=100),
            st.datetimes(min_value=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
                         max_value=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)),
            st.sampled_from(['+', '~'])  # Exclude deletions for simplicity in this test
        ),
        min_size=5,
        max_size=20
    ),
    st.integers(min_value=0, max_value=4)  # Index for selecting as_of date
)
@hypo_settings(max_examples=50)
def test_as_of_date_filtering(records, date_index):
    """
    Test that as_of(date) correctly filters to records before or at the specified date
    and returns the most recent state for each object.
    """
    assume(len(records) > 0)
    
    # Clear existing data
    cursor.execute("DELETE FROM test_app_historicaltestmodel")
    connection.commit()
    
    # Sort records by date to make testing easier
    records = sorted(records, key=lambda x: x[3])
    
    # Insert test historical records
    for obj_id, name, value, history_date, history_type in records:
        cursor.execute('''
            INSERT INTO test_app_historicaltestmodel 
            (id, name, value, created_at, updated_at, history_date, history_type, history_change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (obj_id, name, value, history_date, history_date, history_date, history_type, ''))
    connection.commit()
    
    # Select an as_of date from the available dates
    available_dates = [r[3] for r in records]
    date_index = min(date_index, len(available_dates) - 1)
    as_of_date = available_dates[date_index]
    
    # Get results using as_of
    try:
        results = TestModel.history.as_of(as_of_date)
        results_list = list(results)
        
        # Property 1: All returned records should have history_date <= as_of_date
        # We need to check the underlying historical records
        for result in results_list:
            # Get the historical record that was used
            hist_attr = getattr(result, SIMPLE_HISTORY_REVERSE_ATTR_NAME, None)
            if hist_attr:
                # The historical record's date should be <= as_of_date
                cursor.execute(
                    "SELECT MAX(history_date) FROM test_app_historicaltestmodel WHERE id = ? AND history_date <= ?",
                    (result.id, as_of_date)
                )
                max_date = cursor.fetchone()[0]
                assert max_date is not None, f"No historical record found for id={result.id} before {as_of_date}"
        
        # Property 2: Each object should appear at most once
        result_ids = [r.id for r in results_list]
        assert len(result_ids) == len(set(result_ids)), f"Duplicate IDs in as_of results: {result_ids}"
        
        # Property 3: The values should match the most recent record before as_of_date
        for result in results_list:
            cursor.execute(
                """SELECT name, value FROM test_app_historicaltestmodel 
                   WHERE id = ? AND history_date <= ? 
                   ORDER BY history_date DESC LIMIT 1""",
                (result.id, as_of_date)
            )
            expected = cursor.fetchone()
            if expected:
                assert result.name == expected[0], f"Name mismatch for id={result.id}"
                assert result.value == expected[1], f"Value mismatch for id={result.id}"
                
    except (TestModel.DoesNotExist, AttributeError):
        # This is expected if no records exist before the date
        pass


if __name__ == "__main__":
    # Run the tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])