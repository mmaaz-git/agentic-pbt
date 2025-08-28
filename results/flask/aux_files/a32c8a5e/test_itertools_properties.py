import itertools
import math
from hypothesis import given, strategies as st, assume, settings


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_chain_length_property(a, b):
    """Test that chain preserves total length"""
    chained = list(itertools.chain(a, b))
    assert len(chained) == len(a) + len(b)
    assert chained == a + b


@given(st.lists(st.integers()), st.integers(min_value=0))
def test_islice_equals_list_slice(seq, n):
    """Test that islice(seq, n) equals seq[:n]"""
    assume(n <= len(seq) * 2)  # Reasonable bound
    sliced_iter = list(itertools.islice(seq, n))
    sliced_list = seq[:n]
    assert sliced_iter == sliced_list


@given(st.lists(st.integers()), st.integers(min_value=0), st.integers(min_value=0))
def test_islice_with_start_stop(seq, start, stop):
    """Test that islice(seq, start, stop) equals seq[start:stop]"""
    assume(start <= len(seq) * 2)
    assume(stop <= len(seq) * 2)
    assume(start <= stop)
    sliced_iter = list(itertools.islice(seq, start, stop))
    sliced_list = seq[start:stop]
    assert sliced_iter == sliced_list


@given(st.lists(st.integers(min_value=0, max_value=20)), st.integers(min_value=0, max_value=10))
def test_combinations_count(elements, r):
    """Test that combinations generates correct number of results"""
    n = len(elements)
    assume(r <= n)
    assume(n <= 20)  # Keep reasonable for factorial computation
    
    combos = list(itertools.combinations(elements, r))
    expected_count = math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
    assert len(combos) == expected_count
    
    # Combinations works on positions, not unique values
    # So we just check the count, not uniqueness of tuples


@given(st.lists(st.integers(min_value=0, max_value=20), min_size=0, max_size=8), 
       st.integers(min_value=0, max_value=8))
def test_permutations_count(elements, r):
    """Test that permutations generates correct number of results"""
    n = len(elements)
    assume(r <= n)
    
    perms = list(itertools.permutations(elements, r))
    expected_count = math.factorial(n) // math.factorial(n - r)
    assert len(perms) == expected_count


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_product_length(a, b):
    """Test that product generates len(a) * len(b) results"""
    assume(len(a) * len(b) <= 10000)  # Reasonable bound
    prod = list(itertools.product(a, b))
    assert len(prod) == len(a) * len(b)
    
    # Also test that each element is a pair from a and b
    for pair in prod:
        assert len(pair) == 2
        assert pair[0] in a
        assert pair[1] in b


@given(st.lists(st.integers(), min_size=1))
def test_accumulate_first_element(seq):
    """Test that accumulate preserves first element"""
    accumulated = list(itertools.accumulate(seq))
    assert len(accumulated) == len(seq)
    assert accumulated[0] == seq[0]


@given(st.lists(st.integers()))
def test_accumulate_sum_property(seq):
    """Test that accumulate gives running sums"""
    if not seq:
        accumulated = list(itertools.accumulate(seq))
        assert accumulated == []
    else:
        accumulated = list(itertools.accumulate(seq))
        assert len(accumulated) == len(seq)
        for i in range(len(seq)):
            assert accumulated[i] == sum(seq[:i+1])


@given(st.lists(st.integers(), min_size=0), st.integers(min_value=1, max_value=100))
def test_batched_batch_sizes(seq, n):
    """Test that batched creates correct batch sizes"""
    batches = list(itertools.batched(seq, n))
    
    # All batches except possibly the last should have size n
    for i, batch in enumerate(batches[:-1] if batches else []):
        assert len(batch) == n
    
    # Last batch should have size between 1 and n
    if batches and seq:
        assert 1 <= len(batches[-1]) <= n
    
    # Total elements should be preserved
    flattened = [item for batch in batches for item in batch]
    assert flattened == seq


@given(st.lists(st.integers()), st.lists(st.booleans()))
def test_compress_length_invariant(data, selectors):
    """Test that compress output length <= min(len(data), len(selectors))"""
    compressed = list(itertools.compress(data, selectors))
    assert len(compressed) <= len(data)
    assert len(compressed) <= len(selectors)
    
    # Also verify correctness
    expected = [d for d, s in zip(data, selectors) if s]
    assert compressed == expected


@given(st.lists(st.integers()))
def test_cycle_repeats_sequence(seq):
    """Test that cycle repeats the sequence correctly"""
    if not seq:
        cycled = list(itertools.islice(itertools.cycle(seq), 10))
        assert cycled == []
    else:
        # Take enough elements to see at least 2 full cycles
        n_elements = len(seq) * 3
        cycled = list(itertools.islice(itertools.cycle(seq), n_elements))
        
        for i in range(n_elements):
            assert cycled[i] == seq[i % len(seq)]


@given(st.lists(st.tuples(st.integers(), st.integers())))
def test_groupby_preserves_elements(seq):
    """Test that groupby preserves all elements"""
    grouped = itertools.groupby(seq, key=lambda x: x[0])
    unpacked = []
    for key, group in grouped:
        unpacked.extend(list(group))
    assert unpacked == seq


@given(st.lists(st.integers()), st.lists(st.integers()), st.lists(st.integers()))
def test_chain_multiple_iterables(a, b, c):
    """Test chain with multiple iterables"""
    chained = list(itertools.chain(a, b, c))
    assert chained == a + b + c
    assert len(chained) == len(a) + len(b) + len(c)


@given(st.lists(st.lists(st.integers())))
def test_chain_from_iterable(iterables):
    """Test chain.from_iterable"""
    chained = list(itertools.chain.from_iterable(iterables))
    expected = [item for sublist in iterables for item in sublist]
    assert chained == expected


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_zip_longest_length(a, b):
    """Test that zip_longest goes to the longest iterable"""
    zipped = list(itertools.zip_longest(a, b))
    expected_len = max(len(a), len(b))
    assert len(zipped) == expected_len
    
    # Check that shorter iterable is padded with None
    for i, (x, y) in enumerate(zipped):
        if i < len(a):
            assert x == a[i]
        else:
            assert x is None
        if i < len(b):
            assert y == b[i]
        else:
            assert y is None


@given(st.lists(st.integers()), st.lists(st.integers()), st.integers())
def test_zip_longest_with_fillvalue(a, b, fillvalue):
    """Test zip_longest with custom fillvalue"""
    zipped = list(itertools.zip_longest(a, b, fillvalue=fillvalue))
    expected_len = max(len(a), len(b))
    assert len(zipped) == expected_len
    
    for i, (x, y) in enumerate(zipped):
        if i < len(a):
            assert x == a[i]
        else:
            assert x == fillvalue
        if i < len(b):
            assert y == b[i]
        else:
            assert y == fillvalue


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=100))
def test_count_generates_sequence(start, step):
    """Test that count generates arithmetic sequence"""
    # Take first 10 elements
    counted = list(itertools.islice(itertools.count(start, step), 10))
    for i in range(10):
        assert counted[i] == start + i * step


@given(st.integers(min_value=0, max_value=1000), st.integers(min_value=0, max_value=100))
def test_repeat_count(obj, times):
    """Test that repeat generates exactly 'times' copies"""
    repeated = list(itertools.repeat(obj, times))
    assert len(repeated) == times
    assert all(x == obj for x in repeated)


@given(st.lists(st.integers()))
def test_pairwise_consecutive_pairs(seq):
    """Test that pairwise generates consecutive pairs"""
    pairs = list(itertools.pairwise(seq))
    
    if len(seq) < 2:
        assert pairs == []
    else:
        assert len(pairs) == len(seq) - 1
        for i, (a, b) in enumerate(pairs):
            assert a == seq[i]
            assert b == seq[i + 1]


@given(st.lists(st.integers(min_value=-10, max_value=10)), st.integers(min_value=-10, max_value=10))
def test_takewhile_dropwhile_partition(seq, threshold):
    """Test that takewhile and dropwhile partition the sequence"""
    # Use a simple deterministic predicate
    pred_func = lambda x: x < threshold
    
    taken = list(itertools.takewhile(pred_func, seq))
    dropped = list(itertools.dropwhile(pred_func, seq))
    
    # Verify taken consists of elements that satisfy predicate
    for item in taken:
        assert pred_func(item)
    
    # Verify that taken + dropped reconstructs the sequence
    reconstructed = taken + dropped
    assert reconstructed == seq


@given(st.lists(st.integers()), st.integers(min_value=2, max_value=10))
def test_tee_creates_independent_iterators(seq, n):
    """Test that tee creates n independent iterators"""
    iterators = itertools.tee(seq, n)
    assert len(iterators) == n
    
    # Each iterator should produce the same sequence
    results = [list(it) for it in iterators]
    for result in results:
        assert result == seq


@given(st.lists(st.integers(min_value=0, max_value=10), min_size=0, max_size=10),
       st.integers(min_value=0, max_value=15))
def test_combinations_with_replacement_count(elements, r):
    """Test combinations_with_replacement generates correct number"""
    n = len(elements)
    assume(r >= 0)
    assume(r <= 15)  # Keep reasonable
    assume(n > 0 or r == 0)
    
    combos = list(itertools.combinations_with_replacement(elements, r))
    
    if n == 0:
        expected_count = 0 if r > 0 else 1
    else:
        # Formula: (n+r-1)! / (r! * (n-1)!)
        expected_count = math.factorial(n + r - 1) // (math.factorial(r) * math.factorial(n - 1))
    
    assert len(combos) == expected_count