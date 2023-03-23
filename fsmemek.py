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

    return complete_line.strip()


def copy_relevant_lines(lines):
    # copy all lines until we hit a closing brace
    # return the lines
    braces = []
    for i, line in enumerate(lines):
        if '{' in line:
            braces.append('{')
        if '}' in line:
            braces.pop()
        if not braces and i > 0:
            return lines[:i+1].copy()

class DecisionNode:
    def __init__(self):
        self.children = [] # list of DecisionNode or States (str)
        self.parent = None
        self.condition = None

    def print(self):
        print(self.condition)
        for child in self.children:
            if isinstance(child, DecisionNode):
                child.print()
            else:
                print(child)


class OnEventFunc:
    def __init__(self, lines, state, event):
        self.state = state
        self.event = event
        self.lines = copy_relevant_lines(lines)
        self.currentNode = DecisionNode()
        self.decision_tree = self.CreateDecisionTree()

    def handle_return_statement(self, line):
        current_node = self.currentNode

        trenary_match = re.match(r'return (?P<condition>.*)\?(?P<ret_1>.*):(?P<ret_2>.*);', line.strip())
        if trenary_match:
            new_node = DecisionNode()
            new_node.parent = current_node
            current_node.children.append(new_node)
            current_node = new_node
            current_node.condition = trenary_match.group('condition').strip() # TODO strip paranthasis
            current_node.children.append(trenary_match.group('ret_1').strip())
            current_node.children.append(trenary_match.group('ret_2').strip())
        else:
            self.currentNode.children.append(line.strip())


    def CreateDecisionTree(self):
        current_node = self.currentNode
        root = current_node

        lines = self.lines
        for i, line in enumerate(lines):
            if line.strip().startswith('return '):
                complete_line = get_complete_statement(lines[i:])
                self.handle_return_statement(complete_line)
                pass
            if line.strip().startswith('if (') or line.strip().startswith('if('):

                new_node = DecisionNode()
                new_node.parent = current_node
                current_node.children.append(new_node)
                current_node = new_node
                current_node.condition = get_complete_condition(lines[i:])


            elif 'else if (' in  line.strip() or 'else if(' in line.strip():
                complete_condition = get_complete_condition(lines[i:])
                new_node = DecisionNode()
                new_node.parent = current_node
                current_node.parent.children.append(new_node)
                current_node = new_node
                current_node.condition = get_complete_condition(lines[i:])

            elif 'else' in line.strip():
                new_node = DecisionNode()
                new_node.parent = current_node
                current_node.parent.children.append(new_node)
                current_node = new_node

            else:
                current_node.children.append(line.strip())

        return root




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
                f = OnEventFunc(all_lines[i:], stateAndEvent.state, stateAndEvent.event)
                f.decision_tree.print()
                print("-------------------------\n\n\n")



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



