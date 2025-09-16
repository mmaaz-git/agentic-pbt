import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.i18n import Translations

trans = Translations()
domain_trans = Translations(domain='testdomain')
trans.add(domain_trans)

try:
    result = trans.dugettext('testdomain', 'message')
    print(f"dugettext result: {result}")
except AttributeError as e:
    print(f"dugettext AttributeError: {e}")

try:
    result = trans.dungettext('testdomain', 'singular', 'plural', 1)
    print(f"dungettext result: {result}")
except AttributeError as e:
    print(f"dungettext AttributeError: {e}")