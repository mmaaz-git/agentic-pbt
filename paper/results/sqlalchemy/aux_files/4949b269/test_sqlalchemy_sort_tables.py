"""
Property-based tests for sqlalchemy.schema.sort_tables function
"""
import random
from typing import List, Set, Tuple
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey, String
from sqlalchemy.schema import sort_tables, sort_tables_and_constraints
import pytest


# Strategy to generate table names
table_names = st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10)


@st.composite
def tables_with_dependencies(draw):
    """Generate a set of tables with foreign key dependencies"""
    # Generate between 2 and 10 tables
    num_tables = draw(st.integers(min_value=2, max_value=10))
    
    # Generate unique table names
    names = draw(st.lists(
        table_names,
        min_size=num_tables,
        max_size=num_tables,
        unique=True
    ))
    
    metadata = MetaData()
    tables = []
    
    # Create tables
    for name in names:
        table = Table(name, metadata,
            Column('id', Integer, primary_key=True),
            Column('data', String(50))
        )
        tables.append(table)
    
    # Add some foreign key dependencies
    # We'll create a DAG by only allowing forward references
    num_deps = draw(st.integers(min_value=0, max_value=min(num_tables * 2, 15)))
    
    for _ in range(num_deps):
        # Pick two different tables
        idx1 = draw(st.integers(min_value=0, max_value=num_tables-1))
        idx2 = draw(st.integers(min_value=0, max_value=num_tables-1))
        
        if idx1 != idx2:
            # Add a foreign key from tables[idx1] to tables[idx2]
            # Check if this column already exists to avoid duplicates
            col_name = f'fk_to_{tables[idx2].name}'
            if col_name not in [c.name for c in tables[idx1].columns]:
                tables[idx1].append_column(
                    Column(col_name, Integer, ForeignKey(f'{tables[idx2].name}.id'))
                )
    
    return tables


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_preserves_all_tables(tables):
    """Property: sort_tables should return all input tables"""
    sorted_tables = sort_tables(tables)
    
    # Check that we have the same number of tables
    assert len(sorted_tables) == len(tables), \
        f"Expected {len(tables)} tables, got {len(sorted_tables)}"
    
    # Check that all tables are present (by name)
    input_names = {t.name for t in tables}
    output_names = {t.name for t in sorted_tables}
    
    assert input_names == output_names, \
        f"Tables missing or added. Input: {input_names}, Output: {output_names}"


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_respects_dependencies(tables):
    """Property: If table A depends on table B, B should come before A in sorted output"""
    sorted_tables = sort_tables(tables)
    
    # Create a position map
    position = {table.name: i for i, table in enumerate(sorted_tables)}
    
    # Check all foreign key constraints
    for table in sorted_tables:
        table_pos = position[table.name]
        
        for fk_constraint in table.foreign_key_constraints:
            # Get the referred table
            referred_table = fk_constraint.referred_table
            if referred_table is not None and referred_table != table:
                referred_pos = position.get(referred_table.name)
                
                if referred_pos is not None:
                    # The referred table should come before this table
                    assert referred_pos < table_pos, \
                        f"Table '{table.name}' (position {table_pos}) depends on " \
                        f"'{referred_table.name}' (position {referred_pos}), but comes after it"


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_idempotence(tables):
    """Property: Sorting already sorted tables should give the same result"""
    sorted_once = sort_tables(tables)
    sorted_twice = sort_tables(sorted_once)
    
    # Check that the order is the same
    names_once = [t.name for t in sorted_once]
    names_twice = [t.name for t in sorted_twice]
    
    assert names_once == names_twice, \
        f"Sorting is not idempotent. First: {names_once}, Second: {names_twice}"


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_deterministic(tables):
    """Property: sort_tables should be deterministic - same input gives same output"""
    # Sort the same list multiple times
    results = []
    for _ in range(5):
        # Create a new list with the same tables in random order
        shuffled = list(tables)
        random.shuffle(shuffled)
        sorted_tables = sort_tables(shuffled)
        results.append([t.name for t in sorted_tables])
    
    # All results should be the same
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, \
            f"Non-deterministic result. Run 0: {first_result}, Run {i}: {result}"


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_handles_empty_input(tables):
    """Property: sort_tables should handle edge cases like empty input"""
    # Test with empty list
    empty_result = sort_tables([])
    assert empty_result == [], "Empty input should return empty list"
    
    # Test with single table
    if tables:
        single_result = sort_tables([tables[0]])
        assert len(single_result) == 1, "Single table input should return single table"
        assert single_result[0] == tables[0], "Single table should be unchanged"


@st.composite 
def cyclic_tables(draw):
    """Generate tables with cyclic dependencies"""
    metadata = MetaData()
    
    # Create a simple cycle: A -> B -> C -> A
    num_tables = draw(st.integers(min_value=2, max_value=5))
    names = draw(st.lists(
        table_names,
        min_size=num_tables,
        max_size=num_tables,
        unique=True
    ))
    
    tables = []
    for name in names:
        table = Table(name, metadata,
            Column('id', Integer, primary_key=True)
        )
        tables.append(table)
    
    # Create a cycle
    for i in range(num_tables):
        next_i = (i + 1) % num_tables
        tables[i].append_column(
            Column(f'fk_to_{tables[next_i].name}', Integer, 
                   ForeignKey(f'{tables[next_i].name}.id'))
        )
    
    return tables


@given(cyclic_tables())
@settings(max_examples=50)
def test_sort_tables_handles_cycles(tables):
    """Property: sort_tables should handle cyclic dependencies without crashing"""
    try:
        # This should emit a warning but not crash
        sorted_tables = sort_tables(tables)
        
        # Even with cycles, all tables should be returned
        assert len(sorted_tables) == len(tables), \
            f"Expected {len(tables)} tables even with cycles, got {len(sorted_tables)}"
        
        input_names = {t.name for t in tables}
        output_names = {t.name for t in sorted_tables}
        assert input_names == output_names, \
            f"Tables missing with cycles. Input: {input_names}, Output: {output_names}"
            
    except Exception as e:
        pytest.fail(f"sort_tables crashed on cyclic dependencies: {e}")


@given(tables_with_dependencies())
@settings(max_examples=100)
def test_sort_tables_and_constraints_tuple_structure(tables):
    """Property: sort_tables_and_constraints should return proper tuple structure"""
    result = sort_tables_and_constraints(tables)
    
    # Check that result is a list of tuples
    assert isinstance(result, list), "Result should be a list"
    
    tables_seen = set()
    for item in result:
        assert isinstance(item, tuple), f"Each item should be a tuple, got {type(item)}"
        assert len(item) == 2, f"Each tuple should have 2 elements, got {len(item)}"
        
        table, constraints = item
        
        if table is not None:
            assert table in tables, f"Table {table.name} not in input tables"
            assert table not in tables_seen, f"Table {table.name} appears multiple times"
            tables_seen.add(table)
            
        assert isinstance(constraints, list), "Second element should be a list"
    
    # Check all input tables appear in output (except in case of cycles)
    # Some tables might be None entries for separated constraints
    non_none_tables = [t for t, _ in result if t is not None]
    assert len(non_none_tables) <= len(tables), "Should not have more tables than input"


if __name__ == "__main__":
    # Run a quick test
    print("Running property-based tests for sqlalchemy.schema.sort_tables...")
    
    # Quick smoke test
    metadata = MetaData()
    t1 = Table('parent', metadata, Column('id', Integer, primary_key=True))
    t2 = Table('child', metadata, 
               Column('id', Integer, primary_key=True),
               Column('parent_id', Integer, ForeignKey('parent.id')))
    
    result = sort_tables([t2, t1])
    assert [t.name for t in result] == ['parent', 'child']
    print("✓ Basic smoke test passed")
    
    print("\nRun 'pytest test_sqlalchemy_sort_tables.py -v' for full test suite")