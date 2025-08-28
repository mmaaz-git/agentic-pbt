import logging
import flask.logging


def test_debug_root_logger():
    """Debug test to check root logger state during pytest"""
    root = logging.getLogger()
    print(f"\nRoot logger state in pytest:")
    print(f"  Level: {root.level}")
    print(f"  Handlers: {root.handlers}")
    for h in root.handlers:
        print(f"    Handler: {h}, level: {h.level}")
    
    # Test the specific case
    logger = logging.getLogger('test_debug')
    logger.handlers.clear()
    
    handler = logging.StreamHandler()
    handler.setLevel(logging.ERROR)  # 40
    logger.addHandler(handler)
    
    effective = logger.getEffectiveLevel()
    result = flask.logging.has_level_handler(logger)
    
    print(f"\nTest logger:")
    print(f"  Effective level: {effective}")
    print(f"  Handler level: {handler.level}")
    print(f"  has_level_handler result: {result}")
    print(f"  Expected (handler.level <= effective): {handler.level <= effective}")
    
    assert result == (handler.level <= effective), f"Mismatch: result={result}, expected={handler.level <= effective}"