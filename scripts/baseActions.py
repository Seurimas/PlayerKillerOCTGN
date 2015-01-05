def checkDeck(player, groups):
    mute()
    if player != me: return
    notify("Checking deck of " + me.name)

def chkTwoSided():
    mute()
    notify("Welcome to Player Killer.")
    if not table.isTwoSided(): 
        information("Note: This game is intended for two-sided board play.")
    
def playCard(card, x = 0, y = 0):
    mute()
    notify(card.name)
    notify(card.Description)