flipBoard = -1
flipModX = -Card.width()
flipModY = -Card.height()
MAX_HAND_SIZE = 7

post_priorities = [0, 1, 2, 3]
pre_priorities = [-3, -2, -1]
all_priorities = pre_priorities + post_priorities

def checkDeck(player, groups):
    mute()
    if player != me: return
    notify("Checking deck of " + me.name)
    current_state = {"TYPE":"DeckLoad"}
    for card in me.hand:
        if card.Type == "Item":
            card.moveToBottom(me.piles["Backpack"])
        elif card.Type == "Class":
            script_tokens, remainder = get_list_from(card.Play_Script)
            current_state = follow_script(current_state, script_tokens)
            if type(current_state) is str:
                notify("Checking deck of %s failed because: %s" % (me.name, current_state))
                return
            break
    else:
        notify("Checked deck of %s failed because: No Class card in hand." % (me.name, ))
    for card in me.piles["Backpack"]:
        if card.Type != "Item":
            card.moveToBottom(me.piles["Deck"])
        else:
            script_tokens, remainder = get_list_from(card.Play_Script)
            current_state = follow_script(current_state, script_tokens)
            if type(current_state) is str:
                notify("Checking deck of %s failed because: %s" % (me.name, current_state))
                return
    if current_state["WEIGHT"] < 0:
        notify("Checked deck of %s failed because: %s over weight!" % (me.name, -current_state["WEIGHT"]))
    notify("%s" % (current_state))
    activate_state_change(current_state)
    type_counts = {}
    for card in me.piles["Deck"]:
        try:
            type_counts[card.Type] += 1
        except KeyError:
            type_counts[card.Type] = 1
    for card_type in type_counts:
        whisper("Your deck contains %d %s" % (type_counts[card_type], card_type))

desiredLocations = {"Class":(0, 0),
                    "Item":(75, 0),
                    "Affliction":(0, 100),
                    "Tactic":(0, 200),
                    "Attack":(0, 300),
                    "Spell":(0, 400)}

def cardCount(player, type):
    acc = 0
    for card in table:
        if card.owner == player and card.Type == type:
            acc += 1
    return acc

def getCardX(card):
    return (desiredLocations.get(card.Type)[0] + cardCount(me, card.Type) * card.width()) * flipBoard + flipModX

def getCardY(card):
    return desiredLocations.get(card.Type)[1] * flipBoard + flipModY

def rearrange_afflictions(player):
    aff_i = 1
    if player != me: return
    for card in table:
        if card.Type == "Affliction" and card.controller == player:
            x = -aff_i * card.width() * flipBoard + flipModX
            y = flipModY
            card.moveToTable(x, y)
            aff_i += 1
            
def rearrange_items(player):
    item_i = 1
    for card in table:
        if card.Type == "Item" and card.controller == player:
            x = (desiredLocations["Item"][0] + item_i * card.width()) * flipBoard + flipModX
            y = flipModY
            card.moveToTable(x, y)
            item_i += 1

def checkMovedCard(player, card, fromGroup, toGroup,
                   oldIndex, index,
                   oldX, oldY, x, y,
                   isScriptMove):
    if isScriptMove:
        return
    
def draw(group):
    character = my_class(me)
    state = {"CHARACTER": character,
             "TYPE": "Draw",
             "SUBTYPE": ""}
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        return
    state = follow_script(state, [[Token("PAYSTAMINA"), 1], [Token("DRAW"), 1]])
    if type(state) is str:
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities)
        if type(state) is str:
            return
    activate_state_change(state, None)

def shuffleDeck(group):
    group.shuffle()

def chkTwoSided():
    mute()
    whisper("Welcome to Player Killer.")
    if not table.isTwoSided(): 
        information("Note: This game is intended for two-sided board play.")
    global flipBoard, flipModX, flipModY
    whisper("Checking sides!")
    if not me.hasInvertedTable():
        flipBoard = 1
        flipModX = 0
        flipModY = 0
        whisper("You are the non-flipped side!")
    else:
        whisper("You are the flipped side!")
    
def playCard(card, x = 0, y = 0):
    if card.Type == "Class":
        card.moveToTable(getCardX(card), getCardY(card))
        for card in me.piles["Backpack"]:
            playCard(card)
        me.piles["Deck"].shuffle()
        for _ in range(5):
            drawn = me.piles["Deck"].top()
            drawn.moveTo(me.hand)
    elif card.Type != "Item":
        if me.Stamina <= 0:
            notify("Are you sure it's your turn?")
            if not confirm("You're trying to play a card with no Stamina. Is it your turn?"):
                return "ABORT"
#         card.moveToTable(getCardX(card), getCardY(card))
        useCard(card)
    else:
        card.moveToTable(getCardX(card), getCardY(card))
        rearrange_items(card.controller)

def createDummyCard(card):
    card = table.create(card.model, getCardX(card), getCardY(card))
#     card.moveToTable(getCardX(card), getCardY(card))
    mark_card_temporary(card)
    return card

def retreat(group):
    character = my_class(me)
    state = {"CHARACTER": character,
             "TYPE": "Retreat",
             "SUBTYPE": ""}
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        return
    state = follow_script(state, [[Token("RETREAT")]])
    if type(state) is str:
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities)
        if type(state) is str:
            return
    activate_state_change(state, None)

def handPunch(group):
    character = my_class(me)
    state = {"CHARACTER": character,
             "TYPE": "Attack",
             "SUBTYPE": "Punch"}
    state = applyWithPriorities(state, pre_priorities, ignore_weapons=True)
    if type(state) is str:
        return
    state = follow_script(state, [[Token("PUNCH")]])
    if type(state) is str:
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities, ignore_weapons=True)
        if type(state) is str:
            return
    activate_state_change(state, None)

def applyWithPriorities(state, priorities, ignore_weapons=False):
    for priority in priorities:
        for modifier_card in table:
            if is_card_temporary(modifier_card):
                continue
            if ignore_weapons and modifier_card.Subtype == "Weapon":
                continue
            if type(state) is dict:
                state = applyCard(priority, modifier_card, state)
                if type(state) is str:
                    notify("%s caused failure: %s" % (modifier_card.name, state))
    return state

def useCard(card, x = 0, y = 0):
    if type(card.Play_Script) is str:
        script_tokens, remainder = get_list_from(card.Play_Script)
        card.Play_Script = script_tokens
    if type(card.Use_Script) is str:
        script_tokens, remainder = get_list_from(card.Use_Script)
        card.Use_Script = script_tokens
    character = card_owner(card)
    state = {"CHARACTER": character,
             "THIS": card,
             "TYPE": card.Type,
             "SUBTYPE": card.Subtype}
    base_state = state
    if card.group == me.hand:
        state["PLAYEDCARD"] = card
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        return
    if card.group == me.hand:
        pay_stat("STAMINA", 1, character, state)
        discard_card_in_state(state, card)
        if len(card.Play_Script) != 0:
            state = follow_script(state, card.Play_Script)
        else:
            notify("This card does not have a play script. Handle interactions manually as necessary.")
    elif card.group == table:
        if len(card.Use_Script) != 0:
            state = follow_script(state, card.Use_Script)
        else:
            notify("This card does not have a use script. Handle interactions manually as necessary.")
    else:
        state = state
    if type(state) is str:
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities)
        if type(state) is str:
            return
        if card.group == me.hand:
            activate_state_change(state, createDummyCard(card))
#             card.moveTo(me.piles["Discard"])
        else:
            activate_state_change(state)

def replace_this(state, card, types=False):
    old_state = {}
    if state.has_key("THIS"):
        old_state["THIS"] = state["THIS"]
    else:
        old_state["THIS"] = None
    state["THIS"] = card
    if types:
        old_state["TYPE"] = state["TYPE"]
        old_state["SUBTYPE"] = state["SUBTYPE"]
        old_state["PLAYEDCARD"] = state["PLAYEDCARD"]
        state["PLAYEDCARD"] = card
        state["TYPE"] = card.Type
        state["SUBTYPE"] = card.Subtype
    return old_state

def applyCard(priority, card, current_state):
    if type(card.Constant_Script) is str:
        script_tokens, remainder = get_list_from(card.Constant_Script)
        card.Constant_Script = script_tokens
    if len(card.Constant_Script) != 0:
        for effect in card.Constant_Script:
            if effect[0] == priority:
                old_state = replace_this(current_state, card)
                current_state = follow_script(current_state, effect[1:])
                if type(current_state) is str:
                    return current_state # Fail early.
                current_state.update(old_state)
                # Not returning here after all, because a card may have multiple effects with the same priority.
        else:
            return current_state # We'll get here if we don't fail.
    else:
        return current_state
    
def addMarker(cards, x = 0, y = 0): # A simple function to manually add any of the available markers.
    marker, quantity = askMarker() # Ask the player how many of the same type they want.
    if quantity == 0: return
    for card in cards: # Then go through their cards and add those markers to each.
        card.markers[marker] += quantity
        notify("{} adds {} {} ({}) counter to {}.".format(me, quantity, marker[0], marker[1], card))
        
def checkStatusCard(card, x = 0, y = 0):
    status = askString("What status would you like to check?", "STEALTH")
    if hasStatus(card, status):
        notify("%s has status [%s]" % (card.name, status))
        
def addStatusCard(card, x = 0, y = 0):
    status = askString("What status would you like to add?", "STEALTH")
    addStatus(card, status)
        
def loseStatusCard(card, x = 0, y = 0):
    status = askString("What status would you like to remove?", "STEALTH")
    loseStatus(card, status)
        
def sot(table):
    for player in getPlayers():
        if player.Stamina != 0:
            whisper(player.name + "'s turn has not ended. All players must be at 0 stamina.")
            return
    if not me.isActivePlayer:
        me.setActivePlayer()
    clear_turn()
    notify("Start of " + me.name + "'s turn!")
    state = {"CHARACTER": my_class(me),
             "TYPE": "TurnStart",
             "SUBTYPE": ""}
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        notify("Failed: " + state)
        return
    gain_stat("STAMINA", 3, state["CHARACTER"], state)
    draw_for_state(state, me, 1)
    state = applyWithPriorities(state, post_priorities)
    if type(state) is str:
        notify("Failed: " + state)
        return
    activate_state_change(state)
    
def mark_card_temporary(card):
    card.highlight = "#0000FF"
    
def mark_card_affliction(card):
    card.highlight = "#FF0000"
    
def mark_card_constant(card):
    card.highlight = "#00FF00"
    
def is_card_temporary(card):
    return card.highlight is not None and card.highlight.upper() == "#0000FF"
    
def clear_table_for_me(table):
    mute()
    for card in table:
        if is_card_temporary(card):
            if card.controller == me:
                card.moveTo(me.piles['Discard'])
    
def eot(table):
    if me.Stamina != 0:
        whisper("You must end your turn with 0 stamina.")
        return
    state = {"CHARACTER": my_class(me),
             "TYPE": "TurnEnd",
             "SUBTYPE": ""}
    notify("%s is controlled by %s" % (state["CHARACTER"], state["CHARACTER"].controller))
    state = applyWithPriorities(state, all_priorities)
    if type(state) is str:
        notify("Failed: " + state)
        return
    activate_state_change(state)
    notify("End of " + me.name + "'s turn!")
    if len(players) != 1:
        players[1].setActivePlayer()
    if len(me.hand) > MAX_HAND_SIZE:
        notify(me.name + " needs to discard down to " + str(MAX_HAND_SIZE))
    clear_table_for_me(table)