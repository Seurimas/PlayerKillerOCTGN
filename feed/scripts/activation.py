change_handlers = []

def setup_state_changes():
    change_handlers.append(handle_retreat) # Done!
    change_handlers.append(handle_damage) # Done!
    change_handlers.append(handle_cure) # Done!
    change_handlers.append(handle_afflict) # Done!
    change_handlers.append(handle_draw) # Done!
    change_handlers.append(handle_discard) # Done!
    change_handlers.append(handle_constant) # Done!
    change_handlers.append(handle_pets) # Done!
    change_handlers.append(handle_counters) # Done!
    change_handlers.append(handle_status) # Done!
    change_handlers.append(handle_turn_state) # Done!
    change_handlers.append(handle_gain_health) # Done!
    change_handlers.append(handle_refresh_stamina) # Done!
    whisper("Setting up activation scripts!")

def activate_state_change(current_state, dummy_card=None):
    if type(current_state) is dict:
        for change_handler in change_handlers:
            change_handler(current_state, dummy_card)
        
def handle_turn_state(current_state, dummy_card):
    add_action_this_turn(current_state)
    
def handle_gain_health(current_state, dummy_card):
    if current_state.has_key("GAINHEALTH"):
        for target, value in current_state["GAINHEALTH"].items():
            add_health_marker(target, value)
    
def handle_retreat(current_state, dummy_card):
    mute()
    for retreater in current_state.get("retreat", []):
        if retreater.isActivePlayer:
            retreater.Stamina = 0
            eot(table)
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
        
def remove_stat(target, statname, value):
    if statname != "Stamina" or marker_count(target, "Max Stamina") == 0: # Not stamina. Not a pet with stamina.
        pay_stat_counter(target, statname, value)
    else:
        remove_stamina_marker(target, value)    
    
def handle_counters(current_state, dummy_card): # Useless dummy card.
    mute()
    for target, counters in current_state.get("gain_stat", {}).items():
        for statname, value in counters.items():
            gain_stat_counter(target, statname, value)
    for target, counters in current_state.get("pay", {}).items():
        for statname, value in counters.items():
            remove_stat(target, statname, value)
            notify("%s (%s) pays %d %s" % (target.name, target.controller.name, value, statname))
    for target, counters in current_state.get("set_stat", {}).items():
        for statname, value in counters.items():
            set_stat_counter(target, statname, value)
                
def handle_afflict(current_state, dummy_card): # We want the dummy card!
    mute()
    for target, wound_sets in current_state.get("dealt", {}).items():
        for wounds in wound_sets:
            wound_type = wounds[0]
            always_one = wounds[1]
            if type(wound_type) is Card: # Affliction
                if wound_type == current_state["THIS"]:
                    wound_type = dummy_card # Swap out the dummy card.
                mark_card_affliction(wound_type)
                wound_type.setController(target.controller)
                if is_card_npc(target):
                    set_npc_owner(wound_type, target)
                remove_health_marker(target, 1)
                remoteCall(target.controller, "rearrange_afflictions", [target.controller])
                notify("%s received %s" % (target.controller.name, wound_type))
                
def handle_constant(current_state, dummy_card): # We want the dummy card!
    mute()
    for constant in current_state.get("constants", []):
        notify("%s remains in play" % (constant.name))
        if constant == current_state["THIS"]:
            constant = dummy_card # Swap out the dummy card.
        mark_card_constant(constant)
                
def handle_pets(current_state, dummy_card): # We want the dummy card!
    mute()
    for pet, health, max_stamina in current_state.get("pets", []):
        if pet == current_state["THIS"]:
            pet = dummy_card # Swap out the dummy card.
        mark_card_pet(pet)
        add_health_marker(pet, health)
        add_max_stamina_marker(pet, max_stamina)
        refresh_stamina_marker(pet)
        
def handle_refresh_stamina(current_state, dummy_card):
    mute()
    for pet in current_state.get("refresh_stamina", []):
        refresh_stamina_marker(pet)
        
def handle_damage(current_state, dummy_card): # Dummy card useless here.
    mute()
    for target, wound_sets in current_state.get("dealt", {}).items():
        for wounds in wound_sets:
            wound_type = wounds[0]
            wound_count = wounds[1]
            if type(wound_type) is str: # Normal wound
                add_wound_marker(target, wound_type, wound_count)
            notify("%s received %s %s" % (target.controller.name, wound_count, wound_type))

def handle_cure(current_state, dummy_card): # Dummy card useless here.
    mute()
    for target, wound_sets in current_state.get("remove", {}).items():
        for wounds in wound_sets:
            if len(wounds) == 2: # Normal removal
                wound_type = wounds[0]
                wound_count = wounds[1]
                if type(wound_type) is str: # Normal wound
                    remove_wound_marker(target, wound_type, wound_count)
                    notify("%s cured %s %s" % (target.controller.name, wound_count, wound_type))
                elif type(wound_type) is Card:
                    notify("%s cured %s" % (target.controller.name, wound_type.name))
                    wound_type.moveTo(me.piles["Discard"])
                else:
                    raise Exception("Invalid wound type: %s (%s)" % (wound_type, type(wound_type)))
            else: # ConvertAffliction
                affliction = wounds[0]
                always_one = wounds[1]
                wound_type = wounds[2]
                notify("%s convert %s to a normal %s wound" % (target.controller.name, affliction.name, wound_type))
                add_wound_marker(target, wound_type, always_one)
                if type(affliction) is Card:
                    remove_affliction(affliction)
                else:
                    raise Exception("Invalid affliction type: %s (%s)" % (affliction, type(affliction)))

def handle_draw(current_state, dummy_card): # Ignore the dummy card still.
    mute()
    for drawn_card in current_state.get("drawn_cards", []):
        player = drawn_card[0]
        card = drawn_card[1]
        card.moveTo(player.hand)
        for p in players[1:]:
            remoteCall(p, "whisper", "%s drew a card." % (player.name, ))
        whisper("You drew {}.".format(card))

def handle_discard(current_state, dummy_card):
    mute()
    for discarded in current_state.get("discards", []):
        notify("{} was discarded".format(discarded.name))
        if discarded.Type == "Item":
            discarded.moveTo(discarded.owner.piles["Backpack"])
        else:
            discarded.moveTo(discarded.owner.piles["Discard"])

this_turn = []
def clear_turn():
    global this_turn
    this_turn = []

def add_action_this_turn(action):
    global this_turn
    this_turn.append(action)
    
if __name__ == "__main__":
    setup_state_changes()