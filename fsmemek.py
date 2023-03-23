import sys
import re


STATES = []
EVENTS = []

def get_state_event_from_func_decl(line: str):
    #any function called on_event
    match = re.match(r'.*on_event\s*\((.*STATE_.*&*), (.*EVENT_.*&*)\).*', line)
    if match:
        state = re.split(r'&| ', match.group(1))[0]
        event = re.split(r'&| ', match.group(2))[0]
        print(f"state is {state}")
        print(f"event is {event}")
        return True

def parse(file_name: str):
    with open(file_name, 'r') as f:
        all_lines = f.readlines()
        for i, line in enumerate(all_lines):
            if get_state_event_from_func_decl(line):
                pass


def error(msg):
    print(msg)
    sys.exit(1)


# get file from first arg or exit
FILE = sys.argv[1] if len(sys.argv) > 1 else error("no file specified")
print(f"parsing FILE: {FILE}")
parse(FILE)



