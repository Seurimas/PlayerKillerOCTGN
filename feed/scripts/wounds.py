try:
    from script_base import add_token_script, follow_script, get_value_from, Token, token_func
    from game_scripts import defer_til_end, add_event, owner_this
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

wounds = ("Standard",
          "Shadow",
          "Burn",
          "Frost",
          "Mortal")

wounds_markers = {"Standard":("Standard Wound", "7ae6b4f2-afee-423a-bc18-70a236b41000"),
         "Burn":("Burn Wound", "7ae6b4f2-afee-423a-bc18-70a236b41001"),
         "Frost":("Frost Wound", "7ae6b4f2-afee-423a-bc18-70a236b41002"),
         "Mortal":("Mortal Wound", "7ae6b4f2-afee-423a-bc18-70a236b41003"),
         "Shadow":("Shadow Wound", "7ae6b4f2-afee-423a-bc18-70a236b41004")
         }

PREVENTABLE = ["DEAL", "DEALONLY", "DEALEXTRA"]
DEALT = PREVENTABLE + ["DEALALWAYS", "DEALALWAYSONLY", "DEALEXTRAALWAYS"]
CURED = ["CURE"]
REMOVED = ["CURE", "REMOVENORMALWOUNDS", "AFFLICTED", "CONVERTAFFLICTION"]
PREVENT = "PREVENT"

if __name__ == "__main__":
    print "Running tests."

def add_wounds(current_state, target, new_wounds, deal_type="TAKEWOUNDS"):
    current_targets = current_state.get("dealt", {})
    target_wounds = current_targets.get(target, [])
    for old_wounds in target_wounds:
        if old_wounds[0] == new_wounds[0]:
            old_wounds[1] += new_wounds[1]
            break
    else:
        target_wounds.append(list(new_wounds))
    current_targets[target] = target_wounds
    current_state["dealt"] = current_targets
    add_event(current_state, deal_type, (target, new_wounds[0], new_wounds[1]))

def remove_wounds(current_state, target, removed_wounds, remove_type="REMOVE", extra=None):
    current_targets = current_state.get("remove", {})
    target_wounds = current_targets.get(target, [])
    for old_wounds in target_wounds:
        if wounds_equal(old_wounds[0], removed_wounds[0]) and extra == None:
            old_wounds[1] += removed_wounds[1]
            break
    else:
        if extra is None:
            target_wounds.append(list(removed_wounds))
        else:
            target_wounds.append(list(removed_wounds) + [extra])
    current_targets[target] = target_wounds
    current_state["remove"] = current_targets
    if extra is None:
        event = (target, removed_wounds[0], removed_wounds[1])
    else:
        event = (target, removed_wounds[0], removed_wounds[1], extra)
    add_event(current_state, remove_type, event)
    
def prevent_wounds(current_state, target, wound_type, wound_count):
    actually_prevented = min(get_wounds_dealt(current_state, target, wound_type, preventable_only=True), wound_count)
    current_targets = current_state.get("dealt", {})
    target_wounds = current_targets.get(target, [])
    for old_wounds in target_wounds:
        if old_wounds[0] == wound_type:
            old_wounds[1] -= actually_prevented
    current_targets[target] = target_wounds
    current_state["dealt"] = current_targets
    add_event(current_state, PREVENT, (target, wound_type, actually_prevented))

@token_func(3, 4)
def prevent_token(current_state, current_token):
    if len(current_token) == 3:
        target = owner_this(current_state)
        wound_count = current_token[1]
        wound_type = current_token[2]
    else:
        target = get_value_from(current_state, current_token[1])
        wound_count = get_value_from(current_state, current_token[2])
        wound_type = get_value_from(current_state, current_token[3])
    prevent_wounds(current_state, target, wound_type, wound_count)

def wounds_equal(wound1, wound2):
    return (type(wound1) == type(wound2) and wound1 == wound2) or wound1 == Token("ANY") or wound2 == Token("ANY")

def get_wounds_dealt(current_state, target, wound_type, preventable_only=False, include_prevented=False):
    count = 0
    events = current_state.get("events", [])
    for event in events:
        if event[0] not in DEALT:
            continue # Not a dealt-wounds event.
        elif (not preventable_only) or event[0] in PREVENTABLE:
            if (target == Token("ANY") or event[1][0] == target) and wounds_equal(event[1][1], wound_type):
                count += event[1][2]
        elif (not include_prevented) and event[0] == PREVENT:
            if (target == Token("ANY") or event[1][0] == target) and wounds_equal(event[1][1], wound_type):
                count -= event[1][2]
    return count
    
def get_wounds_removed(current_state, target, wound_type, cured_only=False):
    count = 0
    events = current_state.get("events", [])
    for event in events:
        if not event[0] in REMOVED or (cured_only and event[0] not in CURED):
            continue
        if not event[1][0] == target:
            continue
        if not wounds_equal(event[1][1], wound_type):
            continue
        count += event[1][2]
    return count

@token_func(2, 3)
def dealt_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    return get_wounds_dealt(current_state, target, wound_type, preventable_only=False, include_prevented=False)

@token_func(2, 3)
def cured_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    return get_wounds_removed(current_state, target, wound_type, cured_only=True)

@token_func(2, 2)
def each_cured_token(current_state, current_token):
    wound_validator = current_token[1]
    events = current_state.get("events", [])
    for event in events:
        if not event[0] in REMOVED:
            continue
        if type(event[1][1]) is Card: # Affliction
            current_state["CHECKED"] = event[1][1]
        elif type(event[1][1]) is str: # Wound
            current_state["CHECKED"] = ("WOUND", event[1][0], event[1][1])
        get_value_from(current_state, wound_validator)

def deal(current_state, current_token, deal_type="DEAL"):
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    if deal_type == "TAKEWOUNDS" and len(current_token) == 3:
        target = owner_this(current_state)
    else:
        target = get_value_from(current_state, current_token[3])
    add_wounds(current_state, target, (wound_type, wound_count), deal_type=deal_type)
    
@token_func(3, 3)
def deal_extra(current_state, current_token):
    def deals_extra(event):
        return event[0] in ["DEAL"]
    def deals_extra_always(event):
        return event[0] in ["DEALALWAYS"]
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
#     def deal_extra_at_end(current_state):
    events_which_deal_extra = filter(deals_extra, current_state.get("events", []))
    events_which_deal_extra_always = filter(deals_extra_always, current_state.get("events", []))
    for valid_target in set([event[1][0] for event in events_which_deal_extra]):
        add_wounds(current_state, valid_target, (wound_type, wound_count), deal_type="DEALEXTRA")
    for valid_target in set([event[1][0] for event in events_which_deal_extra_always]):
        add_wounds(current_state, valid_target, (wound_type, wound_count), deal_type="DEALEXTRAALWAYS")
#     defer_til_end(current_state, deal_extra_at_end)

@token_func(2, 3)
def wounds_token_dual(current_state, current_token):
    target = None
    wound_type = None
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    normal_wounds = get_normal_wounds_count(target, wound_type, current_state=current_state)
    if current_token[0] == Token("WOUNDS"):
        afflictions = get_afflictions_count(wound_type, target)
    elif current_token[0] == Token("NORMALWOUNDS"):
        afflictions = 0
    return normal_wounds + afflictions

@token_func(3, 3)
def getwound_token(current_state, current_token):
    target = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    if target.markers[wounds_markers[wound_type]] != 0:
        return ("WOUND", target, wound_type)
    else:
        return None
    
@token_func(3, 4)
def afflict_token_dual(current_state, current_token):
    if len(current_token) == 3:
        target_wound = get_value_from(current_state, current_token[1])
        affliction = get_value_from(current_state, current_token[2])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
        affliction = get_value_from(current_state, current_token[3])
        if target.markers[wounds_markers[wound_type]] != 0:
            target_wound = ("WOUND", target, wound_type)
        else:
            abort(current_state, "Target has no %s wounds" % wound_type)
            return
    if type(target_wound) is not tuple:
        raise Exception("Expected wound representation, not %s" % (type(target_wound)))
    else:
        if current_token[0].name == "AFFLICT" and get_afflictions_count(affliction, target_wound[1], current_state):
            abort(current_state, "That target already has %s" % affliction.name)
        if type(target_wound) is tuple:
            remove_wounds(current_state, target_wound[1], (target_wound[2], 1), "AFFLICTED")
            add_wounds(current_state, target_wound[1], (affliction, 1), "AFFLICT")
        elif type(target_wound) is Card:
            add_wounds(current_state, target_wound, (affliction, 1), "AFFLICT")
    
@token_func(3, 3)
def convert_affliction_token(current_state, current_token):
    affliction = get_value_from(current_state, current_token[1])
    target_wound_type = get_value_from(current_state, current_token[2])
    remove_wounds(current_state, card_owner(affliction), (affliction, 1), "CONVERTAFFLICTION", extra=target_wound_type)
    
def get_normal_wounds_count(target, wound_type, current_state=None):
    if current_state is not None:
        just_removed = get_wounds_removed(current_state, target, wound_type)
    else:
        just_removed = 0
    return target.markers[wounds_markers[wound_type]] - just_removed

def get_afflictions_count(wound_type, target, current_state=None):
    afflictions = 0
    for card in table:
        if card.Type == "Affliction" and card.controller == target.controller:
            if type(wound_type) is str and card.Subtype == wound_type:
                if current_state == None or not get_wounds_removed(current_state, target, card):
                    afflictions += 1
            elif type(wound_type) is Card and wound_type.name == card.name:
                if current_state == None or not get_wounds_removed(current_state, target, card):
                    afflictions += 1
    return afflictions

@token_func(2, 3)
def afflictions_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    afflictions = get_afflictions_count(wound_type, target)
    return afflictions

@token_func(2, 4)
def remove_normal_wounds_token(current_state, current_token):
    if len(current_token) == 2:
        wound = get_value_from(current_state, current_token[1])
        target = wound[1]
        wound_type = wound[2]
        wound_count = 1
    elif len(current_token) == 3:
        target = owner_this(current_state)
        wound_count = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_count = get_value_from(current_state, current_token[2])
        wound_type = get_value_from(current_state, current_token[3])
    remove_wounds(current_state, target, (wound_type, wound_count), "REMOVENORMALWOUNDS")

@token_func(1, 2)
def is_normal_wound_token(current_state, current_token):
    if len(current_token) == 2:
        wound = get_value_from(current_state, current_token[1])
    else:
        wound = get_value_from(current_state, Token("CHECKED"))
    if type(wound) is tuple and len(wound) == 3 and wound[0] == "WOUND" and type(wound[2]) is str:
        return True
    else:
        return False

@token_func(3, 4)
def choose_normal_wound_token(current_state, current_token):
    if len(current_token) == 3:
        prompt = get_value_from(current_state, current_token[1])
        target = owner_this(current_state)
        wound_validator = current_token[2]
    else:
        prompt = get_value_from(current_state, current_token[1])
        target = get_value_from(current_state, current_token[2])
        wound_validator = current_token[3]
    choices = []
    wound_choices = []
    for wound_type in wounds:
        normal_count = get_normal_wounds_count(target, wound_type, current_state=current_state)
        if normal_count != 0:
            current_state["CHECKED"] = ("WOUND", target, wound_type)
            if get_value_from(current_state, wound_validator):
                choices.append("Normal %s Wound on %s (%s)" % (wound_type, target.name, target.controller.name))
                wound_choices.append(wound_type)
    colorsList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel"]
    picked = askChoice(prompt, choices, colorsList, customButtons=customButtons)
    if picked == -1 or picked == 0:
        abort(current_state, "Cancelled picking cured wounds.")
    else:
        return ("WOUND", target, wound_choices[picked - 1])

@token_func(2, 3)
def cure_token(current_state, current_token):
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_validator = current_token[1]
    else:
        target = get_value_from(current_state, current_token[1])
        wound_validator = current_token[2]
    choices = []
    wound_choices = []
    for wound_type in wounds:
        normal_count = get_normal_wounds_count(target, wound_type, current_state=current_state)
        if normal_count != 0:
            current_state["CHECKED"] = ("WOUND", target, wound_type)
            if get_value_from(current_state, wound_validator):
                choices.append("Normal %s Wound on %s (%s)" % (wound_type, target.name, target.controller.name))
                wound_choices.append(wound_type)
#         elif get_afflictions_count(wound_type, target, current_state) != 0:
        if get_afflictions_count(wound_type, target, current_state) != 0:
            for card in table:
                current_state["CHECKED"] = card
                if card.Type == "Affliction" and card.controller == target.controller and get_value_from(current_state, wound_validator):
                    if get_afflictions_count(card, target, current_state) != 0: # Make sure we haven't already cured the affliction.
                        choices.append("%s on %s" % (card.name, card.controller.name))
                        wound_choices.append(card)
    colorsList = ["#FFFFFF" for _ in choices]
    customButtons = ["Cancel", "Finish"]
    picked = askChoice("Which wound would you like to cure?", choices, colorsList, customButtons=customButtons)
    if picked == -1 or picked == 0:
        current_state["FAIL"] = "Cancelled picking cured wounds."
    elif picked == -2:
        return False
    else:
        remove_wounds(current_state, target, (wound_choices[picked - 1], 1), remove_type="CURE")
        return True

if __name__ == "__main__":
    for deal_type in ["DEAL", "DEALONLY", "DEALALWAYS", "DEALALWAYSONLY"]:
        def deal_with(deal_type):
            return lambda current_state, current_token: deal(current_state, current_token, deal_type=deal_type)
        add_token_script(Token(deal_type), deal_with(deal_type))
    test_val = follow_script({}, [[Token("DEAL"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEAL", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 1)
    deal_extra(test_val, [Token("DEALEXTRA"), 1, "Standard"])
    assert(test_val == {"dealt": {"Someone":[["Standard", 2]]},  "events": [("DEAL", ("Someone", "Standard", 1)),
                                                                            ("DEALEXTRA", ("Someone", "Standard", 1)),
                                                                            ]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 2)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 2)
    
    test_val = follow_script({}, [[Token("DEALONLY"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 1)
    deal_extra(test_val, [Token("DEALEXTRA"), 1, "Standard"])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 1)
    
    test_val = follow_script({}, [[Token("DEALALWAYS"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYS", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
    deal_extra(test_val, [Token("DEALEXTRA"), 1, "Standard"])
    assert(test_val == {"dealt": {"Someone":[["Standard", 2]]},  "events": [("DEALALWAYS", ("Someone", "Standard", 1)),
                                                                            ("DEALEXTRAALWAYS", ("Someone", "Standard", 1)),
                                                                            ]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 2)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
    
    test_val = follow_script({}, [[Token("DEALALWAYSONLY"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYSONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
    deal_extra(test_val, [Token("DEALEXTRA"), 1, "Standard"])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYSONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
