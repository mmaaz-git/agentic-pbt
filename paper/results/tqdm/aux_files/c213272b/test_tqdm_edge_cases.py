"""
Edge case tests for tqdm.contrib functions with generators and special iterators
"""
import io
from hypothesis import given, strategies as st, settings
from tqdm.contrib import tenumerate, tmap, tzip, DummyTqdmFile


def test_tmap_generator_consumption():
    """tmap should work correctly with generators that can only be consumed once"""
    def gen():
        for i in range(5):
            yield i
    
    # tmap with generator
    result = list(tmap(lambda x: x * 2, gen()))
    assert result == [0, 2, 4, 6, 8]
    
    # Test with multiple generators
    def gen1():
        for i in range(3):
            yield i
    
    def gen2():
        for i in range(3):
            yield i * 10
    
    result = list(tmap(lambda x, y: x + y, gen1(), gen2()))
    assert result == [0, 11, 22]


def test_tzip_generator_consumption():
    """tzip should work correctly with generators"""
    def gen1():
        for i in range(3):
            yield i
    
    def gen2():
        for i in "abc":
            yield i
    
    result = list(tzip(gen1(), gen2()))
    assert result == [(0, 'a'), (1, 'b'), (2, 'c')]


def test_tenumerate_generator():
    """tenumerate should work with generators"""
    def gen():
        for i in range(3):
            yield i * 10
    
    result = list(tenumerate(gen(), start=5))
    expected = list(enumerate(gen(), start=5))
    assert result == expected


def test_tmap_exception_handling():
    """Test how tmap handles exceptions in the mapped function"""
    def failing_func(x):
        if x == 2:
            raise ValueError("Test error")
        return x * 2
    
    try:
        list(tmap(failing_func, [1, 2, 3]))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Test error"


def test_dummy_tqdm_file_bytes():
    """DummyTqdmFile should handle bytes correctly"""
    output = io.BytesIO()
    dummy = DummyTqdmFile(output)
    
    # Write bytes
    dummy.write(b"Hello")
    dummy.write(b"\n")
    dummy.write(b"World")
    del dummy
    
    assert output.getvalue() == b"Hello\nWorld"


def test_dummy_tqdm_file_mixed_newlines():
    """DummyTqdmFile should handle partial lines correctly"""
    output = io.StringIO()
    dummy = DummyTqdmFile(output)
    
    dummy.write("Line 1\nPart")
    dummy.write("ial line 2")
    dummy.write("\nLine 3")
    del dummy
    
    assert output.getvalue() == "Line 1\nPartial line 2\nLine 3"


def test_tzip_stops_at_shortest():
    """Verify tzip stops at the shortest iterable"""
    # This is important behavior to verify
    infinite_gen = (i for i in range(1000000))
    short_list = [1, 2, 3]
    
    result = list(tzip(infinite_gen, short_list))
    assert len(result) == 3
    assert result == [(0, 1), (1, 2), (2, 3)]
    
    # Test reverse order with fresh generator
    infinite_gen2 = (i for i in range(1000000))
    result = list(tzip(short_list, infinite_gen2))
    assert len(result) == 3
    assert result == [(1, 0), (2, 1), (3, 2)]


def test_tmap_lazy_evaluation():
    """Verify tmap is lazy (yields, doesn't eagerly evaluate)"""
    call_count = 0
    
    def counting_func(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    # Create tmap iterator but don't consume it
    mapper = tmap(counting_func, range(100))
    assert call_count == 0  # Should not have called function yet
    
    # Consume only first 3 items
    for i, result in enumerate(mapper):
        if i >= 3:
            break
    
    # Should have called function only 4 times (0, 1, 2, 3)
    assert call_count == 4