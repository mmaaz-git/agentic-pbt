#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.proto.Model_pb2 as Model
import coremltools.proto.NeuralNetwork_pb2 as NN
import coremltools.proto.FeatureTypes_pb2 as FT
import coremltools.proto.DataStructures_pb2 as DS

def explore_module(module, name):
    print(f"\n{'='*60}")
    print(f"Module: {name}")
    print(f"{'='*60}")
    
    # Get all classes in the module
    classes = [m for m in inspect.getmembers(module, inspect.isclass) 
               if not m[0].startswith('_')]
    
    print(f"Found {len(classes)} classes")
    
    # Show first 10 classes with their methods
    for class_name, class_obj in classes[:10]:
        print(f"\nClass: {class_name}")
        
        # Get public methods/attributes
        methods = []
        for member_name in dir(class_obj):
            if not member_name.startswith('_'):
                methods.append(member_name)
        
        if methods:
            print(f"  Public members: {', '.join(methods[:10])}")
            if len(methods) > 10:
                print(f"  ... and {len(methods)-10} more")

# Explore key modules
explore_module(Model, "Model_pb2")
explore_module(NN, "NeuralNetwork_pb2")
explore_module(FT, "FeatureTypes_pb2")
explore_module(DS, "DataStructures_pb2")