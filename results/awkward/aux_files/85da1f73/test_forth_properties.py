import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from awkward.forth import ForthMachine32, ForthMachine64


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_addition_commutativity(a, b):
    """Test that addition is commutative: a + b == b + a"""
    machine1 = ForthMachine64(f'{a} {b} +')
    machine1.begin()
    machine1.run()
    
    machine2 = ForthMachine64(f'{b} {a} +')
    machine2.begin()
    machine2.run()
    
    assert machine1.stack == machine2.stack


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_multiplication_commutativity(a, b):
    """Test that multiplication is commutative: a * b == b * a"""
    machine1 = ForthMachine64(f'{a} {b} *')
    machine1.begin()
    machine1.run()
    
    machine2 = ForthMachine64(f'{b} {a} *')
    machine2.begin()
    machine2.run()
    
    assert machine1.stack == machine2.stack


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_dup_duplicates_top(x):
    """Test that dup duplicates the top stack element"""
    machine = ForthMachine64(f'{x} dup')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x, x]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_swap_swaps_top_two(a, b):
    """Test that swap exchanges the top two stack elements"""
    machine = ForthMachine64(f'{a} {b} swap')
    machine.begin()
    machine.run()
    
    assert machine.stack == [b, a]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_drop_removes_top(a, b):
    """Test that drop removes the top stack element"""
    machine = ForthMachine64(f'{a} {b} drop')
    machine.begin()
    machine.run()
    
    assert machine.stack == [a]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_addition_identity(x):
    """Test that x + 0 == x"""
    machine = ForthMachine64(f'{x} 0 +')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_multiplication_identity(x):
    """Test that x * 1 == x"""
    machine = ForthMachine64(f'{x} 1 *')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_subtraction_self(x):
    """Test that x - x == 0"""
    machine = ForthMachine64(f'{x} {x} -')
    machine.begin()
    machine.run()
    
    assert machine.stack == [0]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_max_commutativity(a, b):
    """Test that max is commutative: max(a, b) == max(b, a)"""
    machine1 = ForthMachine64(f'{a} {b} max')
    machine1.begin()
    machine1.run()
    
    machine2 = ForthMachine64(f'{b} {a} max')
    machine2.begin()
    machine2.run()
    
    assert machine1.stack == machine2.stack


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_min_commutativity(a, b):
    """Test that min is commutative: min(a, b) == min(b, a)"""
    machine1 = ForthMachine64(f'{a} {b} min')
    machine1.begin()
    machine1.run()
    
    machine2 = ForthMachine64(f'{b} {a} min')
    machine2.begin()
    machine2.run()
    
    assert machine1.stack == machine2.stack


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_max_idempotence(x):
    """Test that max(x, x) == x"""
    machine = ForthMachine64(f'{x} {x} max')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_min_idempotence(x):
    """Test that min(x, x) == x"""
    machine = ForthMachine64(f'{x} {x} min')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_min_max_ordering(a, b):
    """Test that min(a, b) <= max(a, b)"""
    machine_min = ForthMachine64(f'{a} {b} min')
    machine_min.begin()
    machine_min.run()
    
    machine_max = ForthMachine64(f'{a} {b} max')
    machine_max.begin()
    machine_max.run()
    
    assert machine_min.stack[0] <= machine_max.stack[0]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_negate_twice_identity(x):
    """Test that negating twice returns the original value"""
    machine = ForthMachine64(f'{x} negate negate')
    machine.begin()
    machine.run()
    
    assert machine.stack == [x]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_abs_idempotence(x):
    """Test that abs(abs(x)) == abs(x)"""
    machine1 = ForthMachine64(f'{x} abs')
    machine1.begin()
    machine1.run()
    
    machine2 = ForthMachine64(f'{x} abs abs')
    machine2.begin()
    machine2.run()
    
    assert machine1.stack == machine2.stack


@given(st.integers(min_value=-2147483647, max_value=2147483647),
       st.integers(min_value=-2147483647, max_value=2147483647))
def test_machine32_vs_machine64_consistency_addition(a, b):
    """Test that ForthMachine32 and ForthMachine64 produce same results for 32-bit operations"""
    # Avoid overflow for 32-bit machine
    assume(abs(a + b) < 2147483648)
    
    machine32 = ForthMachine32(f'{a} {b} +')
    machine32.begin()
    machine32.run()
    
    machine64 = ForthMachine64(f'{a} {b} +')
    machine64.begin()
    machine64.run()
    
    assert machine32.stack == machine64.stack


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_over_operation(a, b, c):
    """Test that 'over' copies the second element to the top"""
    machine = ForthMachine64(f'{a} {b} {c} over')
    machine.begin()
    machine.run()
    
    assert machine.stack == [a, b, c, b]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_rot_operation(a, b, c):
    """Test that 'rot' rotates the top three elements"""
    machine = ForthMachine64(f'{a} {b} {c} rot')
    machine.begin()
    machine.run()
    
    assert machine.stack == [b, c, a]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_nip_operation(a, b):
    """Test that 'nip' removes the second element"""
    machine = ForthMachine64(f'{a} {b} nip')
    machine.begin()
    machine.run()
    
    assert machine.stack == [b]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_tuck_operation(a, b):
    """Test that 'tuck' duplicates top and puts it below second"""
    machine = ForthMachine64(f'{a} {b} tuck')
    machine.begin()
    machine.run()
    
    assert machine.stack == [b, a, b]


@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_2dup_operation(a, b):
    """Test that '2dup' duplicates top two elements"""
    machine = ForthMachine64(f'{a} {b} 2dup')
    machine.begin()
    machine.run()
    
    assert machine.stack == [a, b, a, b]


@given(st.integers(min_value=1, max_value=1000000),
       st.integers(min_value=1, max_value=1000000))
def test_division_multiplication_inverse(a, b):
    """Test that (a * b) / b == a for positive integers"""
    machine = ForthMachine64(f'{a} {b} * {b} /')
    machine.begin()
    machine.run()
    
    assert machine.stack == [a]


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_stack_clear_operation(x):
    """Test that stack_clear empties the stack"""
    machine = ForthMachine64(f'{x} {x} {x}')
    machine.begin()
    machine.run()
    
    assert len(machine.stack) == 3
    machine.stack_clear()
    assert machine.stack == []


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_stack_push_pop_roundtrip(x):
    """Test that push followed by pop returns same value"""
    machine = ForthMachine64('')
    machine.begin()
    
    machine.stack_push(x)
    assert machine.stack == [x]
    
    popped = machine.stack_pop()
    assert popped == x
    assert machine.stack == []