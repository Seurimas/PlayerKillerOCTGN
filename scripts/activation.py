change_handlers = []

def setup_state_changes():
    change_handlers.append(handle_retreat) # Done!
    change_handlers.append(handle_damage) # Done!
    change_handlers.append(handle_cure) # Done!
    change_handlers.append(handle_injure) # Done!
    change_handlers.append(handle_draw) # Done!
    change_handlers.append(handle_discard) # Done!
    change_handlers.append(handle_constant) # Done!
    change_handlers.append(handle_counters) # Done!
    change_handlers.append(handle_status) # Done!
    change_handlers.append(handle_turn_state) # Done!
    notify("Setting up activation scripts!")

def activate_state_change(current_state, dummy_card=None):
    if type(current_state) is dict:
        for change_handler in change_handlers:
            change_handler(current_state, dummy_card)
        
def handle_turn_state(current_state, dummy_card):
    add_action_this_turn(current_state)
    
def handle_retreat(current_state, dummy_card):
    mute()
    for retreater in current_state.get("retreat", []):
        for card in retreater.piles["Discard"]:
            card.moveTo(retreater.piles["Deck"])
        for card in retreater.hand:
            card.moveTo(retreater.piles["Deck"])
        retreater.piles["Deck"].shuffle()
        for card in retreater.piles["Backpack"]:
            playCard(card)
        
def handle_status(current_state, dummy_card): # Dummy card useless here.
    mute()
    for target, status, value in current_state.get("status", []):
        if value:
            addStatus(target, status)
        else:
            loseStatus(target, status)
        notify("%s (%s) %s set to %s" % (target.name, target.controller.name, status, value))
        
def handle_counters(current_state, dummy_card): # Useless dummy card.
    mute()
    for target, counters in current_state.get("gain_stat", {}).items():
        for statname, value in counters.items():
            target.controller.counters[statname].value += value
            notify("%s gains %d %s" % (target.controller.name, value, statname))
    for target, counters in current_state.get("pay", {}).items():
        for statname, value in counters.items():
            if value > 0:
                target.controller.counters[statname].value -= value
                notify("%s pays %d %s" % (target.controller.name, value, statname))
    for target, counters in current_state.get("set_stat", {}).items():
        for statname, value in counters.items():
            target.controller.counters[statname].value = value
            notify("%s %s set to %d" % (target.controller.name, statname, value))
                
def handle_injure(current_state, dummy_card): # We want the dummy card!
    mute()
    for target, wound_sets in current_state.get("dealt", {}).items():
        for wounds in wound_sets:
            wound_type = wounds[0]
            always_one = wounds[1]
            if type(wound_type) is Card: # Injury
                if wound_type == current_state["THIS"]:
                    wound_type = dummy_card # Swap out the dummy card.
                mark_card_injury(wound_type)
                wound_type.setController(target.controller)
                target.controller.counters["Health"].value -= always_one
                notify("%s received %s" % (target.controller.name, wound_type))
                
def handle_constant(current_state, dummy_card): # We want the dummy card!
    mute()
    for constant in current_state.get("constants", []):
        notify("%s remains in play" % (constant.name))
        if constant == current_state["THIS"]:
            constant = dummy_card # Swap out the dummy card.
        mark_card_constant(constant)
        
def handle_damage(current_state, dummy_card): # Dummy card useless here.
    mute()
    for target, wound_sets in current_state.get("dealt", {}).items():
        for wounds in wound_sets:
            wound_type = wounds[0]
            wound_count = wounds[1]
            if type(wound_type) is str: # Normal wound
                target.markers[wounds_markers[wound_type]] += wound_count
                target.controller.counters["Health"].value -= wound_count
            notify("%s received %s %s" % (target.controller.name, wound_count, wound_type))

def handle_cure(current_state, dummy_card): # Dummy card useless here.
    mute()
    for target, wound_sets in current_state.get("remove", {}).items():
        for wounds in wound_sets:
            if len(wounds) == 2: # Normal removal
                wound_type = wounds[0]
                wound_count = wounds[1]
                if type(wound_type) is str: # Normal wound
                    target.markers[wounds_markers[wound_type]] -= wound_count
                    notify("%s lost %s %s" % (target.controller.name, wound_count, wound_type))
                elif type(wound_type) is Card:
                    notify("%s cured %s" % (target.controller.name, wound_type.name))
                    wound_type.moveTo(me.piles["Discard"])
                else:
                    raise Exception("Invalid wound type: %s (%s)" % (wound_type, type(wound_type)))
                target.controller.counters["Health"].value += wound_count
            else: # ConvertInjury
                injury = wounds[0]
                always_one = wounds[1]
                wound_type = wounds[2]
                notify("%s convert %s to a normal %s wound" % (target.controller.name, injury, wound_type))
                if type(injury) is Card:
                    wound_type.moveTo(me.piles["Discard"])
                else:
                    raise Exception("Invalid injury type: %s (%s)" % (wound_type, type(wound_type)))
                target.markers[wounds_markers[wound_type]] += wound_count

def handle_draw(current_state, dummy_card): # Ignore the dummy card still.
    mute()
    for drawn_card in current_state.get("drawn_cards", []):
        player = drawn_card[0]
        card = drawn_card[1]
        card.moveTo(player.hand)
        notify("%s drew a card." % (player.name, ))

def handle_discard(current_state, dummy_card):
    mute()
    for discarded in current_state.get("discards", []):
        notify("%s was discarded" % (discarded.name))
        if discarded.Type == "Item":
            discarded.moveTo(discarded.owner.piles["Backpack"])
        else:
            discarded.moveTo(discarded.owner.piles["Discard"])

if __name__ == "__main__":
    setup_state_changes()