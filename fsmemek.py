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

# assumes a function ends with ') {'
# assumes that return looks like 'return function(...);'
def get_spesific_function_clause(function_line):
    function_name_match = re.match(r'return (?P<function_name>.*)\(.*\);', function_line.strip())
    if function_name_match is None:
        return None

    function_name = function_name_match.group('function_name').strip()

    for i, line in enumerate(LINES):
        #is the line a function declaration?
        func_match = re.match(r'.* .*\:\:.*\(.*\) {', line.strip())
        if function_name in line and func_match:
            clause = get_clause(LINES[i:])
            return clause

    return None

class ReturnedState:
    def __init__(self, state) -> None:
        self.state = state
    def __str__(self) -> str:
        return self.state if self.state else "NONE"

class DecisionNode:
    def __init__(self, parent, condition):
        self.children = [] # list of DecisionNode or States (str)
        self.parent = parent
        self.condition = condition

    def returns(self):
        for child in self.children:
            if isinstance(child, ReturnedState):
                return True
            elif isinstance(child, DecisionNode) and child.returns():
                return True
        return False


    def print(self, indet=0):
        if len(self.children) == 0:
            return

        for child in self.children:
            if isinstance(child, DecisionNode) and child.condition is not None:
                print (f"IF {child.condition}")
                child.print(indet=indet+2)
                print ("ELSE")
            else:
                print(child)


def get_state_from_return_statement(line) :
    if match := re.match(r'.*(?P<state>STATE_[a-zA-Z0-9_]*)[{(].*', line.strip()):
        return match.group('state').strip()
    elif "nullopt" in line:
        return "NULLOPT"

    return None


def handle_return_statement(node, lines):

    line = lines[0] if lines[0].strip().endswith(';') else get_complete_statement(lines)
    line = " ".join(line.strip().replace('\n', ' ').split())

    trenary_match = re.match(r'return (?P<condition>.*) \? (?P<ret_1>.*) \: (?P<ret_2>.*);', line.strip())
    if trenary_match:
        new_node = DecisionNode(parent=node, condition=trenary_match.group('condition').strip())
        ret_1 = get_state_from_return_statement(trenary_match.group('ret_1').strip())
        ret_2 = get_state_from_return_statement(trenary_match.group('ret_2').strip())
        new_node.children.append(ReturnedState(ret_1))
        node.children.append(new_node)
        node.children.append(ReturnedState(ret_2))
    elif "STATE_" not in line and line.strip().endswith(');'):
        cl = get_spesific_function_clause(line)
        if cl is None:
            print(f"return statement not handled: {line}")
        CreateDecisionTree(cl, node)
    else:
        node.children.append(ReturnedState(get_state_from_return_statement(line.strip())))

def handle_switch_case(node, lines, switch_line):
    switch_match = re.match(r'switch.*\((?P<condition>.*)\)', switch_line.strip())
    if switch_match is None:
        return None

    switch_var = switch_match.group('condition').strip()

    current_case_node = None
    last_falltrough_conditions = []

    for i, line in enumerate(lines):
        if line.strip().startswith('default'):
            current_case_node = "DEFAULT"

        elif line.strip().startswith('case'):
            case_match = re.match(r'case\s?(?P<state>.*):', line.strip())
            if case_match:
                case_condition = switch_var + " == " + case_match.group('state')
                if len(last_falltrough_conditions) > 0:
                    case_condition = " || ".join(last_falltrough_conditions) + " || " + case_condition

                current_case_node = DecisionNode(parent=node, condition=case_condition)

        elif line.strip().startswith('return '):
            if current_case_node is None:
                print("SOMETHING IS WRONG - SHOULD BE IN CASE")
            elif current_case_node == "DEFAULT":
                handle_return_statement(node, lines[i:])
            else:
                handle_return_statement(current_case_node, lines[i:])
                node.children.append(current_case_node)

        if "[[fallthrough]]" in line:
            last_falltrough_conditions.append(current_case_node.condition)
        else:
            last_falltrough_conditions = []


def CreateDecisionTree(clause, root):
    number_of_lines_to_skip = 0

    for i, line in enumerate(clause):
        if number_of_lines_to_skip > 0:
            number_of_lines_to_skip -= 1
            continue

        if line.strip().startswith('return '):
            handle_return_statement(root, clause[i:])

        if line.strip().startswith('if (') or line.strip().startswith('if(') or 'else if (' in  line.strip() or 'else if(' in line.strip():
            #should never be none!
            condition = get_complete_condition(clause[i:])
            new_clause = get_clause(clause[i:])
            if new_clause is None:
                continue

            number_of_lines_to_skip = len(new_clause) - 1

            new_node = DecisionNode(parent=root, condition=condition)
            CreateDecisionTree(new_clause, new_node)
            if new_node.returns():
                root.children.append(new_node)

        if line.strip().startswith("switch (") or line.strip().startswith("switch("):
            new_clause = get_clause(clause[i:])
            handle_switch_case(root, new_clause, line)
            number_of_lines_to_skip = len(new_clause) - 1


class OnEventFunc:
    def __init__(self, clause, state, event):
        self.state = state
        self.event = event
        self.clause = clause
        self.root = DecisionNode(parent=None, condition=None)
        CreateDecisionTree(self.clause, self.root)


def get_state_event_from_func_decl(line: str):
    #any function called on_event
    match = re.match(r'.*on_event\s*\((.*STATE_.*&*), .*(.*EVENT_.*&*)\).*', line)
    if match:
        state = re.split(r'&| ', match.group(1))[0]
        event = re.split(r'&| ', match.group(2))[0]
        return StateAndEvent(state, event)
    return None

def parse():
    for i, line in enumerate(LINES):
        if stateAndEvent := get_state_event_from_func_decl(line):
            STATES.add(stateAndEvent.state)
            EVENTS.add(stateAndEvent.event)
            print(f"on_event({stateAndEvent.state}, {stateAndEvent.event})")
            f = OnEventFunc(get_clause(LINES[i:]), stateAndEvent.state, stateAndEvent.event)
            f.root.print()
            print("-------------------------\n\n\n")

def error(msg):
    print(msg)
    sys.exit(1)

# get file from first arg or exit
FILE = sys.argv[1] if len(sys.argv) > 1 else error("no file specified")
LINES = None
with open(FILE, 'r') as f:
    LINES = f.readlines()
    print(f"parsing FILE: {FILE}")
    parse()





