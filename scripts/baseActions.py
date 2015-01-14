flipBoard = -1
flipModX = -Card.width()
flipModY = -Card.height()
MAX_HAND_SIZE = 7

post_priorities = [0, 1, 2, 3]
pre_priorities = [-2, -1]

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
    elif me.Stamina <= 0 and card.Type != "Item":
        notify("Are you sure it's your turn?")
        if not confirm("You're trying to play a card with no Stamina. Is it your turn?"):
            return "ABORT"
        else:
            useCard(card)
    else:
        card.moveToTable(getCardX(card), getCardY(card))
    
def useCard(card, x = 0, y = 0):
    if type(card.Script) is str:
        script_tokens, remainder = get_list_from(card.Script)
        notify("Script: [%s] - Tokens: [%s] - Remainder: [%s]" % (card.Script, script_tokens, remainder) )
        card.Script = script_tokens
    character = card_owner(card)
    state = {"CHARACTER": character,
             "THIS": card,
             "TYPE": card.Type,
             "SUBTYPE": card.Subtype}
    for priority in pre_priorities:
        for modifier_card in table:
            state = applyCard(priority, modifier_card, state)
            if should_abort(state):
                notify("%s caused failure: %s" % (modifier_card.name, state["FAIL"]))
    if card.group == me.hand:
        pay_stat("STAMINA", 1, character, state)
    if len(card.Script) != 0:
        state = follow_script(state, card.Script)
    else:
        state = state
    if type(state) is str:
        notify("Failed: " + state)
    else:
        for priority in post_priorities:
            for modifier_card in table:
                state = applyCard(priority, modifier_card, state)
                if should_abort(state):
                    notify("%s caused failure: %s" % (modifier_card.name, state["FAIL"]))
        if card.group == me.hand:
            card.moveToTable(getCardX(card), getCardY(card))
        notify("%s" % state)

def applyCard(priority, card, current_state):
    if type(card.Constant) is str:
        script_tokens = get_list_from(card.Constant)[0]
        card.Constant = script_tokens
    if len(card.Constant) != 0:
        for effect in card.Constant:
            if effect[0] == priority:
                return follow_script(current_state, card.Constant[1:])
        else:
            return current_state
    else:
        return current_state

def printWounds(card, x = 0, y = 0):
    notify(str(get_value_from({"THIS": card}, [Token("WOUNDS"), "Standard"])))
def printInjuries(card, x = 0, y = 0):
    notify(str(get_value_from({"THIS": card}, [Token("INJURIES"), "Standard"])))
def printWoundsBurn(card, x = 0, y = 0):
    notify(str(get_value_from({"THIS": card}, [Token("WOUNDS"), "Burn"])))
def printInjuriesBurn(card, x = 0, y = 0):
    notify(str(get_value_from({"THIS": card}, [Token("INJURIES"), "Burn"])))
    
def addMarker(cards, x = 0, y = 0): # A simple function to manually add any of the available markers.
    marker, quantity = askMarker() # Ask the player how many of the same type they want.
    if quantity == 0: return
    for card in cards: # Then go through their cards and add those markers to each.
        card.markers[marker] += quantity
        notify("{} adds {} {} counter to {}.".format(me, quantity, marker[0], card))
        
def sot(table):
    for player in getPlayers():
        if player.Stamina != 0:
            whisper(player.name + "'s turn has not ended. All players must be at 0 stamina.")
            return
    notify("Start of " + me.name + "'s turn!")
    me.Stamina = 3
    
def eot(table):
    if me.Stamina != 0:
        whisper("You must end your turn with 0 stamina.")
        return
    notify("End of " + me.name + "'s turn!")
    if len(me.hand) > MAX_HAND_SIZE:
        notify(me.name + "needs to discard down to " + MAX_HAND_SIZE)
    for card in table:
        if card.Type != "Class" and card.Type != "Item":
            card.moveTo(me.piles['Discard'])