import os
import threading
import concurrent.futures
from hypothesis import given, strategies as st, settings
import requests.certs


def test_where_idempotence():
    """The where() function should always return the same path."""
    first_call = requests.certs.where()
    for _ in range(100):
        assert requests.certs.where() == first_call


def test_where_returns_existing_file():
    """The returned path should always exist and be a file."""
    path = requests.certs.where()
    assert os.path.exists(path)
    assert os.path.isfile(path)


def test_where_returns_readable_file():
    """The returned file should be readable."""
    path = requests.certs.where()
    with open(path, 'rb') as f:
        content = f.read(1024)
        assert len(content) > 0


def test_where_returns_pem_file():
    """The returned file should be a valid PEM certificate."""
    path = requests.certs.where()
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert '-----BEGIN CERTIFICATE-----' in content
        assert '-----END CERTIFICATE-----' in content


@given(st.integers(min_value=1, max_value=50))
def test_where_thread_safety(num_threads):
    """The where() function should be thread-safe."""
    results = []
    
    def call_where():
        return requests.certs.where()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(call_where) for _ in range(num_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All threads should get the same path
    assert len(set(results)) == 1
    assert all(r == results[0] for r in results)


@given(st.integers(min_value=1, max_value=100))
def test_where_repeated_calls_no_crash(num_calls):
    """Calling where() many times should never crash."""
    for _ in range(num_calls):
        path = requests.certs.where()
        assert isinstance(path, str)
        assert len(path) > 0


def test_where_path_immutability():
    """The path returned should not change even if we modify global state."""
    import importlib
    
    path1 = requests.certs.where()
    
    # Try to reset the module's global state
    if hasattr(requests.certs, '_CACERT_PATH'):
        original = requests.certs._CACERT_PATH
        requests.certs._CACERT_PATH = None
        path2 = requests.certs.where()
        # Should reinitialize to the same path
        assert path1 == path2
        requests.certs._CACERT_PATH = original


def test_where_no_arguments():
    """The where() function takes no arguments."""
    import inspect
    sig = inspect.signature(requests.certs.where)
    assert len(sig.parameters) == 0


@given(st.data())
def test_where_concurrent_initialization(data):
    """Test concurrent first-time initialization."""
    import importlib
    import requests.certs
    
    # This test might not trigger the race condition reliably,
    # but it tests the general thread safety of initialization
    
    # Try to force re-initialization by reloading module
    try:
        importlib.reload(requests.certs)
    except:
        # If reload fails, skip this test instance
        return
    
    num_threads = data.draw(st.integers(min_value=2, max_value=10))
    results = []
    barrier = threading.Barrier(num_threads)
    
    def call_where_with_barrier():
        barrier.wait()  # Synchronize all threads to start at the same time
        return requests.certs.where()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(call_where_with_barrier) for _ in range(num_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All threads should get the same path even during concurrent initialization
    assert len(set(results)) == 1
    assert all(os.path.exists(r) for r in results)