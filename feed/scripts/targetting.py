try:
    from script_base import add_token_script, follow_script, get_value_from, Token, token_func
except:
    def token_func(min_len, max_len):
        def actual_decorator(func):
            def decorated_function(current_state, current_token):
                check_token_list(current_token, min_len, max_len)
                return func(current_state, current_token)
            decorated_function.list_head_min = min_len
            decorated_function.list_head_max = max_len
            return decorated_function
        return actual_decorator

def target_token(current_state, current_token):
    if type(current_token) is not Token:
        raise Exception("TARGET cannot be a list head. [%s]" % (current_token, ))
    return current_state.get("TARGET", None)

def checked_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("CHECKED cannot be a list head. [%s]" % (current_token, ))
    return current_state["CHECKED"]

def targetcount_token(current_state, current_token):
    if not type(current_token) is Token:
        raise Exception("TARGETCOUNT cannot be a list head. [%s]" % (current_token, ))
    return target_count(current_state)
    
def target_count(current_state):
    return len(current_state["TARGETS"]) if current_state.has_key("TARGETS") else (1 if current_state.has_key("TARGET") else 0)

@token_func(2, 2)
def each_target(current_state, current_token):
    if not type(current_token) is list:
        raise Exception("EACHTARGET requires arguments to be evaluated")
    if current_state.has_key("TARGETS"):
        for target in current_state.get("TARGETS", []):
            current_state["TARGET"] = target
            value = get_value_from(current_state, current_token[1])
            del current_state["TARGET"]
    else:
        get_value_from(current_state, current_token[1])

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
        return me.piles["Discard"]
    elif source == Token("DECK"):
        return me.piles["Deck"]
    elif source == Token("BACKPACK"):
        return me.piles["Backpack"]
    else:
        raise Exception("Failed to find valid source definition from %s" % (source, ))

@token_func(4, 4)
def choosex_token(current_state, current_token):
    prompt = get_value_from(current_state, current_token[1])
    minimum = get_value_from(current_state, current_token[2])
    maximum = get_value_from(current_state, current_token[3])
    value = -1
    while value is not None and (value < minimum or value > maximum):
        value = askInteger(prompt + "(minimum %d; maximum %d)" % (minimum, maximum), minimum)
    if value is not None:
        return value
    else:
        current_state["FAIL"] = "Cancelled picking integer."

@token_func(3, 999)
def choose_token(current_state, current_token):
    prompt = get_value_from(current_state, current_token[1])
    choices = []
    for token in current_token[2:]:
        choices.append(get_value_from(current_state, token))
    colorList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel"]
    picked = askChoice(prompt, choices, colorList, customButtons=customButtons)
    if picked == 0 or picked == -1:
        current_state["FAIL"] = "Cancelled making choice."
    else:
        return picked - 1
    
@token_func(3, 999)
def actions_token(current_state, current_token):
#     prompt = get_value_from(current_state, current_token[1])
    prompt = "Choose an action:"
    choices = []
    actions = []
    pairs = zip(current_token[1::2], current_token[2::2])
    for value, script in pairs:
        choices.append(get_value_from(current_state, value))
        actions.append(script)
    colorList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel"]
    picked = askChoice(prompt, choices, colorList, customButtons=customButtons)
    if picked == 0 or picked == -1:
        current_state["FAIL"] = "Cancelled taking action."
    else:
        return get_value_from(current_state, actions[picked - 1])

@token_func(2, 2)
def choose_type_token(current_state, current_token):
    prompt = get_value_from(current_state, current_token[1])
    choices = ["Attack", "Spell", "Affliction", "Tactic"]
    colorList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel"]
    picked = askChoice(prompt, choices, colorList, customButtons=customButtons)
    if picked == 0 or picked == -1:
        current_state["FAIL"] = "Cancelled making type choice."
    else:
        return choices[picked - 1]

@token_func(3, 3)
def isenemy_token(current_state, current_token):
    candidate = get_value_from(current_state, current_token[1])
    myself = get_value_from(current_state, current_token[2])
    return is_enemy(myself, candidate)

@token_func(2, 2)
def ischaracter_token(current_state, current_token):
    candidate = get_value_from(current_state, current_token[1])
    return is_character(candidate)
    
def is_enemy(myself, candidate):
    if candidate.owner != myself.owner:
        if candidate.Type == "Class":
            return True
        elif is_card_pet(candidate):
            return True
        elif is_card_monster(candidate) != is_card_monster(myself):
            return True
    return False
    
def is_character(candidate):
    if candidate.Type == "Class":
        return True
    elif is_card_npc(candidate):
        return True
    else:
        return False
    
@token_func(1, 1)
def getenemy_token(current_state, current_token):
    return get_value_from(current_state, [Token("GETTARGET"),
                                          [Token("ISENEMY"), Token("CHECKED"), Token("CHARACTER")],
                                          Token("TABLE")])
    
@token_func(1, 1)
def getcharacter_token(current_state, current_token):
    return get_value_from(current_state, [Token("GETTARGET"),
                                          [Token("ISCHARACTER"), Token("CHECKED")],
                                          Token("TABLE")])

@token_func(1, 2)
def is_target_token(current_state, current_token):
    if len(current_token) == 2:
        checked = get_value_from(current_state, current_token[1])
    else:
        checked = owner_this(current_state)
    return checked in current_state.get("TARGETS", []) or checked == current_state.get("TARGET", None)

@token_func(3, 5)
def gettarget_token_dual(current_state, current_token):
    if not type(current_token) is list:
        raise Exception(current_token + " must be list head")
    elif len(current_token) != 5 and current_token[0] == Token("GETTARGETS"):
        raise Exception("GETTARGETS requires 4 arguments: minimum target count, maximum target count, target selector, source definition")
    elif len(current_token) != 3 and (current_token[0] == Token("GETTARGET") or current_token[0] == Token("CHOOSETARGET")):
        raise Exception("%s requires 2 arguments: target selector, source definition" % current_token[0])
    if current_token[0] == Token("GETTARGET") or current_token[0] == Token("CHOOSETARGET"):
        min_count = 1
        max_count = 1
        target_validator = current_token[1]
        if not valid_source(current_token[2]):
            source_defition = get_value_from(current_state, current_token[2])
        else:
            source_defition = current_token[2]
    elif current_token[0] == Token("GETTARGETS"):
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
    choices = ["%s (%s)" % (card.name, card.controller.name) for card in valid_cards]
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
    elif picked == 0 and picked_cards == []:
        current_state["FAIL"] = "Found no valid targets."
    elif len(picked_cards) < min_count and len(picked_cards) > max_count:
        current_state["FAIL"] = "Found %s targets but need between %s and %s" % (len(picked_cards), min_count, max_count)
    elif current_token[0] == Token("GETTARGETS"):
        current_state["TARGETS"] = picked_cards
    elif current_token[0] == Token("GETTARGET"):
        current_state["TARGET"] = picked_cards[0]
    elif current_token[0] == Token("CHOOSETARGET"):
        return picked_cards[0]
    return picked_cards

if __name__ == "__main__":
    add_token_script(Token("TARGET"), target_token)
    add_token_script(Token("CHECKED"), checked_token)
    add_token_script(Token("TARGETCOUNT"), targetcount_token)
    add_token_script(Token("EACHTARGET"), each_target)
    from wounds import *
    for deal_type in ["DEAL", "DEALONLY", "DEALALWAYS", "DEALALWAYSONLY"]:
        def deal_with(deal_type):
            return lambda current_state, current_token: deal(current_state, current_token, deal_type=deal_type)
        add_token_script(Token(deal_type), deal_with(deal_type))
    test_val = follow_script({"TARGETS":["A guy", "A gal", "A goblin"]}, [[Token("EACHTARGET"), [Token("DEAL"), 1, "Standard", Token("TARGET")]]])
    assert(test_val["dealt"] == {"A guy":[["Standard", 1]],
                                  "A gal":[["Standard", 1]],
                                  "A goblin":[["Standard", 1]]})
    assert(("DEAL", ("A guy", "Standard", 1)) in test_val["events"])
    assert(("DEAL", ("A gal", "Standard", 1)) in test_val["events"])
    assert(("DEAL", ("A goblin", "Standard", 1)) in test_val["events"])
    test_val = get_value_from({"TARGETS":["A guy", "A gal", "A goblin"]}, Token("TARGETCOUNT"))
    assert(test_val == 3)

# if __name__ == "__main__":
#     me = object()
#     me.pile = {"Discard":[], "Deck":[], "Backpack":[]}
#     me.hand = []
#     table = []