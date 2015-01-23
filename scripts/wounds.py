try:
    from script_base import add_token_script, follow_script, get_value_from, Token
    from game_scripts import defer_til_end, add_event, owner_this
except:
    pass

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
CURED = ["CURE"]
REMOVED = ["CURE", "REMOVENORMALWOUNDS", "INJURED", "CONVERTINJURY"]
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
        if old_wounds[0] == removed_wounds[0]:
            old_wounds[1] += removed_wounds[1]
            break
    else:
        target_wounds.append(list(new_wounds))
    current_targets[target] = target_wounds
    current_state["remove"] = current_targets
    if extra is None:
        event = (target, removed_wounds[0], removed_wounds[1])
    else:
        event = (target, removed_wounds[0], removed_wounds[1], extra)
    add_event(current_state, remove_type, event)
    
def prevent_wounds(current_state, target, wound_type, wound_count):
    actually_prevented = max(get_wounds_dealt(current_state, target, wound_type, preventable_only=True), wound_count)
    current_targets = current_state.get("dealt", {})
    target_wounds = current_targets.get(target, [])
    for old_wounds in target_wounds:
        if old_wounds[0] == wound_type:
            old_wounds[1] -= actually_prevented
    current_targets[target] = target_wounds
    current_state["dealt"] = current_targets
    add_event(current_state, PREVENT, (target, wound_type, actually_prevented))
    
def get_wounds_dealt(current_state, target, wound_type, preventable_only=False, include_prevented=False):
    count = 0
    events = current_state.get("events", [])
    for event in events:
        if (not preventable_only) or event[0] in PREVENTABLE:
            if event[1][0] == target and event[1][1] == wound_type:
                count += event[1][2]
        elif (not include_prevented) and event[0] == PREVENT:
            if event[1][0] == target and event[1][1] == wound_type:
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
        if not event[1][1] == wound_type:
            continue
        count += event[1][2]
    return count

def dealt_token(current_state, current_token):
    check_token_list(current_token, 2, 3)
    if len(current_state) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    return get_wounds_dealt(current_state, target, wound_type, preventable_only=False, include_prevented=False)

def deal(current_state, current_token, deal_type="DEAL"):
    check_token_list(current_token, 4, 4)
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    target = get_value_from(current_state, current_token[3])
    add_wounds(current_state, target, (wound_type, wound_count), deal_type=deal_type)
    
def deal_extra(current_state, current_token):
    def deals_extra(event):
        return event[0] in ["DEAL", "DEALALWAYS"]
    check_token_list(current_token, 3, 3)
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
#     def deal_extra_at_end(current_state):
    events_which_deal_extra = filter(lambda event: deals_extra(event), current_state.get("events", []))
    for valid_target in set([event[1][0] for event in events_which_deal_extra]):
        add_wounds(current_state, valid_target, (wound_type, wound_count), deal_type="DEALEXTRA")
#     defer_til_end(current_state, deal_extra_at_end)

def wounds_token_dual(current_state, current_token):
    check_token_list(current_token, 2, 3)
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
        injuries = get_injuries_count(wound_type, target)
    elif current_token[0] == Token("NORMALWOUNDS"):
        injuries = 0
    return normal_wounds + injuries

def getwound_token(current_state, current_token):
    check_token_list(current_token, 3, 3)
    target = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    if target.markers[wounds_markers[wound_type]] != 0:
        return ("WOUND", target, wound_type)
    else:
        return None
    
def injure_token():
    check_token_list(current_token, 3, 3)
    target_wound = get_value_from(current_state, current_token[1])
    injury = get_value_from(current_state, current_token[2])
    if type(target_wound) is not tuple:
        raise Exception("Expected wound representation, not %s" % (type(target_wound)))
    else:
        remove_wounds(current_state, target, (target_wound[2], 1), "INJURED")
        add_wounds(current_state, target, (injury, 1), "INJURE")
    
def convert_injury_token():
    check_token_list(current_token, 3, 3)
    injury = get_value_from(current_state, current_token[1])
    target_wound_type = get_value_from(current_state, current_token[2])
    remove_wounds(current_state, target, (injury, 1), "CONVERTINJURY", extra=target_wound_type)
    
def get_normal_wounds_count(target, wound_type, current_state=None):
    if current_state is not None:
        just_removed = get_wounds_removed(current_state, target, wound_type)
    else:
        just_removed = 0
    return target.markers[wounds_markers[wound_type]] - just_removed

def get_injuries_count(wound_type, target, current_state=None):
    injuries = 0
    for card in table:
        if card.Type == "Injury" and card.controller == target.controller:
            if type(wound_type) is str and card.Subtype == wound_type:
                if current_state == None or not get_wounds_removed(current_state, target, card):
                    injuries += 1
            elif type(wound_type) is Card and wound_type.name == card.name:
                if current_state == None or not get_wounds_removed(current_state, target, card):
                    injuries += 1
    return injuries

def injuries_token(current_state, current_token):
    check_token_list(current_token, 2, 3)
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    injuries = get_injuries_count(wound_type, target)
    return injuries

def remove_normal_wounds_token(current_state, current_token):
    check_token_list(current_token, 3, 4)
    if len(current_token) == 3:
        target = owner_this(current_state)
        wound_count = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_count = get_value_from(current_state, current_token[2])
        wound_type = get_value_from(current_state, current_token[3])
    remove_wounds(current_state, target, (wound_type, wound_count), "REMOVENORMALWOUNDS")

def is_normal_wound_token(current_state, current_token):
    check_token_list(current_token, 1, 2)
    if len(current_token) == 2:
        wound = get_value_from(current_state, current_token[1])
    else:
        wound = get_value_from(current_state, Token("CHECKED"))
    if type(wound) is tuple and len(wound) == 3 and wound[0] == "WOUND" and type(wound[2]) is str:
        return True
    else:
        return False

def cure_token(current_state, current_token):
    check_token_list(current_token, 2, 3)
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_validator = current_token[1]
    else:
        target = get_value_from(current_state, current_token[1])
        wound_validator = current_state, current_token[2]
    choices = []
    wound_choices = []
    for wound_type in wounds:
        normal_count = get_normal_wounds_count(target, wound_type, current_state=current_state)
        if normal_count != 0:
            current_state["CHECKED"] = ("WOUND", target, wound_type)
            if get_value_from(current_state, wound_validator):
                choices.append("Normal %s Wound on %s (%s)" % (wound_type, target.name, target.controller.name))
                wound_choices.append(wound_type)
        elif get_injuries_count(wound_type, target, current_state) != 0:
            for card in table:
                current_state["CHECKED"] = card
                if card.Type == "Injury" and card.controller == target.controller and get_value_from(current_state, wound_validator):
                    if get_injuries_count(card, target, current_state) != 0: # Make sure we haven't already cured the injury.
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
        remove_wounds(current_state, target, (wound_choices[picked - 1], 0), remove_type="CURE")
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
                                                                            ("DEALEXTRA", ("Someone", "Standard", 1)),
                                                                            ]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 2)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 1)
    
    test_val = follow_script({}, [[Token("DEALALWAYSONLY"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYSONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
    deal_extra(test_val, [Token("DEALEXTRA"), 1, "Standard"])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYSONLY", ("Someone", "Standard", 1))]})
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=False, include_prevented=False) == 1)
    assert(get_wounds_dealt(test_val, "Someone", "Standard", preventable_only=True, include_prevented=False) == 0)
