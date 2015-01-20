flipBoard = -1
flipModX = -Card.width()
flipModY = -Card.height()
MAX_HAND_SIZE = 7

post_priorities = [0, 1, 2, 3]
pre_priorities = [-2, -1]
all_priorities = pre_priorities + post_priorities

def checkDeck(player, groups):
    mute()
    if player != me: return
    notify("Checking deck of " + me.name)

desiredLocations = {"Class":(0, 0),
                    "Item":(75, 0),
                    "Injury":(0, 100),
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

def checkMovedCard(player, card, fromGroup, toGroup,
                   oldIndex, index,
                   oldX, oldY, x, y,
                   isScriptMove):
    if isScriptMove:
        return
    
def draw(group):
    if me.Stamina > 0 or confirm("You're trying to draw with no Stamina. Is it your turn?"):
        card = group.top()
        card.moveTo(me.hand)

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

def createDummyCard(card):
    card = table.create(card.model, getCardX(card), getCardY(card))
#     card.moveToTable(getCardX(card), getCardY(card))
    mark_card_temporary(card)

def retreat(group):
    character = group_owner(group)
    state = {"CHARACTER": character,
             "TYPE": "Retreat",
             "SUBTYPE": ""}
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        return
    state = follow_script(state, [Token("RETREAT")])
    if type(state) is str:
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities)
        if type(state) is str:
            return

def applyWithPriorities(state, priorities):
    for priority in priorities:
        for modifier_card in table:
            if type(state) is dict:
                state = applyCard(priority, modifier_card, state)
                if should_abort(state):
                    notify("%s caused failure: %s" % (modifier_card.name, state["FAIL"]))
                    state = state["FAIL"]
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
    state = applyWithPriorities(state, pre_priorities)
    if type(state) is str:
        return
    if card.group == me.hand:
        pay_stat("STAMINA", 1, character, state)
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
        notify(str(base_state))
        notify("Failed: " + state)
    else:
        state = applyWithPriorities(state, post_priorities)
        if type(state) is str:
            return
        if card.group == me.hand:
            createDummyCard(card)
            card.moveTo(me.piles["Discard"])
        notify("%s" % state)

def replace_this(state, card, types=False):
    old_state = {}
    old_state["THIS"] = state["THIS"]
    state["THIS"] = card
    if types:
        old_state["TYPE"] = state["TYPE"]
        old_state["SUBTYPE"] = state["SUBTYPE"]
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
                notify("Applying %s with priority %s [%s]" % (card.name, priority, effect[1:]))
                old_state = replace_this(current_state, card)
                result = follow_script(current_state, effect[1:])
                notify("%s" % result) # FIXME: Need to actually set the result and state to correct values.
                current_state.update(old_state)
                return result
        else:
            return current_state
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
    notify("Start of " + me.name + "'s turn!")
    me.Stamina = 3
    
def mark_card_temporary(card):
    card.highlight = "#00FFFF"
    
def is_card_temporary(card):
    return card.highlight is not None and card.highlight.upper() == "#00FFFF"
    
def clear_table_for_me(table):
    mute()
    for card in table:
        if is_card_temporary(card):
            if card.controller == me:
                card.moveTo(me.piles['Discard'])
            else:
                notify(card.name + " is not my card")
        else:
            notify(card.name + " is not temporary")
    
def eot(table):
    if me.Stamina != 0:
        whisper("You must end your turn with 0 stamina.")
        return
    notify("End of " + me.name + "'s turn!")
    if len(me.hand) > MAX_HAND_SIZE:
        notify(me.name + " needs to discard down to " + str(MAX_HAND_SIZE))
    clear_table_for_me(table)