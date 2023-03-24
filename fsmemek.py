import sys
from collections import namedtuple
import re


STATES = set()
EVENTS = set()

StateAndEvent = namedtuple('StateAndEvent', ['state', 'event'])

def get_complete_statement(lines):
    # get the complete statement from line i
    # return the complete statement
    line = lines[0]
    if ';' in line:
        return line
    else:
        return line + get_complete_statement(lines[1:])

def get_complete_condition(lines):
    # get the complete condtion from the if/else if statement
    # return the complete condition
    count = 0
    complete_line = lines[count]

    while complete_line.count('(') != complete_line.count(')'):
        count += 1
        complete_line = complete_line.strip() + lines[count].strip()

    paran = 0
    condition = ""
    for c in complete_line:
        if c == ')':
            paran -= 1
        if paran >= 1:
            condition += c
        if c == '(':
            paran += 1

    return condition


def copy_until_closed_braces(lines):
    open_braces = 1
    returned_lines = []

    if lines[0].strip() == "{":
        returned_lines.append(lines[0])
        lines = lines[1:]

    for line in lines:
        if open_braces == 1 and line.strip().startswith("}"):
            returned_lines.append("}")
            break

        returned_lines.append(line)
        for c in line:
            if c == '{':
                open_braces += 1
            if c == '}':
                open_braces -= 1
        if open_braces == 0:
            break

    return returned_lines

def get_clause(lines):
    braces = []
    if lines[0].strip().endswith('{') or lines[1].strip().startswith('{'):
        return copy_until_closed_braces(lines[1:])
    elif lines[1].strip().endswith(';'):
        return ["placeholder", lines[1]]
    else:
        return None


class ReturnedState:
    def __init__(self, state) -> None:
        self.state = state
    def __str__(self) -> str:
        return self.state if self.state else "NONE"

class DecisionNode:
    def __init__(self, parent, condition, is_trenary=False):
        self.children = [] # list of DecisionNode or States (str)
        self.parent = parent
        self.condition = condition

    def print(self):
        if len(self.children) == 0:
            return

        for child in self.children:
            if isinstance(child, DecisionNode) and child.condition is not None:
                print (f"IF {child.condition}")
                child.print()
                print ("ELSE")
            else:
                print(child)


def get_state_from_return_statement(line) :
    if match := re.match(r'.*(?P<state>STATE_.*)\s*\{.*', line.strip()):
        return match.group('state').strip()
    elif "nullopt" in line:
        return "NULLOPT"

    return None


def handle_return_statement(node, line):
    trenary_match = re.match(r'return (?P<condition>.*)\?(?P<ret_1>.*):(?P<ret_2>.*);', line.strip())
    if trenary_match:
        new_node = DecisionNode(parent=node, condition=trenary_match.group('condition').strip())
        ret_1 = get_state_from_return_statement(trenary_match.group('ret_1').strip())
        ret_2 = get_state_from_return_statement(trenary_match.group('ret_2').strip())
        new_node.children.append(ReturnedState(ret_1))
        node.children.append(new_node)
        node.children.append(ReturnedState(ret_2))
    else:
        node.children.append(ReturnedState(get_state_from_return_statement(line.strip())))


def CreateDecisionTree(clause, root):
    number_of_lines_to_skip = 0

    for i, line in enumerate(clause):
        if number_of_lines_to_skip > 0:
            number_of_lines_to_skip -= 1
            continue

        if line.strip().startswith('return '):
            handle_return_statement(root, line)

        if line.strip().startswith('if (') or line.strip().startswith('if(') or 'else if (' in  line.strip() or 'else if(' in line.strip():
            #should never be none!
            condition = get_complete_condition(clause[i:])
            new_clause = get_clause(clause[i:])
            if new_clause is None:
                continue

            number_of_lines_to_skip = len(new_clause) - 1

            new_node = DecisionNode(parent=root, condition=condition)
            CreateDecisionTree(new_clause, new_node)
            #if new_node.returns():
            root.children.append(new_node)

class OnEventFunc:
    def __init__(self, clause, state, event):
        self.state = state
        self.event = event
        self.clause = clause
        self.root = DecisionNode(parent=None, condition=None)
        CreateDecisionTree(self.clause, self.root)


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
                f = OnEventFunc(get_clause(all_lines[i:]), stateAndEvent.state, stateAndEvent.event)
                f.root.print()
                print("-------------------------\n\n\n")



def error(msg):
    print(msg)
    sys.exit(1)


# get file from first arg or exit
#FILE = sys.argv[1] if len(sys.argv) > 1 else error("no file specified")
FILE = "./example/fsm.cpp.txt"
print(f"parsing FILE: {FILE}")
parse(FILE)

for state in STATES:
    print(state)
for event in EVENTS:
    print(event)



