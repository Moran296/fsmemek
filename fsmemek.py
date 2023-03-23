import sys
from collections import namedtuple
import re


STATES = set()
EVENTS = set()

StateAndEvent = namedtuple('StateAndEvent', ['state', 'event'])

def get_state_event_from_func_decl(line: str):
    #any function called on_event
    match = re.match(r'.*on_event\s*\((.*STATE_.*&*), (.*EVENT_.*&*)\).*', line)
    if match:
        state = re.split(r'&| ', match.group(1))[0]
        event = re.split(r'&| ', match.group(2))[0]
        return StateAndEvent(state, event)
    return None

def parse(file_name: str):
    with open(file_name, 'r') as f:
        all_lines = f.readlines()
        for i, line in enumerate(all_lines):
            if stateAndEvent := get_state_event_from_func_decl(line):
                STATES.add(stateAndEvent.state)
                EVENTS.add(stateAndEvent.event)
                


def error(msg):
    print(msg)
    sys.exit(1)


# get file from first arg or exit
FILE = sys.argv[1] if len(sys.argv) > 1 else error("no file specified")
print(f"parsing FILE: {FILE}")
parse(FILE)

for state in STATES:
    print(state)
for event in EVENTS:
    print(event)



