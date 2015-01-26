def getPlayScript(card, x=0, y=0):
    notify("%s" % (card.Play_Script, ))
    
def getConstantScript(card, x=0, y=0):
    notify("%s" % (card.Constant_Script, ))
    
def getUseScript(card, x=0, y=0):
    notify("%s" % (card.Use_Script, ))
    
def setPlayScript(card, x=0, y=0):
    card.Play_Script = askString("New script:", "%s" % (card.Play_Script, ))
    
def setConstantScript(card, x=0, y=0):
    card.Constant_Script = askString("New script:", "%s" % (card.Constant_Script, ))
    
def setUseScript(card, x=0, y=0):
    card.Use_Script = askString("New script:", "%s" % (card.Use_Script, ))
    
def feedConstants(card, x=0, y=0):
    state_str = askString("State:", "{}")
    state = eval(state_str)
    state["CHARACTER"] = me
    state["THIS"] = None
    for x in range(-2, 5):
        state = applyCard(x, card, state)
        if type(state) is str:
            whisper("FAILED: %s" % state)
            return
    whisper("Result: %s" % state)