import itertools
import math
from hypothesis import given, strategies as st, assume, settings, example
import operator


@given(st.lists(st.integers()), st.integers(min_value=0), st.integers(min_value=0), st.integers(min_value=1, max_value=10))
def test_islice_with_step(seq, start, stop, step):
    """Test islice with step parameter matches list slicing"""
    assume(start <= 100)
    assume(stop <= 100)
    assume(start <= stop)
    
    sliced_iter = list(itertools.islice(seq, start, stop, step))
    sliced_list = seq[start:stop:step]
    assert sliced_iter == sliced_list


@given(st.lists(st.integers()))
def test_groupby_without_key(seq):
    """Test groupby groups consecutive equal elements"""
    grouped = []
    for key, group in itertools.groupby(seq):
        grouped.append((key, list(group)))
    
    # Reconstruct and verify
    reconstructed = []
    for key, items in grouped:
        for item in items:
            assert item == key
            reconstructed.append(item)
    assert reconstructed == seq


@given(st.lists(st.integers(min_value=-100, max_value=100)))
def test_accumulate_with_operator(seq):
    """Test accumulate with different operators"""
    if not seq:
        assert list(itertools.accumulate(seq, operator.mul)) == []
    else:
        # Test multiplication
        mul_result = list(itertools.accumulate(seq, operator.mul))
        assert len(mul_result) == len(seq)
        assert mul_result[0] == seq[0]
        
        # Manually verify multiplication accumulation
        for i in range(1, len(seq)):
            expected = seq[0]
            for j in range(1, i + 1):
                expected *= seq[j]
            assert mul_result[i] == expected


@given(st.lists(st.integers(min_value=1, max_value=100)))
def test_accumulate_min_max(seq):
    """Test accumulate with min/max functions"""
    if seq:
        min_accum = list(itertools.accumulate(seq, min))
        max_accum = list(itertools.accumulate(seq, max))
        
        # Min should be non-increasing
        for i in range(1, len(min_accum)):
            assert min_accum[i] <= min_accum[i-1]
        
        # Max should be non-decreasing
        for i in range(1, len(max_accum)):
            assert max_accum[i] >= max_accum[i-1]
        
        # First element unchanged
        assert min_accum[0] == seq[0]
        assert max_accum[0] == seq[0]


@given(st.lists(st.integers()))
def test_starmap_vs_map(seq):
    """Test starmap with operator.add vs regular map"""
    pairs = [(x, x) for x in seq]
    
    starmap_result = list(itertools.starmap(operator.add, pairs))
    map_result = [x + x for x in seq]
    
    assert starmap_result == map_result


@given(st.lists(st.integers()))
def test_filterfalse_complement(seq):
    """Test that filterfalse is complement of filter"""
    pred = lambda x: x % 2 == 0
    
    filtered = list(filter(pred, seq))
    filterfalse_result = list(itertools.filterfalse(pred, seq))
    
    # Combined should equal original
    combined = []
    filter_iter = iter(filtered)
    false_iter = iter(filterfalse_result)
    
    for item in seq:
        if pred(item):
            assert next(filter_iter) == item
            combined.append(item)
        else:
            assert next(false_iter) == item
            combined.append(item)
    
    assert combined == seq
    assert len(filtered) + len(filterfalse_result) == len(seq)


@given(st.lists(st.integers(), min_size=1))
def test_cycle_consistency(seq):
    """Test cycle produces consistent repeating pattern"""
    # Take 5 full cycles
    n_cycles = 5
    n_elements = len(seq) * n_cycles
    cycled = list(itertools.islice(itertools.cycle(seq), n_elements))
    
    # Verify each cycle is identical
    for cycle_num in range(n_cycles):
        start = cycle_num * len(seq)
        end = start + len(seq)
        assert cycled[start:end] == seq


@given(st.lists(st.integers()), st.integers(min_value=1, max_value=10))
def test_tee_exhaustion_independence(seq, n):
    """Test that exhausting one tee'd iterator doesn't affect others"""
    iterators = list(itertools.tee(seq, n))
    
    # Exhaust first iterator
    first_result = list(iterators[0])
    assert first_result == seq
    
    # Others should still work
    for it in iterators[1:]:
        assert list(it) == seq


@given(st.lists(st.integers(min_value=0, max_value=10), min_size=0, max_size=6))
def test_permutations_ordering(elements):
    """Test that permutations are generated in a consistent order"""
    # Note: With duplicate elements, permutations may not be in strict lexicographic order
    # because permutations works on positions, not values
    perms1 = list(itertools.permutations(elements))
    perms2 = list(itertools.permutations(elements))
    
    # Should generate same sequence every time
    assert perms1 == perms2


@given(st.lists(st.integers(min_value=0, max_value=10), min_size=0, max_size=6))
def test_combinations_ordering(elements):
    """Test that combinations are generated in a consistent order"""
    # Note: With duplicate elements, combinations may not be in strict lexicographic order
    # because combinations works on positions, not values
    for r in range(len(elements) + 1):
        combos1 = list(itertools.combinations(elements, r))
        combos2 = list(itertools.combinations(elements, r))
        
        # Should generate same sequence every time
        assert combos1 == combos2


@given(st.lists(st.integers()))
def test_chain_single_iterable(seq):
    """Test chain with single iterable"""
    chained = list(itertools.chain(seq))
    assert chained == seq


@given(st.integers(min_value=0, max_value=100))
def test_repeat_infinite(obj):
    """Test repeat without times generates infinite sequence"""
    # Take first 100 elements from infinite repeat
    repeated = list(itertools.islice(itertools.repeat(obj), 100))
    assert len(repeated) == 100
    assert all(x == obj for x in repeated)


@given(st.lists(st.lists(st.integers())))
def test_product_multiple_iterables(iterables):
    """Test product with multiple iterables"""
    if not iterables or any(len(it) == 0 for it in iterables):
        result = list(itertools.product(*iterables))
        # Should be empty if any iterable is empty
        if any(len(it) == 0 for it in iterables):
            assert result == []
    else:
        assume(all(len(it) <= 5 for it in iterables))  # Keep size reasonable
        assume(len(iterables) <= 4)  # Keep dimensions reasonable
        
        result = list(itertools.product(*iterables))
        
        # Check length
        expected_len = 1
        for it in iterables:
            expected_len *= len(it)
        assert len(result) == expected_len
        
        # Check each tuple has correct length
        for tup in result:
            assert len(tup) == len(iterables)


@given(st.lists(st.integers(), min_size=1), st.integers(min_value=-100, max_value=100))
def test_accumulate_with_initial(seq, initial):
    """Test accumulate with initial value"""
    accumulated = list(itertools.accumulate(seq, initial=initial))
    
    # Should have one more element than input
    assert len(accumulated) == len(seq) + 1
    
    # First element should be initial
    assert accumulated[0] == initial
    
    # Verify accumulation
    for i in range(len(seq)):
        expected_sum = initial + sum(seq[:i+1])
        assert accumulated[i+1] == expected_sum


@given(st.lists(st.tuples(st.integers(min_value=0, max_value=10), st.integers())))
def test_groupby_with_key_function(pairs):
    """Test groupby with explicit key function"""
    # Group by first element of tuple
    grouped = itertools.groupby(pairs, key=lambda x: x[0])
    
    # Reconstruct to verify
    reconstructed = []
    for key, group in grouped:
        group_list = list(group)
        for item in group_list:
            assert item[0] == key  # Key function result should match
            reconstructed.append(item)
    
    assert reconstructed == pairs


@given(st.lists(st.integers()), st.integers(min_value=0, max_value=10))
def test_repeat_with_itertools_chain(seq, n):
    """Test repeat combined with chain"""
    # Repeat the sequence n times using chain and repeat
    repeated_seq = list(itertools.chain.from_iterable(itertools.repeat(seq, n)))
    
    # Should be equivalent to seq * n
    assert repeated_seq == seq * n


@given(st.lists(st.integers(), min_size=1, max_size=10), st.integers(min_value=1, max_value=5))
def test_product_repeat_parameter(seq, repeat):
    """Test product with repeat parameter"""
    assume(len(seq) ** repeat <= 10000)  # Keep size reasonable
    
    # product(seq, repeat=n) should equal product(seq, seq, ..., seq) n times
    result_repeat = list(itertools.product(seq, repeat=repeat))
    result_explicit = list(itertools.product(*[seq] * repeat))
    
    assert result_repeat == result_explicit
    assert len(result_repeat) == len(seq) ** repeat


@given(st.lists(st.integers(min_value=-10, max_value=10)))
def test_compress_empty_selectors(data):
    """Test compress with empty selectors"""
    compressed = list(itertools.compress(data, []))
    assert compressed == []


@given(st.lists(st.booleans()))
def test_compress_empty_data(selectors):
    """Test compress with empty data"""
    compressed = list(itertools.compress([], selectors))
    assert compressed == []


@given(st.lists(st.integers()))
def test_batched_single_element_batches(seq):
    """Test batched with batch size 1"""
    if seq:
        batches = list(itertools.batched(seq, 1))
        assert len(batches) == len(seq)
        for i, batch in enumerate(batches):
            assert batch == (seq[i],)


@given(st.lists(st.integers(), min_size=1))
def test_batched_full_size_batch(seq):
    """Test batched with batch size equal to sequence length"""
    batches = list(itertools.batched(seq, len(seq)))
    assert len(batches) == 1
    assert batches[0] == tuple(seq)


@given(st.lists(st.integers(), min_size=1))
def test_batched_oversized_batch(seq):
    """Test batched with batch size larger than sequence"""
    batches = list(itertools.batched(seq, len(seq) + 10))
    assert len(batches) == 1
    assert batches[0] == tuple(seq)