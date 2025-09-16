import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import simple_history.utils as utils
from unittest.mock import Mock, MagicMock
from django.db.models import ForeignKey


# Test get_app_model_primary_key_name with mock models
@given(st.text().filter(lambda x: x and not x.isspace()))
def test_primary_key_name_without_foreignkey(pk_name):
    """
    Property: For non-ForeignKey primary keys, should return the exact name
    """
    mock_model = Mock()
    mock_pk = Mock()
    mock_pk.name = pk_name
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    # Make sure isinstance check returns False for ForeignKey
    mock_pk.__class__ = Mock
    
    result = utils.get_app_model_primary_key_name(mock_model)
    assert result == pk_name


@given(st.text().filter(lambda x: x and not x.isspace()))
def test_primary_key_name_with_foreignkey(pk_name):
    """
    Property: For ForeignKey primary keys, should append '_id' to the name
    """
    mock_model = Mock()
    
    # Create a mock that passes isinstance(obj, ForeignKey) check
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = pk_name
    
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result = utils.get_app_model_primary_key_name(mock_model)
    assert result == pk_name + "_id"


@given(st.text())
def test_primary_key_name_idempotence(pk_name):
    """
    Property: Calling the function multiple times should return the same result
    """
    mock_model = Mock()
    mock_pk = Mock()
    mock_pk.name = pk_name
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result1 = utils.get_app_model_primary_key_name(mock_model)
    result2 = utils.get_app_model_primary_key_name(mock_model)
    assert result1 == result2


def test_primary_key_name_with_empty_string():
    """
    Property: Empty string primary key name should be handled
    """
    mock_model = Mock()
    mock_pk = Mock()
    mock_pk.name = ""
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result = utils.get_app_model_primary_key_name(mock_model)
    assert result == ""


def test_primary_key_name_foreignkey_with_empty_string():
    """
    Property: ForeignKey with empty string name should still append '_id'
    """
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = ""
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result = utils.get_app_model_primary_key_name(mock_model)
    assert result == "_id"


@given(st.text(min_size=1).filter(lambda x: not x.endswith("_id")))
def test_foreignkey_always_adds_id_suffix(pk_name):
    """
    Property: ForeignKey should always add _id suffix, even if name has underscores
    """
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = pk_name
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result = utils.get_app_model_primary_key_name(mock_model)
    assert result == pk_name + "_id"
    assert result.endswith("_id")


def test_foreignkey_with_name_already_ending_in_id():
    """
    Property: ForeignKey should still add _id even if name already ends with _id
    """
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = "user_id"
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    result = utils.get_app_model_primary_key_name(mock_model)
    # This might create user_id_id which could be a bug!
    assert result == "user_id_id"


def test_foreignkey_with_special_characters():
    """
    Property: Special characters in pk name should be preserved
    """
    special_names = ["user-id", "user.id", "user id", "user@id", "user$id"]
    
    for pk_name in special_names:
        mock_model = Mock()
        mock_pk = Mock(spec=ForeignKey)
        mock_pk.name = pk_name
        mock_model._meta = Mock()
        mock_model._meta.pk = mock_pk
        
        result = utils.get_app_model_primary_key_name(mock_model)
        assert result == pk_name + "_id"


@given(st.text())
def test_primary_key_name_unicode_handling(pk_name):
    """
    Property: Unicode characters in pk name should be handled correctly
    """
    mock_model = Mock()
    mock_pk = Mock()
    mock_pk.name = pk_name
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    try:
        result = utils.get_app_model_primary_key_name(mock_model)
        assert isinstance(result, str)
        assert result == pk_name
    except Exception as e:
        # Should not raise any exception for valid strings
        assert False, f"Unexpected exception: {e}"


def test_primary_key_none_name():
    """
    Property: What happens if pk.name is None?
    """
    mock_model = Mock()
    mock_pk = Mock()
    mock_pk.name = None
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    try:
        result = utils.get_app_model_primary_key_name(mock_model)
        assert result == None
    except TypeError:
        # This might raise a TypeError when trying to concatenate None + "_id"
        pass


def test_foreignkey_with_none_name():
    """
    Property: ForeignKey with None name might cause TypeError
    """
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = None
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    try:
        result = utils.get_app_model_primary_key_name(mock_model)
        # This will likely fail with TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
        assert False, "Expected TypeError but got result: " + str(result)
    except TypeError as e:
        # This is expected behavior - None + "_id" raises TypeError
        assert "unsupported operand" in str(e) or "NoneType" in str(e)