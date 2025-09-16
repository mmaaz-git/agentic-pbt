# Bug Report: flask.blueprints Empty URL Rule Without Prefix

**Target**: `flask.blueprints.BlueprintSetupState.add_url_rule`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

BlueprintSetupState.add_url_rule fails to handle empty string rules when url_prefix is None, causing a ValueError when the empty rule is passed to the application's add_url_rule method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask import Flask, Blueprint
from flask.blueprints import BlueprintSetupState

url_prefixes = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/-_"),
        min_size=1,
        max_size=50
    ).map(lambda x: "/" + x.strip("/") if x.strip() else "/")
)

@given(
    url_prefix=url_prefixes,
    rule=st.one_of(st.just(""), st.just("/"), st.text())
)
def test_empty_rule_with_prefix_handling(url_prefix, rule):
    app = Flask(__name__)
    bp = Blueprint('test', __name__)
    
    state = BlueprintSetupState(bp, app, {"url_prefix": url_prefix}, True)
    state.add_url_rule(rule, endpoint="test", view_func=lambda: "test")
    
    rules = list(app.url_map.iter_rules())
    test_rules = [r for r in rules if 'test' in r.endpoint]
    assert len(test_rules) > 0
    
    rule_str = str(test_rules[0])
    assert rule_str.startswith("/") or rule_str == ""
```

**Failing input**: `url_prefix=None, rule=''`

## Reproducing the Bug

```python
from flask import Flask, Blueprint

app = Flask(__name__)
bp = Blueprint('test', __name__)

bp.add_url_rule("", endpoint="root", view_func=lambda: "root")
app.register_blueprint(bp)
```

## Why This Is A Bug

Flask's URL rules must always start with a forward slash. When a blueprint has no url_prefix and an empty string is used as the rule, BlueprintSetupState.add_url_rule passes the empty string directly to app.add_url_rule, violating this requirement. The code correctly handles the case when url_prefix exists (converting empty rule to the prefix itself), but fails to handle the case when both url_prefix is None and rule is empty.

## Fix

```diff
--- a/flask/sansio/blueprints.py
+++ b/flask/sansio/blueprints.py
@@ -96,11 +96,14 @@ class BlueprintSetupState:
         blueprint's name.
         """
         if self.url_prefix is not None:
             if rule:
                 rule = "/".join((self.url_prefix.rstrip("/"), rule.lstrip("/")))
             else:
                 rule = self.url_prefix
+        elif not rule:
+            # Handle empty rule with no prefix
+            rule = "/"
         options.setdefault("subdomain", self.subdomain)
         if endpoint is None:
             endpoint = _endpoint_from_view_func(view_func)  # type: ignore
```