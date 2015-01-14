flipBoard = -1
flipModX = -Card.width()
flipModY = -Card.height()
MAX_HAND_SIZE = 7

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
            draw(me.piles["Deck"])
    elif me.Stamina <= 0 and card.Type != "Item":
        notify("Are you sure it's your turn?")
        if not confirm("You're trying to play a card with no Stamina. Is it your turn?"):
            return "ABORT"
    card.moveToTable(getCardX(card), getCardY(card))
    
def useCard(card, x = 0, y = 0):
    if card.Script != "":
        pass
    
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