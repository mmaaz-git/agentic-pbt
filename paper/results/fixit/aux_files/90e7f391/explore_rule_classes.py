#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import importlib
import inspect
import fixit.rules

# List of rule modules
rule_modules = [
    'avoid_or_in_except', 'chained_instance_check', 'cls_in_classmethod',
    'compare_primitives_by_equal', 'compare_singleton_primitives_by_is',
    'deprecated_unittest_asserts', 'no_assert_true_for_comparison',
    'no_inherit_from_object', 'no_namedtuple', 'no_redundant_arguments_super',
    'no_redundant_fstring', 'no_redundant_lambda', 'no_redundant_list_comprehension',
    'no_static_if_condition', 'no_string_type_annotation', 'replace_union_with_optional',
    'rewrite_to_comprehension', 'rewrite_to_literal', 'sorted_attributes_rule',
    'use_assert_in', 'use_assert_is_not_none', 'use_async_sleep_in_async_def',
    'use_fstring', 'use_types_from_typing'
]

# Import and analyze each rule module
for rule_name in rule_modules[:5]:  # Start with first 5
    print(f"\n{'='*60}")
    print(f"Rule: {rule_name}")
    print('='*60)
    
    try:
        module = importlib.import_module(f'fixit.rules.{rule_name}')
        
        # Get all classes in the module
        classes = [(name, obj) for name, obj in inspect.getmembers(module, inspect.isclass)
                   if not name.startswith('_')]
        
        for class_name, cls in classes:
            print(f"\nClass: {class_name}")
            
            # Show the base classes
            bases = [b.__name__ for b in cls.__bases__]
            print(f"  Bases: {bases}")
            
            # Show docstring
            if cls.__doc__:
                doc_lines = cls.__doc__.strip().split('\n')
                print(f"  Doc: {doc_lines[0][:150]}")
            
            # Show methods
            methods = [(name, obj) for name, obj in inspect.getmembers(cls, inspect.ismethod)
                       if not name.startswith('_')]
            if methods:
                print(f"  Methods: {[m[0] for m in methods]}")
            
            # Show instance methods
            inst_methods = [(name, obj) for name, obj in inspect.getmembers(cls, inspect.isfunction)
                            if not name.startswith('_')]
            if inst_methods:
                print(f"  Instance methods: {[m[0] for m in inst_methods[:5]]}")
                
    except Exception as e:
        print(f"  Error importing: {e}")