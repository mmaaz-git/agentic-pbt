import itertools
import math
from hypothesis import given, strategies as st, assume


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_chain_length(a, b):
    """Test that chain preserves total length"""
    chained = list(itertools.chain(a, b))
    assert len(chained) == len(a) + len(b)
    assert chained == a + b


@given(st.lists(st.integers()), st.integers(min_value=0))
def test_islice_basic(seq, n):
    """Test that islice(seq, n) equals seq[:n]"""
    assume(n <= len(seq) * 2)
    sliced = list(itertools.islice(seq, n))
    assert sliced == seq[:n]


@given(st.lists(st.integers(min_value=0, max_value=10), max_size=20), st.integers(min_value=0, max_value=10))
def test_combinations_count(elements, r):
    """Test combinations generates correct number of results"""
    n = len(elements)
    assume(r <= n)
    assume(n <= 20)  # Keep factorial computation reasonable
    combos = list(itertools.combinations(elements, r))
    expected = math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
    assert len(combos) == expected


@given(st.lists(st.integers()))
def test_accumulate_sum(seq):
    """Test accumulate gives running sums"""
    if not seq:
        assert list(itertools.accumulate(seq)) == []
    else:
        accumulated = list(itertools.accumulate(seq))
        for i in range(len(seq)):
            assert accumulated[i] == sum(seq[:i+1])


@given(st.lists(st.integers()), st.integers(min_value=1, max_value=100))
def test_batched_sizes(seq, n):
    """Test batched creates correct batch sizes"""
    batches = list(itertools.batched(seq, n))
    
    # All except possibly last should have size n
    for batch in batches[:-1] if batches else []:
        assert len(batch) == n
    
    # Last batch size check
    if batches and seq:
        assert 1 <= len(batches[-1]) <= n
    
    # Total elements preserved
    flattened = [item for batch in batches for item in batch]
    assert flattened == seq


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_product_length(a, b):
    """Test product generates len(a) * len(b) results"""
    assume(len(a) * len(b) <= 10000)
    prod = list(itertools.product(a, b))
    assert len(prod) == len(a) * len(b)


@given(st.lists(st.integers()), st.lists(st.booleans()))
def test_compress(data, selectors):
    """Test compress filters correctly"""
    compressed = list(itertools.compress(data, selectors))
    expected = [d for d, s in zip(data, selectors) if s]
    assert compressed == expected