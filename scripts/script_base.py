class Token(object):
    name = ""
    def __init__(self, name):
        self.name = name
        
    def __eq__(self, other):
        return type(other) == type(self) and self.name == other.name
    
    def __hash__(self):
        return self.name.__hash__()
    
def get_list_from(string):
    acc = []
    next_token, remaining_string = get_next_token(string)
    while next_token != None:
        acc.append(next_token)
        next_token, remaining_string = get_next_token(remaining_string)
    return acc, remaining_string
        
def get_next_token(string):
    string = string.lstrip(", ")
    if string == "": # We were given empty string, there are no tokens.
        return None, ""
    elif string[0] == "]": # This is the end of a list, there are no tokens.
        return None, string[1:]
    elif string[0] == '"':
        token = ""
        string = string[1:]
        while string[0] != '"':
            if string[0:2] == '\\"':
                token += '"'
                string = string[2:]
            else:
                token += string[0]
                string = string[1:]
        return token, string
    elif string[0] == "[":
        string = string[1:]
        return get_list_from(string)
    else:
        value = ""
        while len(string) != 0 and string[0].isalnum():
            value += string[0]
            string = string[1:]
        try:
            value = int(value)
        except:
            pass
        if type(value) is int:
            return value, string
        elif len(value) != 0:
            return Token(value), string
        else:
            raise Exception("Invalid token string at '%s'." % string)
    
def parse_tokens(string):
    parsed, remainder = get_next_token(string)
    if remainder != "":
        raise Exception("Invalid token string, found '%s' at end." % remainder)
    return parsed

assert(parse_tokens("TOKEN") == Token("TOKEN"))
assert(parse_tokens("[TOKEN]") == [Token("TOKEN")])
assert(parse_tokens("[[TOKEN]]") == [[Token("TOKEN")]])
assert(parse_tokens("[TOKEN, ANOTHER]") == [Token("TOKEN"), Token("ANOTHER")])
assert(parse_tokens("[TOKEN, [ANOTHER]]") == [Token("TOKEN"), [Token("ANOTHER")]])
assert(parse_tokens("[[TOKEN], [ANOTHER]]") == [[Token("TOKEN")], [Token("ANOTHER")]])
assert(parse_tokens("1") == 1)
assert(parse_tokens("[1]") == [1])
assert(parse_tokens("[TOKEN, [1]]") == [Token("TOKEN"), [1]])

token_scripts = {}

def add_token_script(token, function):
    global token_scripts
    token_scripts[token] = function
    
def get_value_from(current_state, current_token):
    if type(current_token) is Token:
        return token_scripts[current_token](current_state, current_token)
    elif type(current_token) is list:
        return token_scripts[current_token[0]](current_state, current_token)
    elif type(current_token) is str:
        return current_token
    elif type(current_token) is int:
        return current_token
    elif type(current_token) is bool:
        return current_token
    else:
        raise Exception("Invalid token %s in current state %s" % (current_token, current_state))
    
def follow_script(initial_state, token_list):
    current_state = initial_state.copy()
    for token in token_list:
        value = get_value_from(current_state, token)
        if should_abort(current_state):
            return get_abort_reason(current_state)
    return current_state

def should_abort(current_state):
    return current_state.get("FAIL", False)

def get_abort_reason(current_state):
    return current_state["FAIL"]

def fail_token(current_state, current_token):
    if type(current_token) is Token:
        current_state["FAIL"] = "Action failed."
    else:
        current_state["FAIL"] = current_token[1]

add_token_script(Token("FAIL"), fail_token)
assert(follow_script({}, [1, 2, "True", True, Token("FAIL")]) == "Action failed.")
assert(follow_script({}, [1, 2, "True", True, [Token("FAIL"), "Really failed."]]) == "Really failed.")

def if_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("IF requires a list token.")
    if get_value_from(current_state, current_token[1]) == True:
        return get_value_from(current_state, current_token[2])
    else:
        return get_value_from(current_state, current_token[3])
    
add_token_script(Token("IF"), if_token)
assert(follow_script({}, [[Token("IF"), True, Token("FAIL"), "Win"]]) == "Action failed.")
assert(follow_script({}, [[Token("IF"), False, Token("FAIL"), "Win"]]) == {}) # We've returned the final state.
assert(get_value_from({}, [Token("IF"), False, Token("FAIL"), "Win"]) == "Win") # We've returned the final state.

def on_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("ON requires a list token.")
    if get_value_from(current_state, current_token[1]) == True:
        return get_value_from(current_state, current_token[2])
    else:
        return None
    
add_token_script(Token("ON"), on_token)
assert(follow_script({}, [[Token("ON"), True, Token("FAIL")]]) == "Action failed.")
assert(follow_script({}, [[Token("ON"), True, "Win"]]) == {}) # We've returned the final state.
assert(get_value_from({}, [Token("ON"), True, "Win"]) == "Win") # We've returned the final state.

def not_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("NOT requires a list token.")
    if get_value_from(current_state, current_token[1]) == False:
        return True
    else:
        return False
add_token_script(Token("NOT"), not_token)
assert(get_value_from({}, [Token("NOT"), True]) == False)
assert(get_value_from({}, [Token("NOT"), False]) == True)

def true_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("TRUE cannot be a head token")
    return True

def false_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("FALSE cannot be a head token")
    return False

add_token_script(Token("TRUE"), true_token)
add_token_script(Token("FALSE"), false_token)
assert(get_value_from({}, Token("TRUE")) == True)
assert(get_value_from({}, Token("FALSE")) == False)

def and_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("AND requires a list token.")
    for token in current_token[1:]:
        value = get_value_from(current_state, token)
        if not value:
            return value
    return True

add_token_script(Token("AND"), and_token)
assert(get_value_from({}, [Token("AND"), True, True]) == True)
assert(get_value_from({}, [Token("AND"), True, False]) == False)
assert(get_value_from({}, [Token("AND"), False, True]) == False)

comparisons = {Token("GT"): lambda x, y: x > y,
               Token("LT"): lambda x, y: x < y,
               Token("GTE"): lambda x, y: x >= y,
               Token("LTE"): lambda x, y: x <= y,
               Token("EQUAL"): lambda x, y: x == y,
               Token("INEQUAL"): lambda x, y: x != y
               }
def comparison_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("comparison (GT, LT, GTE, LTE, EQUAL, INEQUAL) requires a list token.")
    left = get_value_from(current_state, current_token[1])
    right = get_value_from(current_state, current_token[2])
    return comparisons[current_token[0]](left, right)

for comparison in comparisons.keys():
    add_token_script(comparison, comparison_token)
    
assert(get_value_from({}, [Token("GT"), 0, 1]) == False)
assert(get_value_from({}, [Token("GT"), 1, 0]) == True)
assert(get_value_from({}, [Token("GT"), 1, 1]) == False)
assert(get_value_from({}, [Token("LT"), 0, 1]) == True)
assert(get_value_from({}, [Token("LT"), 1, 0]) == False)
assert(get_value_from({}, [Token("LT"), 1, 1]) == False)
assert(get_value_from({}, [Token("GTE"), 0, 1]) == False)
assert(get_value_from({}, [Token("GTE"), 1, 0]) == True)
assert(get_value_from({}, [Token("GTE"), 1, 1]) == True)
assert(get_value_from({}, [Token("LTE"), 0, 1]) == True)
assert(get_value_from({}, [Token("LTE"), 1, 0]) == False)
assert(get_value_from({}, [Token("LTE"), 1, 1]) == True)
assert(get_value_from({}, [Token("EQUAL"), True, True]) == True)
assert(get_value_from({}, [Token("EQUAL"), True, False]) == False)
assert(get_value_from({}, [Token("INEQUAL"), True, True]) == False)
assert(get_value_from({}, [Token("INEQUAL"), True, False]) == True)

def set_token(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("SET requires a list token.")
    token_name = current_token[1].name
    token_value = get_value_from(current_state, current_token[2])
    current_state[token_name] = token_value
    return token_value

add_token_script(Token("SET"), set_token)
assert(follow_script({}, [[Token("SET"), Token("VARIABLE"), 1]]) == {"VARIABLE": 1})