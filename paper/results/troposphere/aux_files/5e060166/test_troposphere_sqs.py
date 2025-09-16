import string
from hypothesis import given, strategies as st, assume, settings
import troposphere.sqs as sqs
from troposphere.validators import boolean, integer


# Test 1: FIFO Queue naming validation
@given(
    queue_name=st.text(min_size=1, max_size=100, alphabet=string.ascii_letters + string.digits + "-_."),
    is_fifo=st.booleans()
)
def test_fifo_queue_naming_validation(queue_name, is_fifo):
    """
    Property: When FifoQueue=True, QueueName must end with '.fifo' per validate_queue function
    """
    queue = sqs.Queue(title="TestQueue", FifoQueue=is_fifo, QueueName=queue_name)
    
    if is_fifo:
        if queue_name.endswith(".fifo"):
            # Should validate successfully
            queue.validate()
        else:
            # Should raise ValueError
            try:
                queue.validate()
                assert False, f"Expected ValueError for FIFO queue name '{queue_name}' not ending with .fifo"
            except ValueError as e:
                assert "FIFO queues need to provide a" in str(e)
                assert "QueueName that ends with '.fifo'" in str(e)
    else:
        # Non-FIFO queues should validate regardless of name
        queue.validate()


# Test 2: Boolean validator accepts specific values
@given(value=st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1),
    st.integers(),
    st.floats()
))
def test_boolean_validator(value):
    """
    Property: boolean() validator should only accept specific true/false values
    """
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert boolean(value) is True
    elif value in false_values:
        assert boolean(value) is False
    else:
        try:
            boolean(value)
            assert False, f"Expected ValueError for non-boolean value {value!r}"
        except ValueError:
            pass


# Test 3: Integer validator property
@given(value=st.one_of(
    st.integers(),
    st.text(alphabet=string.digits, min_size=1, max_size=10),
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.floats()
))
def test_integer_validator(value):
    """
    Property: integer() validator should accept only int-convertible values
    """
    try:
        result = integer(value)
        # Should be able to convert to int
        int(result)
        # Original conversion should also work
        int(value)
    except (ValueError, TypeError):
        # If integer() doesn't raise, int() should have
        try:
            integer(value)
            # If we get here, integer() didn't raise but int() would
            int(value)
            assert False, f"integer() accepted {value!r} but shouldn't have"
        except ValueError:
            pass


# Test 4: Queue property type validation
@given(
    delay_seconds=st.one_of(
        st.integers(min_value=0, max_value=900),
        st.text(alphabet=string.digits, min_size=1, max_size=3),
        st.text(alphabet=string.ascii_letters, min_size=1),
        st.floats()
    )
)
def test_queue_delay_seconds_validation(delay_seconds):
    """
    Property: DelaySeconds should only accept integer-convertible values (0-900 seconds per AWS docs)
    """
    try:
        queue = sqs.Queue(title="TestQueue", DelaySeconds=delay_seconds)
        # If it accepted the value, it should be int-convertible
        int(delay_seconds)
        # And should be in valid range for AWS (0-900 seconds)
        assert 0 <= int(delay_seconds) <= 10000000  # using large upper bound to find validation gaps
    except (ValueError, TypeError):
        # Expected for non-integer values
        pass


# Test 5: RedrivePolicy maxReceiveCount validation
@given(
    max_receive_count=st.one_of(
        st.integers(min_value=1, max_value=1000),
        st.text(alphabet=string.digits, min_size=1, max_size=4),
        st.text(alphabet=string.ascii_letters, min_size=1),
        st.floats(),
        st.none()
    )
)
def test_redrive_policy_max_receive_count(max_receive_count):
    """
    Property: RedrivePolicy.maxReceiveCount should only accept integer values
    """
    try:
        policy = sqs.RedrivePolicy(maxReceiveCount=max_receive_count)
        # If it accepted the value, should be int-convertible
        if max_receive_count is not None:
            int(max_receive_count)
    except (ValueError, TypeError):
        # Expected for non-integer values
        pass


# Test 6: Queue ContentBasedDeduplication requires FifoQueue
@given(
    content_dedup=st.booleans(),
    is_fifo=st.booleans()
)
@settings(max_examples=100)
def test_content_based_deduplication_requires_fifo(content_dedup, is_fifo):
    """
    Property: ContentBasedDeduplication should only be allowed when FifoQueue=True
    This is an AWS requirement that troposphere might validate
    """
    if is_fifo:
        queue_name = "test.fifo"
    else:
        queue_name = "test-queue"
    
    queue = sqs.Queue(
        title="TestQueue",
        QueueName=queue_name,
        FifoQueue=is_fifo,
        ContentBasedDeduplication=content_dedup
    )
    
    # Troposphere may or may not validate this AWS constraint
    # Let's see what happens
    try:
        queue.validate()
        # If validation passes, record the behavior
        pass
    except Exception:
        # If it fails, that's also valid behavior to record
        pass


# Test 7: Queue to_dict preserves properties
@given(
    delay_seconds=st.integers(min_value=0, max_value=900),
    max_message_size=st.integers(min_value=1024, max_value=262144),
    retention_period=st.integers(min_value=60, max_value=1209600)
)
def test_queue_to_dict_preserves_properties(delay_seconds, max_message_size, retention_period):
    """
    Property: Queue.to_dict() should preserve all set properties
    """
    queue = sqs.Queue(
        title="TestQueue",
        DelaySeconds=delay_seconds,
        MaximumMessageSize=max_message_size,
        MessageRetentionPeriod=retention_period
    )
    
    result = queue.to_dict()
    
    # Check that properties are preserved
    assert result["Type"] == "AWS::SQS::Queue"
    assert result["Properties"]["DelaySeconds"] == delay_seconds
    assert result["Properties"]["MaximumMessageSize"] == max_message_size
    assert result["Properties"]["MessageRetentionPeriod"] == retention_period