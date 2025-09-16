import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import io
import tempfile
from hypothesis import given, strategies as st, settings, assume
from pyramid.i18n import Translations, Localizer, make_localizer, negotiate_locale_name, default_locale_negotiator


@given(
    messages=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=20
    )
)
def test_translations_merge_preserves_catalog(messages):
    trans1 = Translations()
    trans1._catalog = messages.copy()
    
    trans2 = Translations()
    trans2._catalog = {'extra_key': 'extra_value'}
    
    original_messages = messages.copy()
    trans1.merge(trans2)
    
    for key, value in original_messages.items():
        assert key in trans1._catalog
        assert trans1._catalog[key] == value
    
    assert trans1._catalog['extra_key'] == 'extra_value'


@given(
    messages1=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=10
    ),
    messages2=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_translations_merge_overrides_correctly(messages1, messages2):
    trans1 = Translations()
    trans1._catalog = messages1.copy()
    
    trans2 = Translations()
    trans2._catalog = messages2.copy()
    
    trans1.merge(trans2)
    
    for key, value in messages2.items():
        assert trans1._catalog[key] == value


@given(
    domain=st.text(min_size=1, max_size=50).filter(lambda x: not x.isspace())
)
def test_translations_add_returns_self(domain):
    trans1 = Translations()
    trans2 = Translations(domain=domain)
    
    result = trans1.add(trans2)
    assert result is trans1


@given(
    domain=st.text(min_size=1, max_size=50).filter(lambda x: not x.isspace()),
    message=st.text(min_size=1, max_size=100)
)
def test_translations_dgettext_domain_handling(domain, message):
    trans = Translations()
    trans._catalog = {message: f"translated_{message}"}
    
    domain_trans = Translations(domain=domain)
    domain_trans._catalog = {message: f"domain_translated_{message}"}
    
    trans.add(domain_trans)
    
    default_result = trans.gettext(message)
    assert default_result == f"translated_{message}"
    
    domain_result = trans.dgettext(domain, message)
    assert domain_result == f"domain_translated_{message}"


@given(
    locale_name=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_-'), min_size=2, max_size=10)
)
def test_locale_fallback_generation(locale_name):
    assume('_' in locale_name)
    assume(locale_name.count('_') == 1)
    assume(not locale_name.startswith('_'))
    assume(not locale_name.endswith('_'))
    
    parts = locale_name.split('_')
    assume(len(parts[0]) > 0 and len(parts[1]) > 0)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        localizer = make_localizer(locale_name, [tmpdir])
        
        assert localizer.locale_name == locale_name
        assert localizer.translations is not None


@given(
    singular=st.text(min_size=1, max_size=50),
    plural=st.text(min_size=1, max_size=50),
    n=st.integers(min_value=0, max_value=1000),
    domain=st.text(min_size=1, max_size=30).filter(lambda x: not x.isspace())
)
def test_translations_dngettext_handles_domains(singular, plural, n, domain):
    trans = Translations()
    
    domain_trans = Translations(domain=domain)
    
    def custom_plural(n):
        return int(n != 1)
    domain_trans.plural = custom_plural
    
    trans.add(domain_trans)
    
    result = trans.dngettext(domain, singular, plural, n)
    assert isinstance(result, str)
    assert result in [singular, plural]


@given(
    messages=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=10
    ),
    domain1=st.text(min_size=1, max_size=30).filter(lambda x: not x.isspace()),
    domain2=st.text(min_size=1, max_size=30).filter(lambda x: not x.isspace())
)
def test_translations_add_multiple_domains(messages, domain1, domain2):
    assume(domain1 != domain2)
    assume(domain1 != 'messages')
    assume(domain2 != 'messages')
    
    base_trans = Translations()
    
    trans1 = Translations(domain=domain1)
    trans1._catalog = messages.copy()
    
    trans2 = Translations(domain=domain2)
    trans2._catalog = {'other': 'value'}
    
    base_trans.add(trans1)
    base_trans.add(trans2)
    
    assert domain1 in base_trans._domains
    assert domain2 in base_trans._domains
    assert base_trans._domains[domain1] is not base_trans._domains[domain2]


@given(
    locale_name=st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_-'), min_size=2, max_size=15)
)
def test_localizer_initialization(locale_name):
    trans = Translations()
    localizer = Localizer(locale_name, trans)
    
    assert localizer.locale_name == locale_name
    assert localizer.translations is trans
    assert localizer.translator is None
    assert localizer.pluralizer is None


@given(
    catalog1=st.dictionaries(
        st.text(min_size=1, max_size=30),
        st.text(min_size=1, max_size=50),
        min_size=0,
        max_size=10
    ),
    catalog2=st.dictionaries(
        st.text(min_size=1, max_size=30),
        st.text(min_size=1, max_size=50),
        min_size=0,
        max_size=10
    )
)
def test_translations_merge_chaining(catalog1, catalog2):
    trans1 = Translations()
    trans1._catalog = catalog1.copy()
    
    trans2 = Translations()
    trans2._catalog = catalog2.copy()
    
    trans3 = Translations()
    trans3._catalog = {'third': 'value'}
    
    result = trans1.merge(trans2).merge(trans3)
    
    assert result is trans1
    assert 'third' in trans1._catalog
    assert trans1._catalog['third'] == 'value'


class MockRequest:
    def __init__(self, attr_locale=None, param_locale=None, cookie_locale=None):
        if attr_locale is not None:
            self._LOCALE_ = attr_locale
        self.params = {'_LOCALE_': param_locale} if param_locale else {}
        self.cookies = {'_LOCALE_': cookie_locale} if cookie_locale else {}


@given(
    attr_locale=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    param_locale=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    cookie_locale=st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
def test_default_locale_negotiator_priority(attr_locale, param_locale, cookie_locale):
    request = MockRequest(attr_locale, param_locale, cookie_locale)
    result = default_locale_negotiator(request)
    
    if attr_locale is not None:
        assert result == attr_locale
    elif param_locale is not None:
        assert result == param_locale
    elif cookie_locale is not None:
        assert result == cookie_locale
    else:
        assert result is None


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])