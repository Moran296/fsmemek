import sys
from collections import namedtuple
import re


CONDITION_ID = 1
COLOR_INDEX = 0
COLORS = ["#orange", "#purple", "#pink", "#brown", "#grey", "#magenta", "#lime", "#olive", "#maroon", "#navy", "#teal", "#aqua", "#fuchsia", "#silver", "#gray", "#olive", "#yellowgreen", "#violet", "#turquoise", "#tomato", "#tan", "#steelblue", "#skyblue", "#sienna", "#seagreen", "#sandybrown", "#salmon", "#rosybrown", "#royalblue", "#orangered", "#orchid", "#olivedrab", "#navajowhite", "#moccasin", "#mistyrose", "#midnightblue", "#mediumvioletred", "#mediumturquoise", "#mediumspringgreen", "#mediumslateblue", "#mediumseagreen", "#mediumorchid", "#mediumblue", "#mediumaquamarine", "#maroon", "#lawngreen", "#khaki", "#indigo", "#hotpink", "#honeydew", "#greenyellow", "#green", "#gold", "#fuchsia", "#forestgreen", "#firebrick", "#dodgerblue", "#deeppink", "#darkviolet", "#darkturquoise", "#darkslategray", "#darkslateblue", "#darkseagreen", "#darkorchid", "#darkolivegreen", "#darkmagenta", "#darkkhaki", "#darkgreen", "#darkgoldenrod", "#darkcyan", "#darkblue", "#darkblue", "#cyan", "#crimson", "#cornflowerblue", "#coral", "#chocolate", "#chartreuse", "#cadetblue", "#burlywood", "#blueviolet", "#blue", "#blanchedalmond", "#bisque", "#beige", "#azure", "#aquamarine", "#aquamarine", "#antiquewhite", "#aliceblue", "#aqua", "#aquamarine", "#azure", "#beige", "#bisque", "#blanchedalmond", "#blue", "#blueviolet", "#burlywood", "#cadetblue", "#chartreuse", "#chocolate", "#coral", "#cornflowerblue", "#crimson", "#cyan", "#darkblue", "#darkblue", "#darkcyan", "#darkgolden"]

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
        return self.state if self.state else "*UNKNOWN RETURN VALUE*"

class DecisionNode:
    def __init__(self, parent, condition):
        self.children = [] # list of DecisionNode or States (str)
        self.parent = parent
        self.condition = condition
        global CONDITION_ID
        self.id = f"{CONDITION_ID}" if condition else "0"
        CONDITION_ID = CONDITION_ID + 1 if condition else CONDITION_ID

    def returns(self):
        for child in self.children:
            if isinstance(child, ReturnedState):
                return True
            elif isinstance(child, DecisionNode) and child.returns():
                return True
        return False


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

    def declare_ids(self, file):
        if self.id != "0":
            file.write(f"state {self.id} <<choice>>\n")
            file.write(f"note left of {self.id} {COLORS[COLOR_INDEX]} : {self.condition}\n")
        for child in self.children:
            if isinstance(child, DecisionNode):
                child.declare_ids(file)

    def print_uml(self, file, orginal_state):
        if len(self.children) == 0:
            return

        global COLORS
        global COLOR_INDEX

        state = self.parent.state if isinstance(self.parent, OnEventFunc) else self.id
        event = self.parent.event if isinstance(self.parent, OnEventFunc) else self.condition
        bold_line = f"-[{COLORS[COLOR_INDEX]}]->"
        line = f"-[bold,{COLORS[COLOR_INDEX]}]->"

        def target_id(i):
            if isinstance(self.children[i], ReturnedState):
                if self.children[i].state == "NULLOPT":
                    return orginal_state
                else :
                    return self.children[i].state
            else:
                return self.children[i].id

        for i in range(len(self.children)):
                target = target_id(i)
                if i > 0:
                    file.write(f"{state} {line} {target} : $failure(\"FALSE\")\n")
                else:
                    if isinstance(self.parent, OnEventFunc):
                        file.write(f"{state} {bold_line} {target} \nnote on link\n    __**{event}**__\nend note\n")
                    else:
                        file.write(f"{state} {line} {target} : $success(\"TRUE\")\n")
                state = target
                if isinstance(self.children[i], DecisionNode):
                    self.children[i].print_uml(file, orginal_state)


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
                    cases = [case.split()[-1] for case in last_falltrough_conditions]
                    case_condition = switch_var + " == " + " || ".join(cases) + " || " + case_match.group('state')

                current_case_node = DecisionNode(parent=node, condition=case_condition)
                continue

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
        self.root = DecisionNode(parent=self, condition=None)
        CreateDecisionTree(self.clause, self.root)

    def declare(self, f):
        self.root.declare_ids(f)

    def print_uml(self, f):
        self.root.print_uml(f, self.state)


def get_state_event_from_func_decl(line: str):
    #any function called on_event
    match = re.match(r'.*on_event\s*\((.*STATE_.*&*), .*(.*EVENT_.*&*)\).*', line)
    if match:
        state = re.split(r'&| ', match.group(1))[0]
        event = re.split(r'&| ', match.group(2))[0]
        return StateAndEvent(state, event)
    return None

def parse():
    functions = []

    for i, line in enumerate(LINES):
        if stateAndEvent := get_state_event_from_func_decl(line):
            print(f"on_event({stateAndEvent.state}, {stateAndEvent.event})")
            f = OnEventFunc(get_clause(LINES[i:]), stateAndEvent.state, stateAndEvent.event)
            if f is not None:
                functions.append(f)
    return functions

def output_uml(file_name, functions):
    global COLOR_INDEX
    with open(file_name, "w") as f:
        f.write("@startuml\n")
        f.write("!theme spacelab\n")
        for func in functions:
            func.declare(f)
            f.write("\n\n")
            COLOR_INDEX = (COLOR_INDEX + 1) % len(COLORS)
        COLOR_INDEX = 0
        for func in functions:
            func.print_uml(f)
            f.write("\n")
            COLOR_INDEX = (COLOR_INDEX + 1) % len(COLORS)

        f.write("\n@enduml")

def error(msg):
    print(msg)
    sys.exit(1)

# get file from first arg or exit
FILE = sys.argv[1] if len(sys.argv) > 1 else error("no file specified")
LINES = None
with open(FILE, 'r') as f:
    LINES = f.readlines()
    print(f"parsing FILE: {FILE}")
    functions = parse()
    output_uml(f"{FILE.split('/')[-1].replace('cpp', 'uml')}", functions)





