import datetime
from dateutil import rrule

# Minimal failing example from Hypothesis
freq = rrule.YEARLY  # 0 maps to YEARLY
dtstart = datetime.datetime(2000, 1, 1, 0, 0)
interval = 87
count = 93

# Create the rule
rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)

# Get all events
events = list(rule)

print(f"Configuration:")
print(f"  freq: YEARLY")
print(f"  dtstart: {dtstart}")
print(f"  interval: {interval}")
print(f"  count: {count}")
print(f"\nExpected number of events: {count}")
print(f"Actual number of events: {len(events)}")
print(f"Missing events: {count - len(events)}")

# Show last few events to see what's happening
print(f"\nLast 5 events generated:")
for event in events[-5:]:
    print(f"  {event}")

# Check if we're hitting datetime.MAXYEAR
print(f"\nLast event year: {events[-1].year}")
print(f"datetime.MAXYEAR: {datetime.MAXYEAR}")
print(f"Next expected year would be: {events[-1].year + interval}")
print(f"Exceeds MAXYEAR: {events[-1].year + interval > datetime.MAXYEAR}")