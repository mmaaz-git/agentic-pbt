"""Property-based tests for SQLAlchemy ORM loader strategies and options."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session, declarative_base, relationship, selectinload, joinedload
import sqlalchemy.orm as orm


Base = declarative_base()


class Parent(Base):
    __tablename__ = 'parents'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    children = relationship("Child", back_populates="parent")


class Child(Base):
    __tablename__ = 'children'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    parent_id = Column(Integer, ForeignKey('parents.id'))
    parent = relationship("Parent", back_populates="children")


# Test: Load strategy option creation and composition
@given(st.sampled_from(['id', 'name', 'children', 'parent']))
@settings(max_examples=50)
def test_load_option_creation(attr_name):
    """Test that various load options can be created without errors."""
    
    # These should all create valid load options
    options = [
        orm.lazyload(attr_name),
        orm.immediateload(attr_name),
        orm.subqueryload(attr_name),
        orm.selectinload(attr_name),
        orm.joinedload(attr_name),
        orm.noload(attr_name),
        orm.raiseload(attr_name),
        orm.defaultload(attr_name),
        orm.defer(attr_name),
        orm.undefer(attr_name),
    ]
    
    # All should be Load objects
    for opt in options:
        assert isinstance(opt, orm.Load) or hasattr(opt, '_generate_cache_key')


# Test: Chained loader options
@given(
    st.lists(
        st.sampled_from(['lazyload', 'immediateload', 'selectinload', 'joinedload']),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=50)
def test_chained_loader_options(loaders):
    """Test chaining multiple loader options."""
    
    # Start with a base load
    load = orm.defaultload('parent')
    
    # Chain loaders
    for loader_name in loaders:
        loader_func = getattr(orm, loader_name)
        load = load.options(loader_func('children'))
    
    # Should still be a valid load option
    assert hasattr(load, '_generate_cache_key') or isinstance(load, orm.Load)


# Test: load_only with various attribute combinations
@given(
    st.sets(
        st.sampled_from(['id', 'name', 'parent_id']),
        min_size=1,
        max_size=3
    ),
    st.booleans()
)
@settings(max_examples=50)
def test_load_only_options(attrs, raiseload):
    """Test load_only with different attribute combinations."""
    
    attrs_list = list(attrs)
    load_opt = orm.load_only(*attrs_list, raiseload=raiseload)
    
    # Should create a valid load option
    assert hasattr(load_opt, '_generate_cache_key')


# Test: with_loader_criteria property
@given(
    st.text(min_size=1, max_size=50),
    st.booleans()
)
@settings(max_examples=50)
def test_with_loader_criteria(name_filter, include_aliases):
    """Test with_loader_criteria option creation."""
    
    # Create a criteria function
    def criteria(cls):
        return cls.name.like(f'%{name_filter}%')
    
    # Should create valid loader criteria
    loader_criteria = orm.with_loader_criteria(
        Parent,
        criteria,
        include_aliases=include_aliases
    )
    
    # Should have required attributes
    assert hasattr(loader_criteria, 'entity_namespace')
    assert hasattr(loader_criteria, 'where_criteria')
    assert loader_criteria.include_aliases == include_aliases


# Test: selectin_polymorphic with empty class list
def test_selectin_polymorphic_empty():
    """Test selectin_polymorphic with edge cases."""
    
    # Empty class list should still work
    result = orm.selectin_polymorphic(Parent, [])
    assert result is not None


# Test: contains_eager path construction
@given(
    st.lists(
        st.sampled_from(['parent', 'children', 'name', 'id']),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_contains_eager_paths(path_elements):
    """Test contains_eager with various attribute paths."""
    
    # Build path
    eager = orm.contains_eager(*path_elements)
    
    # Should create a valid option
    assert hasattr(eager, '_generate_cache_key')
    
    # Test chaining
    eager2 = eager.options(orm.defer('id'))
    assert hasattr(eager2, '_generate_cache_key')


# Test: aliased entity creation
@given(
    st.text(min_size=0, max_size=20),
    st.booleans(),
    st.booleans()
)
@settings(max_examples=50)
def test_aliased_entity(alias_name, flat, adapt_on_names):
    """Test aliased entity creation with various options."""
    
    # Create aliased entity
    if alias_name:
        alias = orm.aliased(
            Parent,
            name=alias_name if alias_name else None,
            flat=flat,
            adapt_on_names=adapt_on_names
        )
    else:
        alias = orm.aliased(Parent, flat=flat, adapt_on_names=adapt_on_names)
    
    # Should have entity namespace
    assert hasattr(alias, 'entity_namespace')
    
    # Should be usable in queries (smoke test)
    assert alias.id is not None
    assert alias.name is not None


# Test: Bundle creation with duplicate columns
@given(
    st.lists(
        st.sampled_from(['id', 'name', 'id', 'name']),  # Intentional duplicates
        min_size=1,
        max_size=10
    ),
    st.booleans()
)
@settings(max_examples=50)
def test_bundle_duplicate_columns(columns, single_entity):
    """Test Bundle with duplicate column names."""
    
    # Create bundle with potential duplicates
    col_refs = [getattr(Parent, col) for col in columns]
    bundle = orm.Bundle('test_bundle', *col_refs, single_entity=single_entity)
    
    # Should create successfully
    assert bundle.name == 'test_bundle'
    assert bundle.single_entity == single_entity
    
    # Should handle duplicates (implementation detail, just check it doesn't crash)
    assert len(bundle.columns) >= 1


# Test: with_expression property
@given(
    st.sampled_from(['id', 'name']),
    st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=50)
def test_with_expression(attr_name, const_value):
    """Test with_expression loader option."""
    
    from sqlalchemy import literal
    
    # Create with_expression option
    expr_opt = orm.with_expression(attr_name, literal(const_value))
    
    # Should create valid option
    assert hasattr(expr_opt, '_generate_cache_key')


# Test: polymorphic_union with empty table map
def test_polymorphic_union_empty():
    """Test polymorphic_union with edge cases."""
    
    # Empty table map - should handle gracefully
    with pytest.raises((ValueError, KeyError, TypeError)):
        orm.polymorphic_union({}, 'type')


# Test: undefer_group with various group names
@given(
    st.one_of(
        st.text(min_size=1, max_size=50),
        st.just(''),
        st.sampled_from(['*', 'default', '_private', '123'])
    )
)
@settings(max_examples=50)
def test_undefer_group_names(group_name):
    """Test undefer_group with various group names."""
    
    # Should create option for any string group name
    opt = orm.undefer_group(group_name)
    assert hasattr(opt, '_generate_cache_key')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])