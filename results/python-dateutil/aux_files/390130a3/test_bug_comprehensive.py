import datetime
from dateutil import rrule

def test_count_with_maxyear_limit():
    """Test various scenarios where MAXYEAR might be hit"""
    
    test_cases = [
        # (freq, dtstart, interval, count, description)
        (rrule.YEARLY, datetime.datetime(2000, 1, 1), 87, 93, "YEARLY with interval 87"),
        (rrule.YEARLY, datetime.datetime(9900, 1, 1), 10, 20, "YEARLY starting near MAXYEAR"),
        (rrule.MONTHLY, datetime.datetime(9990, 1, 1), 12, 200, "MONTHLY near MAXYEAR"),
        (rrule.DAILY, datetime.datetime(9998, 1, 1), 365, 10, "DAILY near MAXYEAR"),
    ]
    
    print("Testing count parameter when approaching datetime.MAXYEAR:")
    print("=" * 60)
    
    for freq, dtstart, interval, count, desc in test_cases:
        rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
        events = list(rule)
        
        print(f"\nTest: {desc}")
        print(f"  Config: freq={rrule.FREQNAMES[freq]}, dtstart={dtstart.year}, interval={interval}, count={count}")
        print(f"  Expected events: {count}")
        print(f"  Actual events: {len(events)}")
        
        if len(events) != count:
            print(f"  ❌ BUG: Missing {count - len(events)} events!")
            if events:
                print(f"  Last event: {events[-1]}")
                if freq == rrule.YEARLY:
                    print(f"  Next would be year: {events[-1].year + interval}")
                elif freq == rrule.MONTHLY:
                    next_month = events[-1].month + interval
                    next_year = events[-1].year + (next_month - 1) // 12
                    print(f"  Next would be year: {next_year}")
        else:
            print(f"  ✓ Correct count")

def test_count_vs_until_precedence():
    """Test that count takes precedence over MAXYEAR limit"""
    
    print("\n" + "=" * 60)
    print("Testing count vs MAXYEAR precedence:")
    print("=" * 60)
    
    # When both count and effective MAXYEAR limit apply, count should win
    rule = rrule.rrule(rrule.YEARLY, 
                      dtstart=datetime.datetime(9950, 1, 1),
                      interval=1,
                      count=100)
    
    events = list(rule)
    print(f"\nYEARLY from 9950 with count=100:")
    print(f"  Expected: 100 events (9950-10049)")
    print(f"  Actual: {len(events)} events")
    
    if events:
        print(f"  First event: {events[0]}")
        print(f"  Last event: {events[-1]}")
        
    if len(events) != 100:
        print(f"  ❌ BUG: count parameter not honored when hitting MAXYEAR")

if __name__ == "__main__":
    test_count_with_maxyear_limit()
    test_count_vs_until_precedence()