ANY = "ANY"
# Deal damage event format (deal_type, (target, wound_type, wound_count))
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

variables = ["THIS", "CHARACTER"]
card_values = ["TYPE", "SUBTYPE"]
counters = ["HEALTH", "MANA", "SUBTERFUGE", "STAMINA"]
status_counter_id = "00000000-0000-0000-0000-000000000001"

def setupTokens():
    notify("Setting up scripting tokens.")
    add_token_script(Token("GETTARGET"), gettarget_token_dual)
    add_token_script(Token("GETTARGETS"), gettarget_token_dual)
    add_token_script(Token("TARGETCOUNT"), targetcount_token)
    add_token_script(Token("ISENEMY"), isenemy_token)
    add_token_script(Token("ISTARGET"), is_target_token)
    add_token_script(Token("GETENEMY"), getenemy_token)
    add_token_script(Token("ISCHARACTER"), ischaracter_token)
    add_token_script(Token("GETCHARACTER"), getcharacter_token)
    
    add_token_script(Token("ISATTACK"), is_attack_token)
    add_token_script(Token("ISSPELL"), is_spell_token)
    add_token_script(Token("ISPLAYINGCARD"), is_playing_card_token)
    add_token_script(Token("EACHTARGET"), each_target)
    add_token_script(Token("BLOCKDRAW"), block_draw_token)
    add_token_script(Token("DRAW"), draw_token)
    add_token_script(Token("RETREAT"), retreat_token)
    add_token_script(Token("PUNCH"), punch_token)
    add_token_script(Token("PAYDISCARD"), pay_discard_token)
    add_token_script(Token("FORCEDISCARD"), force_discard_token)
    add_token_script(Token("CONSTANT"), constant_token)
    add_token_script(Token("DISCARD"), discard_token)
    add_token_script(Token("ONTURNSTART"), on_turn_start_token)
    add_token_script(Token("ONTURNEND"), on_turn_end_token)
    
    # Variables and references
    add_token_script(Token("CHOOSEX"), choosex_token)
    add_token_script(Token("CHOOSE"), choose_token)
    add_token_script(Token("TARGET"), target_token)
    add_token_script(Token("OWNER"), owner_token)
    add_token_script(Token("CHECKED"), checked_token)
    add_token_script(Token("CHECKACTION"), checkaction_token)
    for variable in variables:
        add_token_script(Token(variable), variable_token(variable))
    for card_value in card_values:
        add_token_script(Token(card_value), card_value_token(card_value))
    
    # Counters and markers
    add_token_script(Token("WOUNDS"), wounds_token_dual)
    add_token_script(Token("NORMALWOUNDS"), wounds_token_dual)
    add_token_script(Token("CHOOSENORMALWOUND"), choose_normal_wound_token)
    add_token_script(Token("GETWOUND"), getwound_token)
    add_token_script(Token("STATUS"), status_token)
    add_token_script(Token("GAINSTATUS"), gain_status_token)
    add_token_script(Token("LOSESTATUS"), lose_status_token)
    for counter in counters:
        add_token_script(Token(counter), playerstat_token(counter))
        add_token_script(Token("GAIN" + counter), gainstat_token(counter))
        if counter != "HEALTH":
            add_token_script(Token("PAY" + counter), paystat_token(counter))
            add_token_script(Token("PAYX" + counter), payxstat_token(counter))
            add_token_script(Token("REDUCECOST" + counter), reducecoststat_token(counter))
            add_token_script(Token("LOSE" + counter), losestat_token(counter))
            add_token_script(Token("SET" + counter), setstat_token(counter))
        
    # Wound manipulation and injures
    add_token_script(Token("DEALT"), dealt_token)
    add_token_script(Token("DEALEXTRA"), deal_extra)
    add_token_script(Token("CONVERTINJURY"), convert_injury_token)
    add_token_script(Token("PREVENT"), prevent_token)
    add_token_script(Token("INJURE"), injure_token)
    add_token_script(Token("REMOVENORMALWOUNDS"), remove_normal_wounds_token)
    add_token_script(Token("CURE"), cure_token)
    add_token_script(Token("CURED"), cured_token)
    add_token_script(Token("INJURIES"), injuries_token)
    add_token_script(Token("THISTURN"), this_turn_token)
    for deal_type in ["DEAL", "DEALONLY", "DEALALWAYS", "DEALALWAYSONLY", "TAKEWOUNDS"]:
        def deal_with(deal_type):
            return token_func(3, 4)(lambda current_state, current_token: deal(current_state, current_token, deal_type=deal_type))
        add_token_script(Token(deal_type), deal_with(deal_type))

def defer_til_end(current_state, deferred_call):
    current_defers = current_state.get("deferred", [])
    current_defers.append(deferred_call)
    current_state["deferred"] = current_defers

def add_event(current_state, event_type, event_value):
    current_events = current_state.get("events", [])
    current_events.append((event_type, event_value))
    current_state["events"] = current_events

def my_class(myself):
    for card in table:
        if card.Type == "Class" and card.controller == myself:
            return card
    else:
        raise Exception("%s's has no Class in play!" % (myself.name, ))

def group_owner(group):
    controller = group.controller
    for card in table:
        if card.Type == "Class" and card.controller == controller:
            return card
    else:
        raise Exception("Group %s's own has no Class in play!" % (group.name, ))

def card_owner(card):
    controller = card.controller
    for card in table:
        if card.Type == "Class" and card.controller == controller:
            return card
    else:
        raise Exception("Card %s's own has no Class in play!" % (card.name, ))
    
@token_func(2, 2)
def owner_token(current_state, current_token):
    card = get_value_from(current_state, current_token[1])
    if type(card) is Card:
        return card_owner(card)
    elif type(card) is tuple and card[0] == "WOUND":
        return card[1]
    
@token_func(1, 2)
def played_token(current_state, current_token):
    if len(current_token) == 1:
        card = get_value_from(current_state, Token("THIS"))
    else:
        card = get_value_from(current_state, current_token[1])
    return card.group == table
    
def variable_token(singleton):
    @token_func(0, 0)
    def _actual_token(current_state, current_token):
        return current_state.get(singleton, None)
    return _actual_token
    
def card_value_token(singleton):
    @token_func(0, 2)
    def _actual_token(current_state, current_token):
        if type(current_token) is not list:
            return current_state[singleton]
        else:
            target = get_value_from(current_state, current_token[1])
            if singleton == "TYPE":
                if type(target) is Card:
                    return target.Type
                elif type(target) is tuple:
                    return target[2]
            elif singleton == "SUBTYPE":
                return target.Subtype
            else:
                raise Exception("Invalid card value script: %s" % singleton)
    return _actual_token

def owner_this(current_state):
    this = get_value_from(current_state, Token("THIS"))
    if this is not None:
        return get_value_from(current_state, [Token("OWNER"), this])
    else:
        return my_class(me)

@token_func(3, 3)
def checkaction_token(current_state, current_token):
    type_matches = current_state["TYPE"] == get_value_from(current_state, current_token[1])
    subtype_matches = current_state["SUBTYPE"] == get_value_from(current_state, current_token[2])
    return type_matches and subtype_matches

@token_func(1, 2)
def constant_token(current_state, current_token):
    constants = current_state.get("constants", [])
    if len(current_token) == 1:
        constants.append(get_value_from(current_state, Token("THIS")))
    else:
        constants.append(get_value_from(current_state, current_token[1]))
    current_state["constants"] = constants

def is_discarded(current_state, checked_card):
    return checked_card in current_state.get("discards", [])

def discard_card_in_state(current_state, discarded):
    discards = current_state.get("discards", [])
    discards.append(discarded)
    current_state["discards"] = discards

@token_func(1, 2)
def discard_token(current_state, current_token):
    if len(current_token) == 1:
        discarded = get_value_from(current_state, Token("THIS"))
    else:
        discarded = get_value_from(current_state, current_token[1])
    discard_card_in_state(current_state, discarded)

@token_func(1, 3)
def draw_token(current_state, current_token):
    if len(current_token) == 1:
        player = owner_this(current_state).controller
        draw_count = 1
    elif len(current_token) == 2:
        player = owner_this(current_state).controller
        draw_count = get_value_from(current_state, current_token[1])
    else:
        player = get_value_from(current_state, current_token[1]).controller
        draw_count = get_value_from(current_state, current_token[2])
    return draw_for_state(current_state, player, draw_count)

@token_func(1, 3)
def block_draw_token(current_state, current_token):
    if len(current_token) == 1:
        player = owner_this(current_state).controller
        draw_count = 1
    elif len(current_token) == 2:
        player = owner_this(current_state).controller
        draw_count = get_value_from(current_state, current_token[1])
    else:
        player = get_value_from(current_state, current_token[1]).controller
        draw_count = get_value_from(current_state, current_token[2])
    current_state["block_draw"] = current_state.get("block_draw", 0) + draw_count
    
@token_func(1, 1)
def retreat_token(current_state, current_token):
    retreater = owner_this(current_state).controller
    retreats = current_state.get("retreat", [])
    retreats.append(retreater)
    current_state["retreat"] = retreats
    draw_for_state(current_state, retreater, 4)
    
@token_func(1, 1)
def punch_token(current_state, current_token):
    puncher = owner_this(current_state)
    if get_value_from(current_state, [Token("THISTURN"), [Token("EQUAL"), Token("SUBTYPE"), "Punch"]]):
        abort(current_state, "You may not punch again this turn.")
    get_value_from(current_state, [Token("GETENEMY")])
    get_value_from(current_state, [Token("PAYSTAMINA"), 1])
    get_value_from(current_state, [Token("DEAL"), 1, "Standard", Token("TARGET")])
    
def draw_for_state(current_state, player, draw_count):
    blocked = current_state.get("block_draw", 0)
    if blocked:
        blocked -= draw_count
        current_state["block_draw"] = blocked
    else:
        drawn_count = current_state.get("drawn_count", 0)
        drawn_cards = current_state.get("drawn_cards", [])
        for _ in range(draw_count):
            drawn_cards.append((player, player.piles["Deck"][drawn_count]))
            drawn_count += 1
        current_state["drawn_cards"] = drawn_cards
        current_state["drawn_count"] = drawn_count
        return drawn_cards
    
@token_func(2, 3)
def pay_discard_token(current_state, current_token):
    if len(current_token) == 2:
        player = owner_this(current_state).controller
        discard_count = get_value_from(current_state, current_token[1])
    else:
        player = get_value_from(current_state, current_token[1]).controller
        discard_count = get_value_from(current_state, current_token[2])
    player_hand = player.hand
    choices = []
    choice_cards = []
    for card in player_hand:
        if not is_discarded(current_state, card):
            choices.append(card.name)
            choice_cards.append(card)
    colorList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel"]
    picked = askChoice("Which card will you discard?", choices, colorList, customButtons=customButtons)
    if picked <= 0:
        abort(current_state, "Cancelled discard choice.")
    else:
        discard_card_in_state(current_state, choice_cards[picked - discard_count])
    
@token_func(2, 3)
def force_discard_token(current_state, current_token):
    if len(current_token) == 2:
        player = owner_this(current_state).controller
        discard_count = get_value_from(current_state, current_token[1])
    else:
        player = get_value_from(current_state, current_token[1]).controller
        discard_count = get_value_from(current_state, current_token[2])
    player_hand = player.hand
    choice_cards = []
    for card in player_hand:
        if not is_discarded(current_state, card):
            choice_cards.append(card)
    if len(choice_cards) != 0:
        discarded = rnd(0, len(choice_cards) - discard_count)
        discard_card_in_state(current_state, discarded)
        return discarded
    else:
        return None

def hasStatus(target, status):
    return target.markers[(status, status_counter_id)] != 0

@token_func(2, 3)
def status_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        status = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        status = get_value_from(current_state, current_token[2])
    counter_status = hasStatus(target, status)
    return counter_status

def addStatus(target, status):
    target.markers[status, status_counter_id] = 1

@token_func(2, 3)
def gain_status_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        status = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        status = get_value_from(current_state, current_token[2])
    statuses = current_state.get("status", [])
    statuses.append((target, status, True))
    current_state["status"] = statuses


def loseStatus(target, status):
    target.markers[status, status_counter_id] = 0

@token_func(2, 3)
def lose_status_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        status = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        status = get_value_from(current_state, current_token[2])
    statuses = current_state.get("status", [])
    statuses.append((target, status, False))
    current_state["status"] = statuses
    
@token_func(2, 2)
def this_turn_token(current_state, current_token):
    validator = current_token[1]
#     so_far_this_turn = current_state.get("this_turn", [])
    so_far_this_turn = this_turn
    for action in so_far_this_turn:
        dummy_state = current_state.copy()
        dummy_state.update(action)
        value = get_value_from(dummy_state, validator)
        if value:
            return value
    return False

this_turn = []
def clear_turn():
    global this_turn
    this_turn = []

def add_action_this_turn(action):
    global this_turn
    this_turn.append(action)

@token_func(2, 3)
def on_turn_start_token(current_state, current_token):
    if len(current_token) == 3:
        x = current_token[1]
        y = current_token[2]
    else:
        x = owner_this(current_state)
        y = current_token[1]
    return get_value_from(current_state, [Token("ON"), [Token("AND"), [Token("EQUAL"), Token("TYPE"), "TurnStart"], [Token("EQUAL"), Token("CHARACTER"), x]], y])

@token_func(2, 3)
def on_turn_end_token(current_state, current_token):
    if len(current_token) == 3:
        x = current_token[1]
        y = current_token[2]
    else:
        x = owner_this(current_state)
        y = current_token[1]
    return get_value_from(current_state, [Token("ON"), [Token("AND"), [Token("EQUAL"), Token("TYPE"), "TurnEnd"], [Token("EQUAL"), Token("CHARACTER"), x]], y])

@token_func(1, 1)
def is_playing_card_token(current_state, current_token):
    return current_state.has_key("PLAYEDCARD")

@token_func(1, 1)
def is_attack_token(current_state, current_token):
    return current_state["TYPE"] == "Attack" or current_state["TYPE"] == "Punch"

@token_func(1, 1)
def is_spell_token(current_state, current_token):
    return current_state["TYPE"] == "Spell"

if __name__ == "__main__":
    from targetting import *
    from wounds import *
    from counters import *
    setupTokens()