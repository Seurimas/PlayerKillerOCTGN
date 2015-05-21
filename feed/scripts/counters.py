try:
    from token_func import script_base
except:
    def token_func(min_len, max_len):
        def actual_decorator(func):
            def decorated_function(current_state, current_token):
                check_token_list(current_token, min_len, max_len)
                return func(current_state, current_token)
            decorated_function.list_head_min = min_len
            decorated_function.list_head_max = max_len
            return decorated_function
        return actual_decorator

def get_stat_value(target, statname):
    if statname.capitalize() != "Stamina" or marker_count(target, "Max Stamina") == 0: # Not stamina. Not a pet with stamina.
        return target.controller.counters[statname.capitalize()].value
    else:
        return get_stamina_count_marker(target)

def get_paid_value(target, statname, current_state):
    return current_state.get("pay", {}).get(target, {}).get(statname.capitalize(), 0)

def overpaid(target, statname, current_state):
    if target is not None and get_stat_value(target, statname) >= get_paid_value(target, statname, current_state):
        return False
    else:
        return True

def stat_token(statname):
    @token_func(1, 2)
    def _actual_token(current_state, current_token):
        if len(current_token) == 1:
            target = owner_this(current_state)
        else:
            target = get_value_from(current_state, current_token[1])
        if target.Type == "Class":
            stat_value = get_stat_value(target, statname)
        elif is_card_npc(target):
            stat_value = get_stamina_count_marker(target)
        return stat_value
    return _actual_token

def payxstat_token(statname):
    @token_func(1, 2)
    def _actual_token(current_state, current_token):
        if len(current_token) == 1:
            target = owner_this(current_state)
        else:
            target = get_value_from(current_state, current_token[1])
        max_paid = get_stat_value(target, statname) - get_paid_value(target, statname, current_state)
        paid = choosex_token(current_state, [Token("CHOOSEX"), "How much %s is X? (Max: %d)" % (statname.capitalize(), max_paid),
                                             0, max_paid])
        pay_stat(statname, paid, target, current_state)
        return paid
    return _actual_token

def paystat_token(statname):
    @token_func(2, 3)
    def _actual_token(current_state, current_token):
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        pay_stat(statname, amount, target, current_state)
        if overpaid(target, statname, current_state):
            abort(current_state, "%s cannot pay %d %s (only have %d)" % (target.name, amount, statname.capitalize(), get_stat_value(target, statname)))
    return _actual_token

def reducecoststat_token(statname):
    @token_func(2, 3)
    def _actual_token(current_state, current_token):
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        reducecost_stat(statname, amount, target, current_state)
    return _actual_token

def pay_stat(statname, amount, target, current_state):
    current_payments = current_state.get("pay", {})
    target_payments = current_payments.get(target, {})
    stat_payment = target_payments.get(statname.capitalize(), 0)
    stat_payment += amount
    target_payments[statname.capitalize()] = stat_payment
    current_payments[target] = target_payments
    current_state["pay"] = current_payments

def reducecost_stat(statname, amount, target, current_state):
    pay_stat(statname, -amount, target, current_state)

def setstat_token(statname):
    @token_func(2, 3)
    def _actual_token(current_state, current_token):
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        set_stat(statname, amount, target, current_state)
    return _actual_token

def set_stat(statname, amount, target, current_state):
    current_sets = current_state.get("set_stat", {})
    target_sets = current_sets.get(target, {})
    target_sets[statname.capitalize()] = amount
    current_sets[target] = target_sets
    current_state["set_stat"] = current_sets

def gainstat_token(statname):
    @token_func(2, 3)
    def _actual_token(current_state, current_token):
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        gain_stat(statname, amount, target, current_state)
    return _actual_token

def losestat_token(statname):
    @token_func(2, 3)
    def _actual_token(current_state, current_token):
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        lose_stat(statname, amount, target, current_state)
    return _actual_token

def gain_stat(statname, amount, target, current_state):
    current_sets = current_state.get("gain_stat", {})
    target_sets = current_sets.get(target, {})
    current_gain = target_sets.get(statname.capitalize(), 0)
    current_gain += amount
    target_sets[statname.capitalize()] = current_gain
    current_sets[target] = target_sets
    current_state["gain_stat"] = current_sets
    
def lose_stat(statname, amount, target, current_state):
    gain_stat(statname, amount, target, current_state)
    
def gain_stat_counter(target, statname, value):
    target.controller.counters[statname].value += value
    notify("%s (%s) gains %d %s" % (target.name, target.controller.name, value, statname))
    
def set_stat_counter(target, statname, value):
    target.controller.counters[statname].value = value
    notify("%s %s set to %d" % (target.controller.name, statname, value))
    
def pay_stat_counter(target, statname, value):
    if value > 0:
        target.controller.counters[statname].value -= value
        
