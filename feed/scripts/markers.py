markers = {"Standard":("Standard Wound", "7ae6b4f2-afee-423a-bc18-70a236b41000"),
         "Burn":("Burn Wound", "7ae6b4f2-afee-423a-bc18-70a236b41001"),
         "Frost":("Frost Wound", "7ae6b4f2-afee-423a-bc18-70a236b41002"),
         "Mortal":("Mortal Wound", "7ae6b4f2-afee-423a-bc18-70a236b41003"),
         "Shadow":("Shadow Wound", "7ae6b4f2-afee-423a-bc18-70a236b41004"),
         "Health":("Health", "7ae6b4f2-afee-423a-bc18-70a236b41005"),
         "Max Stamina":("Max Stamina", "7ae6b4f2-afee-423a-bc18-70a236b41006"),
         "Stamina":("Stamina", "7ae6b4f2-afee-423a-bc18-70a236b41007"),
         }

unique_npc_marker_ids = ["10000000-0000-0000-0000-0000000000%02x" % i for i in range(256)]
unique_npc_markers = [("NPC%d" % i, unique_npc_marker_ids[i]) for i in range(len(unique_npc_marker_ids))]
unique_npc_count = 0

def marker_count(target, marker_name):
    return target.markers[markers[marker_name]]

def add_wound_marker(target, wound_type, wound_count):
    target.markers[markers[wound_type]] += wound_count
    remove_health_marker(target, wound_count)

def remove_wound_marker(target, wound_type, wound_count):
    target.markers[markers[wound_type]] -= wound_count
    add_health_marker(target, wound_count)

def add_health_marker(target, value):
    target.markers[markers["Health"]] += value
    if target.Type == "Class":
        target.controller.counters["Health"].value = target.markers[markers["Health"]]
    
def remove_health_marker(target, value):
    target.markers[markers["Health"]] -= value
    if target.Type == "Class":
        target.controller.counters["Health"].value = target.markers[markers["Health"]]

def add_max_stamina_marker(target, value):
    target.markers[markers["Max Stamina"]] += value
    
def refresh_stamina_marker(target):
    target.markers[markers["Stamina"]] = target.markers[markers["Max Stamina"]]
    
def remove_stamina_marker(target, value):
    target.markers[markers["Stamina"]] -= value
    
def get_stamina_count_marker(target):
    return target.markers[markers["Stamina"]]
    
def addStatus(target, status):
    target.markers[status, status_counter_id] = 1

def loseStatus(target, status):
    target.markers[status, status_counter_id] = 0
    
def add_unique_npc_marker(target):
    global unique_npc_count
    target.markers[unique_npc_markers[unique_npc_count]] = 1
    unique_npc_count += 1
    
def set_npc_owner(target, owner):
    for marker in unique_npc_markers:
        if owner.markers[marker] != 0:
            target.markers[marker] = 1
    
def get_npc(marker):
    for card in table:
        if card.markers[marker] != 0 and is_card_npc(card):
            return card
    
def get_npc_owner(card):
    for marker in unique_npc_markers:
        if card.markers[marker] != 0:
            return get_npc(marker)