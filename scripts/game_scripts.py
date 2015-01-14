ANY = "ANY"
# Deal damage event format (deal_type, (target, wound_type, wound_count))
try:
    from script_base import add_token_script, follow_script, get_value_from, Token
except:
    pass

variables = ["THIS", "CHARACTER", "TYPE", "SUBTYPE"]
counters = ["HEALTH", "MANA", "SUBTERFUGE", "STAMINA"]

def setupTokens():
    add_token_script(Token("GETTARGET"), gettarget_token_dual)
    add_token_script(Token("GETTARGETS"), gettarget_token_dual)
    add_token_script(Token("GETENEMY"), getenemy_token)
    add_token_script(Token("GETCHARACTER"), getcharacter_token)
    add_token_script(Token("ISENEMY"), isenemy_token)
    add_token_script(Token("ISCHARACTER"), ischaracter_token)
    add_token_script(Token("TARGET"), target_token)
    add_token_script(Token("TARGET"), target_token)
    add_token_script(Token("CHECKED"), checked_token)
    add_token_script(Token("TARGETCOUNT"), targetcount_token)
    add_token_script(Token("EACHTARGET"), each_target)
    add_token_script(Token("DEALT"), dealt_token)
    add_token_script(Token("OWNER"), owner_token)
    add_token_script(Token("CHECKACTION"), checkaction_token)
    add_token_script(Token("WOUNDS"), wounds_token_dual)
    add_token_script(Token("GETWOUND"), getwound_token)
    add_token_script(Token("NORMALWOUNDS"), wounds_token_dual)
    add_token_script(Token("INJURIES"), injuries_token)
    for variable in variables:
        add_token_script(Token(variable), variable_token(variable))
    for counter in counters:
        add_token_script(Token(counter), playerstat_token(counter))
        add_token_script(Token("PAY" + counter), paystat_token(counter))
        add_token_script(Token("PAYX" + counter), payxstat_token(counter))
        add_token_script(Token("REDUCECOST" + counter), reducecoststat_token(counter))
        add_token_script(Token("GAIN" + counter), gainstat_token(counter))
        add_token_script(Token("LOSE" + counter), losestat_token(counter))
        add_token_script(Token("SET" + counter), setstat_token(counter))
    for deal_type in ["DEAL", "DEALONLY", "DEALALWAYS", "DEALALWAYSONLY"]:
        def deal_with(deal_type):
            return lambda current_state, current_token: deal(current_state, current_token, deal_type=deal_type)
        add_token_script(Token(deal_type), deal_with(deal_type))

def defer_til_end(current_state, deferred_call):
    current_defers = current_state.get("deferred", [])
    current_defers.append(deferred_call)
    current_state["deferred"] = current_defers

def add_event(current_state, event_type, event_value):
    current_events = current_state.get("events", [])
    current_events.append((event_type, event_value))
    current_state["events"] = current_events
    
def card_owner(card):
    controller = card.controller
    for card in table:
        if card.Type == "Class" and card.controller == controller:
            return card
    else:
        raise Exception("Card %s's own has no Class in play!" % (card.name, ))
    
def owner_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("OWNER must be list head.")
    card = get_value_from(current_state, current_token[1])
    if type(card) is Card:
        return card_owner(card)
    elif type(card) is tuple and card[0] == "WOUND":
        return card[1]
    
def played_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("PLAYED must be list head.")
    if len(current_token) == 1:
        card = get_value_from(current_state, Token("THIS"))
    else:
        card = get_value_from(current_state, current_token[1])
    return card.group == table
    
def variable_token(singleton):
    def _actual_token(current_state, current_token):
        return current_state[singleton]
    return _actual_token

def owner_this(current_state):
    return get_value_from(current_state, [Token("OWNER"), Token("THIS")])

def checkaction_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("CHECKACTION must be list head.")
    type_matches = current_state["TYPE"] == get_value_from(current_state, current_token[1])
    subtype_matches = current_state["SUBTYPE"] == get_value_from(current_state, current_token[2])
    return type_matches and subtype_matches

if __name__ == "__main__":
    from targetting import *
    from wounds import *
    from counters import *
    setupTokens()