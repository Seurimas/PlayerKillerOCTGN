class Token(object):
    name = ""
    def __init__(self, name):
        self.name = name
        
    def __eq__(self, other):
        return type(other) == type(self) and self.name == other.name
    
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
        token_str = ""
        while len(string) != 0 and string[0].isalnum():
            token_str += string[0]
            string = string[1:]
        if len(token_str) != 0:
            return Token(token_str), string
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