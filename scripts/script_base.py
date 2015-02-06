class Token(object):
    name = ""
    def __init__(self, name):
        self.name = name
        
    def __eq__(self, other):
        return type(other) == type(self) and self.name == other.name
    
    def __hash__(self):
        return self.name.__hash__()
    
    def __repr__(self):
        return self.name

def check_token_list(current_token, min_len, max_len):
    if not type(current_token) is list and min_len != 0:
        raise Exception(current_token.name + " must be list head.")
    elif type(current_token) is list and not (min_len <= len(current_token) <= max_len):
        raise Exception("Invalid list len for " + current_token[0].name + ". !%d <= %d <= %d" % (min_len, len(current_token), max_len))
    
# Decorator
def token_func(min_len, max_len):
    def actual_decorator(func):
        def decorated_function(current_state, current_token):
            check_token_list(current_token, min_len, max_len)
            return func(current_state, current_token)
        decorated_function.list_head_min = min_len
        decorated_function.list_head_max = max_len
        return decorated_function
    return actual_decorator
    
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
        return token, string[1:]
    elif string[0] == "[":
        string = string[1:]
        return get_list_from(string)
    else:
        value = ""
        while len(string) != 0 and (string[0].isalnum() or (len(value) == 0 and string[0] == "-")):
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

assert(get_list_from("") == ([], ''))
fighter = [[Token("ON"), [Token("AND"), [Token("EQUAL"), Token("TYPE"), "Attack"], [Token("EQUAL"), Token("CHARACTER"), [Token("OWNER"), Token("THIS")]],
                         [Token("NOT"), [Token("THISTURN"), [Token("EQUAL"), Token("TYPE"), "Attack"]]]], [Token("DRAW"), 1]]]
assert(get_list_from("""[ON, [AND, [EQUAL, TYPE, "Attack"], [EQUAL, CHARACTER, [OWNER, THIS]], [NOT, [THISTURN, [EQUAL, TYPE, "Attack"]]]], [DRAW, 1]]""") == (fighter, ""))
assert(parse_tokens("TOKEN") == Token("TOKEN"))
assert(parse_tokens("[TOKEN]") == [Token("TOKEN")])
assert(parse_tokens("[[TOKEN]]") == [[Token("TOKEN")]])
assert(parse_tokens("[TOKEN, ANOTHER]") == [Token("TOKEN"), Token("ANOTHER")])
assert(parse_tokens("[TOKEN, [ANOTHER]]") == [Token("TOKEN"), [Token("ANOTHER")]])
assert(parse_tokens("[[TOKEN], [ANOTHER]]") == [[Token("TOKEN")], [Token("ANOTHER")]])
assert(parse_tokens("1") == 1)
assert(parse_tokens("-1") == -1)
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
    else:
        return current_token
    
def follow_script(initial_state, token_list):
    #current_state = initial_state.copy()
    current_state = initial_state
    for token in token_list:
        value = get_value_from(current_state, token)
        if should_abort(current_state):
            return get_abort_reason(current_state)
    return current_state

def check_token(token, errors):
    if type(token) is Token:
        if token_scripts.has_key(token):
            if hasattr(token_scripts[token], "list_head_min"):
                if token_scripts[token].list_head_min != 0:
                    errors.append("Found token %s as non-list head. Should be list head." % token.name)
        else:
            errors.append("Did not find script for %s" % token.name)
    elif type(token) is list:
        if type(token[0]) is int:
            for sub_token in token[1:]:
                check_token(sub_token, errors)
        else:
            if token_scripts.has_key(token[0]):
                if hasattr(token_scripts[token[0]], "list_head_min") and hasattr(token_scripts[token[0]], "list_head_max"):
                    if len(token) < token_scripts[token[0]].list_head_min:
                        errors.append("Found token list for %s with len %d (min %d)" % (token[0], len(token), token_scripts[token[0]].list_head_min))
                    if len(token) > token_scripts[token[0]].list_head_max:
                        errors.append("Found token list for %s with len %d (max %d)" % (token[0], len(token), token_scripts[token[0]].list_head_max))
                else:
                    errors.append("Did not have list constraints for %s" % (token[0]))
                for sub_token in token[1:]:
                    check_token(sub_token, errors)
            else:
                errors.append("Did not find script for list head %s" % token[0])

def check_script(script):
    errors = []
    if type(script) is str:
        try:
            script_tokens, remainder = get_list_from(script)
            script = script_tokens
        except:
#             errors.append("!!FAILED TO PARSE: %s" % script)
            raise
    for token in script:
        check_token(token, errors)
    return errors

def abort(current_state, reason):
    current_state["FAIL"] = reason

def should_abort(current_state):
    return current_state.get("FAIL", False)

def get_abort_reason(current_state):
    return current_state["FAIL"]

@token_func(0, 2)
def fail_token(current_state, current_token):
    if type(current_token) is Token:
        current_state["FAIL"] = "Action failed."
    else:
        current_state["FAIL"] = current_token[1]

add_token_script(Token("FAIL"), fail_token)
assert(follow_script({}, [1, 2, "True", True, Token("FAIL")]) == "Action failed.")
assert(follow_script({}, [1, 2, "True", True, [Token("FAIL"), "Really failed."]]) == "Really failed.")

@token_func(4, 4)
def if_token(current_state, current_token):
    if get_value_from(current_state, current_token[1]):
        return get_value_from(current_state, current_token[2])
    else:
        return get_value_from(current_state, current_token[3])
    
add_token_script(Token("IF"), if_token)
assert(follow_script({}, [[Token("IF"), True, Token("FAIL"), "Win"]]) == "Action failed.")
assert(follow_script({}, [[Token("IF"), False, Token("FAIL"), "Win"]]) == {}) # We've returned the final state.
assert(get_value_from({}, [Token("IF"), False, Token("FAIL"), "Win"]) == "Win") # We've returned the final state.

@token_func(3, 9999)
def on_token(current_state, current_token):
    if get_value_from(current_state, current_token[1]):
        tokens = current_token[2:]
        while not should_abort(current_state) and tokens:
            get_value_from(current_state, tokens[0])
            tokens = tokens[1:]
    else:
        return None
    
@token_func(2, 9999)
def do_token(current_state, current_token):
    check_token_list(current_token, 2, 999)
    tokens = current_token[1:]
    while not should_abort(current_state) and tokens:
        get_value_from(current_state, tokens[0])
        tokens = tokens[1:]
    
add_token_script(Token("ON"), on_token)
assert(follow_script({}, [[Token("ON"), True, Token("FAIL")]]) == "Action failed.")
assert(follow_script({}, [[Token("ON"), True, "Win"]]) == {}) # We've returned the final state.

add_token_script(Token("DO"), do_token)
assert(follow_script({}, [[Token("DO"), True, Token("FAIL")]]) == "Action failed.")
assert(follow_script({}, [[Token("DO"), True, "Win"]]) == {}) # We've returned the final state.

@token_func(2, 2)
def not_token(current_state, current_token):
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

def any_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("ANY cannot be a head token")
    return current_token

add_token_script(Token("TRUE"), true_token)
add_token_script(Token("FALSE"), false_token)
add_token_script(Token("ANY"), any_token)
assert(get_value_from({}, Token("TRUE")) == True)
assert(get_value_from({}, Token("FALSE")) == False)

@token_func(2, 9999)
def and_token(current_state, current_token):
    for token in current_token[1:]:
        value = get_value_from(current_state, token)
        if not value:
            return value
    return True

add_token_script(Token("AND"), and_token)
assert(get_value_from({}, [Token("AND"), True, True]) == True)
assert(get_value_from({}, [Token("AND"), True, False]) == False)
assert(get_value_from({}, [Token("AND"), False, True]) == False)
assert(get_value_from({}, [Token("AND"), False, False]) == False)

@token_func(2, 9999)
def or_token(current_state, current_token):
    for token in current_token[1:]:
        value = get_value_from(current_state, token)
        if value:
            return value
    return False

add_token_script(Token("OR"), or_token)
assert(get_value_from({}, [Token("OR"), True, True]) == True)
assert(get_value_from({}, [Token("OR"), True, False]) == True)
assert(get_value_from({}, [Token("OR"), False, True]) == True)
assert(get_value_from({}, [Token("OR"), False, False]) == False)

comparisons = {Token("GT"): lambda x, y: x > y,
               Token("LT"): lambda x, y: x < y,
               Token("GTE"): lambda x, y: x >= y,
               Token("LTE"): lambda x, y: x <= y,
               Token("EQUAL"): lambda x, y: x == y,
               Token("INEQUAL"): lambda x, y: x != y,
               Token("MAX"): lambda x, y: x if x > y else y,
               Token("MIN"): lambda x, y: x if x < y else y,
               }

@token_func(3, 3)
def comparison_token(current_state, current_token):
    left = get_value_from(current_state, current_token[1])
    right = get_value_from(current_state, current_token[2])
    if type(left) != type(right):
        return False
    return comparisons[current_token[0]](left, right)

for comparison in comparisons.keys():
    add_token_script(comparison, comparison_token)

operators = {Token("DIVFLOOR"): lambda x, y: x // y,
             }

@token_func(3, 3)
def operator_token(current_state, current_token):
    left = get_value_from(current_state, current_token[1])
    right = get_value_from(current_state, current_token[2])
    return operators[current_token[0]](left, right)

for operator in operators.keys():
    add_token_script(operator, operator_token)
    
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

@token_func(3, 3)
def set_token(current_state, current_token):
    token_name = current_token[1].name
    token_value = get_value_from(current_state, current_token[2])
    current_state[token_name] = token_value
    return token_value

add_token_script(Token("SET"), set_token)

@token_func(2, 2)
def get_token(current_state, current_token):
    token_name = current_token[1].name
    return current_state[token_name]

add_token_script(Token("GET"), get_token)
assert(get_value_from({"VARIABLE": 1}, [Token("SET"), Token("VARIABLE"), 1]) == 1)