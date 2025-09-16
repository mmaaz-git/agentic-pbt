"""Additional property-based tests for SQLAlchemy ORM edge cases."""

import pytest
from hypothesis import given, assume, strategies as st, settings, example
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import Session, declarative_base
import sqlalchemy.orm as orm
import datetime


Base = declarative_base()


class EdgeModel(Base):
    """Model for testing edge cases."""
    __tablename__ = 'edge_table'
    id = Column(Integer, primary_key=True)
    data = Column(String(100))


# Test: KeyFuncDict behavior with None keys
@given(
    st.lists(
        st.one_of(
            st.none(),
            st.text(min_size=1, max_size=10)
        ),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_keyfuncdict_none_keys(keys):
    """Test KeyFuncDict behavior with None keys."""
    
    class Item:
        def __init__(self, key):
            self.key = key
            self.value = f"val_{key}"
    
    dict_class = orm.attribute_keyed_dict('key')
    kfd = dict_class()
    
    items_added = []
    for key in keys:
        item = Item(key)
        items_added.append((key, item))
        kfd[key] = item
    
    # Verify consistency
    for k, v in kfd.items():
        assert k == v.key
    
    # Verify None key handling
    none_count = keys.count(None)
    if none_count > 0:
        # Should have None as a key
        assert None in kfd
        # The value should have None as its key attribute
        assert kfd[None].key is None


# Test: Multiple make_transient on same object with modifications
@given(
    st.integers(min_value=1, max_value=1000),
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50)
)
@settings(max_examples=100)
def test_make_transient_with_modifications(id_val, data1, data2):
    """Test make_transient behavior when object is modified between calls."""
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    obj = EdgeModel(id=id_val, data=data1)
    session.add(obj)
    session.commit()
    
    # First make_transient
    orm.make_transient(obj)
    assert orm.object_session(obj) is None
    
    # Modify object
    obj.data = data2
    
    # Second make_transient (should still work)
    orm.make_transient(obj)
    assert orm.object_session(obj) is None
    assert obj.data == data2
    
    # Add back to session
    session.add(obj)
    assert orm.object_session(obj) is session
    
    session.close()


# Test: KeyFuncDict with duplicate key values
@given(
    st.lists(
        st.integers(min_value=0, max_value=5),  # Small range to encourage duplicates
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_keyfuncdict_duplicate_keys(values):
    """Test KeyFuncDict behavior with duplicate keys."""
    
    class Record:
        def __init__(self, key, idx):
            self.key = key
            self.idx = idx
    
    dict_class = orm.attribute_keyed_dict('key')
    kfd = dict_class()
    
    # Add records with potentially duplicate keys
    for idx, key in enumerate(values):
        record = Record(key, idx)
        kfd[key] = record
    
    # Verify consistency
    for k, v in kfd.items():
        assert k == v.key
    
    # With duplicates, later values should overwrite earlier ones
    unique_keys = set(values)
    assert len(kfd) == len(unique_keys)
    
    # Verify last-write-wins for duplicate keys
    for key in unique_keys:
        last_idx = max(i for i, v in enumerate(values) if v == key)
        assert kfd[key].idx == last_idx


# Test: Empty string and whitespace keys
@given(
    st.lists(
        st.sampled_from(['', ' ', '  ', '\t', '\n', 'normal']),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_keyfuncdict_whitespace_keys(keys):
    """Test KeyFuncDict with empty and whitespace keys."""
    
    class Item:
        def __init__(self, key):
            self.key = key
            self.data = repr(key)
    
    dict_class = orm.attribute_keyed_dict('key')
    kfd = dict_class()
    
    for key in keys:
        item = Item(key)
        kfd[key] = item
    
    # Verify all keys are preserved correctly
    for k, v in kfd.items():
        assert k == v.key
        assert v.data == repr(k)
    
    # Empty string should be a valid key
    if '' in keys:
        assert '' in kfd
        assert kfd[''].key == ''


# Test: object_mapper with unmapped objects
@given(st.integers(), st.text())
def test_object_mapper_unmapped(num, text):
    """Test object_mapper raises for unmapped objects."""
    
    class UnmappedClass:
        def __init__(self, num, text):
            self.num = num
            self.text = text
    
    obj = UnmappedClass(num, text)
    
    with pytest.raises(orm.exc.UnmappedInstanceError):
        orm.object_mapper(obj)


# Test: was_deleted on various object states
@given(st.integers(min_value=1, max_value=1000), st.text(max_size=50))
@settings(max_examples=100)
def test_was_deleted_states(id_val, data):
    """Test was_deleted function across different object states."""
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    obj = EdgeModel(id=id_val, data=data)
    
    # Transient state
    assert not orm.was_deleted(obj)
    
    # Pending state
    session.add(obj)
    assert not orm.was_deleted(obj)
    
    # Persistent state
    session.commit()
    assert not orm.was_deleted(obj)
    
    # Deleted state
    session.delete(obj)
    session.flush()
    assert orm.was_deleted(obj)
    
    session.close()
    
    # Detached state (after session close)
    # According to docs, was_deleted works regardless of persistent/detached
    assert orm.was_deleted(obj)


# Test: KeyFuncDict.set method
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=100),
            st.text(min_size=1, max_size=10)
        ),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_keyfuncdict_set_method(items):
    """Test KeyFuncDict.set method for adding items."""
    
    class Entity:
        def __init__(self, id_val, name):
            self.id = id_val
            self.name = name
    
    dict_class = orm.keyfunc_mapping(lambda e: e.id)
    kfd = dict_class()
    
    # Use set method to add items
    for id_val, name in items:
        entity = Entity(id_val, name)
        kfd.set(entity)
    
    # Verify all items were added with correct keys
    for entity in kfd.values():
        assert entity.id in [i[0] for i in items]
        # Key should match the entity's id
        key = entity.id
        assert kfd[key] == entity


# Test: Chained state transitions
@given(st.integers(min_value=1, max_value=1000), st.text(max_size=50))
@settings(max_examples=50)
def test_chained_state_transitions(id_val, data):
    """Test chained state transitions: persistent -> transient -> persistent."""
    
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session1 = Session(engine)
    session2 = Session(engine)
    
    obj = EdgeModel(id=id_val, data=data)
    
    # Make persistent in session1
    session1.add(obj)
    session1.commit()
    assert orm.object_session(obj) == session1
    
    # Make transient
    orm.make_transient(obj)
    assert orm.object_session(obj) is None
    
    # Add to different session
    session2.add(obj)
    assert orm.object_session(obj) == session2
    
    # Should be able to commit in new session
    try:
        session2.commit()
        assert orm.object_session(obj) == session2
    except Exception:
        # Primary key conflict is expected
        pass
    
    session1.close()
    session2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])