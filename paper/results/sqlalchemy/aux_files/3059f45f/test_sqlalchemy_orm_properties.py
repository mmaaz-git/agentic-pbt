"""Property-based tests for SQLAlchemy ORM using Hypothesis."""

import pytest
from hypothesis import given, assume, strategies as st, settings
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import sqlalchemy.orm as orm
import random
import string


# Create base for test models
Base = declarative_base()


class TestModel(Base):
    """Simple test model for property testing."""
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(Integer)
    flag = Column(Boolean)
    

class AnotherModel(Base):
    """Another test model to test with multiple classes."""
    __tablename__ = 'another_table'
    id = Column(Integer, primary_key=True)
    data = Column(Text)
    score = Column(Float)


# Strategy for creating test model instances
@st.composite
def model_instances(draw):
    """Generate TestModel instances with random data."""
    return TestModel(
        id=draw(st.integers(min_value=1, max_value=100000)),
        name=draw(st.text(min_size=1, max_size=50)),
        value=draw(st.integers(min_value=-2147483648, max_value=2147483647)),
        flag=draw(st.booleans())
    )


@st.composite  
def another_model_instances(draw):
    """Generate AnotherModel instances with random data."""
    return AnotherModel(
        id=draw(st.integers(min_value=1, max_value=1000000)),
        data=draw(st.text(max_size=1000)),
        score=draw(st.floats(allow_nan=False, allow_infinity=False))
    )


# Test 1: make_transient should be idempotent
@given(model_instances())
@settings(max_examples=100)
def test_make_transient_idempotent(obj):
    """Property: Applying make_transient twice should have same effect as once."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Add object to session to make it persistent
    session.add(obj)
    session.commit()
    
    # Apply make_transient once
    orm.make_transient(obj)
    state_after_once = (
        orm.object_session(obj),
        obj in session,
        hasattr(obj, '_sa_instance_state')
    )
    
    # Apply make_transient again (should be idempotent)
    orm.make_transient(obj)
    state_after_twice = (
        orm.object_session(obj),
        obj in session,
        hasattr(obj, '_sa_instance_state')
    )
    
    session.close()
    
    # States should be identical
    assert state_after_once == state_after_twice
    assert orm.object_session(obj) is None


# Test 2: object_session should return None for transient objects
@given(model_instances())
@settings(max_examples=100)
def test_object_session_transient(obj):
    """Property: object_session returns None for transient (non-session) objects."""
    # Fresh object not added to any session
    assert orm.object_session(obj) is None
    
    # After make_transient
    orm.make_transient(obj)
    assert orm.object_session(obj) is None


# Test 3: KeyFuncDict maintains key-value consistency
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10),  # attribute value
            st.integers()  # object id
        ),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_keyfuncdict_consistency(items):
    """Property: KeyFuncDict keys should always match keyfunc(value)."""
    
    # Create simple objects with an attribute
    class Item:
        def __init__(self, key, value):
            self.key = key
            self.value = value
    
    # Create a KeyFuncDict that keys by the 'key' attribute
    dict_class = orm.attribute_keyed_dict('key')
    kfd = dict_class()
    
    # Add items
    for key, value in items:
        item = Item(key, value)
        kfd[key] = item
    
    # Verify consistency: all keys should match their value's key attribute
    for k, v in kfd.items():
        assert k == v.key
        
    # Verify we can retrieve items by their key
    for key, value in items:
        if key in kfd:
            assert kfd[key].key == key


# Test 4: class_mapper determinism
@given(st.sampled_from([TestModel, AnotherModel]))
@settings(max_examples=50)
def test_class_mapper_deterministic(model_class):
    """Property: class_mapper should always return the same mapper for a class."""
    mapper1 = orm.class_mapper(model_class)
    mapper2 = orm.class_mapper(model_class)
    
    # Same mapper object
    assert mapper1 is mapper2
    
    # Same class
    assert mapper1.class_ == mapper2.class_ == model_class


# Test 5: Round-trip property for session add/remove
@given(model_instances())
@settings(max_examples=100)
def test_session_add_remove_roundtrip(obj):
    """Property: Adding then expunging an object should leave it transient."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Initial state
    initial_in_session = obj in session
    initial_has_session = orm.object_session(obj) is not None
    
    # Add to session
    session.add(obj)
    assert obj in session
    
    # Remove from session (expunge)
    session.expunge(obj)
    
    # Should return to transient state
    assert obj not in session
    assert orm.object_session(obj) is None
    assert initial_in_session == (obj in session)
    assert initial_has_session == (orm.object_session(obj) is not None)
    
    session.close()


# Test 6: make_transient_to_detached requires transient object
@given(model_instances())
@settings(max_examples=100)
def test_make_transient_to_detached_state_requirement(obj):
    """Property: make_transient_to_detached should work on transient objects."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Object starts transient
    assert orm.object_session(obj) is None
    
    # Should work on transient object
    try:
        orm.make_transient_to_detached(obj)
        # After this, object should still not have a session
        assert orm.object_session(obj) is None
    except Exception as e:
        # If it fails, it might be because object needs primary key
        # This is expected for some cases
        pass
    
    session.close()


# Test 7: KeyFuncDict with keyfunc mapping
@given(
    st.lists(
        st.integers(min_value=0, max_value=1000),
        min_size=0,
        max_size=20,
        unique=True
    )
)
@settings(max_examples=100)
def test_keyfunc_mapping_consistency(ids):
    """Property: keyfunc_mapping should maintain key consistency with keyfunc values."""
    
    # Create objects with id attribute
    class Entity:
        def __init__(self, id_val):
            self.id = id_val
            self.data = f"data_{id_val}"
    
    # Create keyfunc-mapped dictionary
    dict_class = orm.keyfunc_mapping(lambda e: e.id)
    kmd = dict_class()
    
    # Add entities
    entities = []
    for id_val in ids:
        entity = Entity(id_val)
        entities.append(entity)
        kmd[id_val] = entity
    
    # Verify all keys match their entity's id
    for key, entity in kmd.items():
        assert key == entity.id
    
    # Verify retrieval
    for id_val in ids:
        assert kmd[id_val].id == id_val
        assert kmd[id_val].data == f"data_{id_val}"
    
    # Verify size
    assert len(kmd) == len(ids)


# Test 8: Mapped collection with custom keyfunc
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=100),
            st.text(min_size=1, max_size=20)
        ),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100)
def test_mapped_collection_keyfunc(items):
    """Property: mapped_collection should correctly apply keyfunc."""
    
    class Record:
        def __init__(self, num, text):
            self.number = num
            self.text = text
    
    # Create mapped collection with custom keyfunc
    def custom_key(record):
        return f"{record.number}_{record.text[:3] if len(record.text) >= 3 else record.text}"
    
    dict_class = orm.mapped_collection(custom_key)
    mc = dict_class()
    
    # Add records
    records = []
    for num, text in items:
        record = Record(num, text)
        records.append(record)
        key = custom_key(record)
        mc[key] = record
    
    # Verify keys match keyfunc
    for key, record in mc.items():
        expected_key = custom_key(record)
        assert key == expected_key
    
    # Verify all records are accessible
    for record in records:
        key = custom_key(record)
        if key in mc:  # May have duplicates
            stored = mc[key]
            assert custom_key(stored) == key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])