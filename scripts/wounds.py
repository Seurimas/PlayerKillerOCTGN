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
PREVENT = "PREVENT"

if __name__ == "__main__":
    print "Running tests."

def add_wounds(current_state, target, new_wounds, deal_type="TAKE"):
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

def dealt_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("DEALT must be list head.")
    elif len(current_state) < 2 or len(current_token) > 3:
        raise Exception("DEALT requires 1 or 2 arguments: optional target, wound type")
    if len(current_state) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    

def deal(current_state, current_token, deal_type="DEAL"):
    if not type(current_token) is list or len(current_token) != 4:
        raise Exception(deal_type + " requires 3 arguments: Number of wounds, type of wounds, target.")
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    target = get_value_from(current_state, current_token[3])
    add_wounds(current_state, target, (wound_type, wound_count), deal_type=deal_type)
    
def deal_extra(current_state, current_token):
    def deals_extra(event):
        return event[0] in ["DEAL", "DEALALWAYS"]
    if not type(current_token) is list or len(current_token) != 3:
        raise Exception("DEALEXTRA requires 2 arguments: Number of wounds, type of wounds.")
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
#     def deal_extra_at_end(current_state):
    events_which_deal_extra = filter(lambda event: deals_extra(event), current_state.get("events", []))
    for event in events_which_deal_extra:
        target = event[1][0]
        add_wounds(current_state, target, (wound_type, wound_count), deal_type="DEALEXTRA")
#     defer_til_end(current_state, deal_extra_at_end)

def wounds_token_dual(current_state, current_token):
    if type(current_token) is not list:
        raise Exception(current_token + " must be list head.")
    target = None
    wound_type = None
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    normal_wounds = target.markers[wounds_markers[wound_type]]
    if current_token[0] == Token("WOUNDS"):
        injuries = get_injuries(wound_type, target)
    elif current_token[0] == Token("NORMALWOUNDS"):
        injuries = 0
    return normal_wounds + injuries

def getwound_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("GETWOUND must be list head.")
    target = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    if target.markers[wounds_markers[wound_type]] != 0:
        return ("WOUND", target, wound_type)
    else:
        return None

def get_injuries(wound_type, target):
    injuries = 0
    for card in table:
        if card.Type == "Injury" and card.controller == target.controller:
            if type(wound_type) is str and card.Subtype == wound_type:
                injuries += 1
            elif type(wound_type) is Card and wound_type.name == card.name:
                injuries += 1
    
    return injuries

def injuries_token(current_state, current_token):
    if type(current_token) is not list:
        raise Exception("INJURIES must be list head.")
    if len(current_token) == 2:
        target = owner_this(current_state)
        wound_type = get_value_from(current_state, current_token[1])
    else:
        target = get_value_from(current_state, current_token[1])
        wound_type = get_value_from(current_state, current_token[2])
    injuries = get_injuries(wound_type, target)
    return injuries

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
