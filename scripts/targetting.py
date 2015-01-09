try:
    from script_base import add_token_script, follow_script, get_value_from, Token
except:
    pass

def target_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("TARGET cannot be a list head.")
    return current_state["TARGET"]
def checked_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("CHECKED cannot be a list head.")
    return current_state["CHECKED"]
def targetcount_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("TARGETCOUNT cannot be a list head.")
    return len(current_state["TARGETS"]) if current_state.has_key("TARGETS") else (1 if current_state.has_key("TARGET") else 0)

def each_target(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("EACHTARGET requires arguments to be evaluated")
    for target in current_state["TARGETS"]:
        current_state["TARGET"] = target
        value = get_value_from(current_state, current_token[1])
        del current_state["TARGET"]

def valid_source(source):
    return source in [Token("TABLE"),
                      Token("HAND"),
                      Token("DISCARD"),
                      Token("DECK"),
                      Token("BACKPACK"),
                      ]

def cards_in_source(source):
    if source == Token("TABLE"):
        return table
    elif source == Token("HAND"):
        return me.hand
    elif source == Token("DISCARD"):
        return me.pile["Discard"]
    elif source == Token("Deck"):
        return me.pile["Deck"]
    elif source == Token("Backpack"):
        return me.pile["Backpack"]
    else:
        raise Exception("Failed to find valid source definition from %s" % (source, ))

def get_targets(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("GETTARGETS requires 4 arguments: minimum target count, maximum target count, target selector, source definition")
    min_count = get_value_from(current_state, current_token[1])
    max_count = get_value_from(current_state, current_token[2])
    target_validator = current_token[3]
    if not valid_source(current_token[4]):
        source_defition = get_value_from(current_state, current_token[4])
    else:
        source_defition = current_token[4]
    valid_cards = []
    for card in cards_in_source(source_defition):
        current_state["CHECKED"] = card
        is_valid = get_value_from(current_state, target_validator)
        if is_valid:
            valid_cards.append(card)
    del current_state["CHECKED"]
    choices = [card.name for card in valid_cards]
    colorsList = ["#FFFFFF" for _ in valid_cards]
    customButtons = ["Cancel"]
    picked = 0
    picked_cards = []
    while len(valid_cards) > 0 and len(picked_cards) < max_count:
        picked = askChoice("Pick a target:", choices, colorsList, customButtons)
        if picked > 0:
            picked_cards.append(valid_cards[picked - 1])
            del choices[picked - 1]
            if len(customButtons) == 1 and len(picked_cards) >= min_count:
                customButtons.append("Finish")
        else:
            break
    if picked == -1:
        current_state["FAIL"] = "Cancelled picking targets."
    elif len(picked_cards) < min_count and len(picked_cards) > max_count:
        current_state["FAIL"] = "Found %s targets but need between %s and %s" % (len(picked_cards), min_count, max_count)
    else:
        current_state["TARGETS"] = picked_cards
    return picked_cards

add_token_script(Token("TARGET"), target_token)
add_token_script(Token("CHECKED"), checked_token)
add_token_script(Token("TARGETCOUNT"), targetcount_token)
add_token_script(Token("EACHTARGET"), each_target)
if __name__ == "__main__":
    from deal_wounds import *
    test_val = follow_script({"TARGETS":["A guy", "A gal", "A goblin"]}, [[Token("EACHTARGET"), [Token("DEAL"), 1, "Standard", Token("TARGET")]]])
    assert(test_val["dealt"] == {"A guy":[["Standard", 1]],
                                  "A gal":[["Standard", 1]],
                                  "A goblin":[["Standard", 1]]})
    assert(("DEAL", ("A guy", "Standard", 1)) in test_val["events"])
    assert(("DEAL", ("A gal", "Standard", 1)) in test_val["events"])
    assert(("DEAL", ("A goblin", "Standard", 1)) in test_val["events"])
    test_val = get_value_from({"TARGETS":["A guy", "A gal", "A goblin"]}, Token("TARGETCOUNT"))
    assert(test_val == 3)

if __name__ == "__main__":
    me = object()
    me.pile = {"Discard":[], "Deck":[], "Backpack":[]}
    me.hand = []
    table = []