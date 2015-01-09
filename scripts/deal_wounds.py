from script_base import add_token_script, follow_script, get_value_from, Token
from game_scripts import defer_til_end, add_event, add_wounds
wounds = ("Standard",
          "Shadow",
          "Burn",
          "Frost",
          "Mortal")

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
    add_event(current_state, deal_type, (target, wound_type, wound_count))
    
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
    
def get_wounds_dealt(current_state, target, type, preventable_only=False, include_prevented=False):
    count = 0
    for event in events:
        if preventable_only and event[0] in PREVENTABLE:
            if event[1][0] == target and event[1][1] == type:
                count += event[1][2]
        elif (not include_prevented) and event[0] == PREVENT:
            if event[1][0] == target and event[1][1] == type:
                count -= event[1][2]
    return count

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
    if not type(current_token) is list or len(current_tokens) != 3:
        raise Exception("DEALEXTRA requires 2 arguments: Number of wounds, type of wounds.")
    wound_count = get_value_from(current_state, current_token[1])
    wound_type = get_value_from(current_state, current_token[2])
    def deal_extra_at_end(current_state):
        events_which_deal_extra = filter(current_state.get("events", []), lambda event: deals_extra(event))
        for event in events_which_deal_extra:
            target = event[1][0]
            add_wounds(current_state, target, (wound_type, wound_count))
    defer_til_end(current_state, deal_extra_at_end)
    
for deal_type in ["DEAL", "DEALONLY", "DEALALWAYS", "DEALALWAYSONLY"]:
    def deal_with(deal_type):
        return lambda current_state, current_token: deal(current_state, current_token, deal_type=deal_type)
    add_token_script(Token(deal_type), deal_with(deal_type))

if __name__ == "__main__":
    test_val = follow_script({}, [[Token("DEAL"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEAL", ("Someone", "Standard", 1))]})
    test_val = follow_script({}, [[Token("DEALONLY"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALONLY", ("Someone", "Standard", 1))]})
    test_val = follow_script({}, [[Token("DEALALWAYS"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYS", ("Someone", "Standard", 1))]})
    test_val = follow_script({}, [[Token("DEALALWAYSONLY"), 1, "Standard", "Someone"]])
    assert(test_val == {"dealt": {"Someone":[["Standard", 1]]},  "events": [("DEALALWAYSONLY", ("Someone", "Standard", 1))]})
