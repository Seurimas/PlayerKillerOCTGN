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
    
def check_card(card, x=0, y=0):
    errors = check_script(card.Play_Script)
    errors.extend(check_script(card.Constant_Script))
    errors.extend(check_script(card.Use_Script))
    if len(errors) != 0:
        whisper("Errors in %s:" % (card.name))
        for error in errors:
            whisper(error)
    
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
    
set_sizes = [0x1a, # Rogue card count
             0x2b, # Mage card count
             0x1b, # Fighter card count
             0x0e] # General card count

def check_scripts(group, x=0, y=0):
    mute()
    base_set_guid = "75f0e3d1-7f7d-4c15-abec-4b7424e"
    for set_i in range(4):
        set_guid = base_set_guid + str(set_i)
        for card in range(set_sizes[set_i] + 1):
            card_model = "%s%04x" % (set_guid, card)
            card = table.create(card_model, 0, 0, quantity=1, persist = False)
            if not card:
                raise Exception("Could not create card %s" % card_model)
            check_card(card)
            card.delete()
            
            
"""[DISCARD, THIS], [REMOVENORMALWOUNDS, [CHOOSENORMALWOUND, "Which wound are you converting?", [OWNER, THIS], [NOT, [EQUAL, TYPE, "Standard"]]]], [TAKEWOUNDS, 1, "Standard"]"""