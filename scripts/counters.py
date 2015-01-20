def get_counter_value(target, statname):
    return target.controller.__getattr__(statname.capitalize())

def get_paid_value(target, statname, current_state):
    return current_state.get("pay", {}).get(target, {}).get(statname.capitalize(), 0)

def can_pay(target, statname, current_state):
    return get_counter_value(target, statname) >= get_paid_value(target, statname, current_state)

def playerstat_token(statname):
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 1, 2)
        if len(current_token) == 1:
            target = owner_this(current_state)
        else:
            target = get_value_from(current_state, current_token[1])
        counter_value = get_counter_value(target, statname)
        return counter_value
    return _actual_token

def payxstat_token(statname):
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 1, 2)
        if len(current_token) == 1:
            target = owner_this(current_state)
        else:
            target = get_value_from(current_state, current_token[1])
        max_paid = get_counter_value(target, statname) - get_paid_value(target, statname, current_state)
        paid = choosex_token(current_state, [Token("CHOOSEX"), "How much %s is X? (Max: %d)" % (statname.capitalize(), max_paid),
                                             0, max_paid])
        pay_stat(statname, paid, target, current_state)
        return paid
    return _actual_token

def paystat_token(statname):
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 2, 3)
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        pay_stat(statname, amount, target, current_state)
        if not can_pay(target, statname, current_state):
            abort(current_state, "Cannot pay %d %s (only have %d)" % (amount, statname.capitalize(), get_counter_value(target, statname)))
    return _actual_token

def reducecoststat_token(statname):
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 2, 3)
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
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 2, 3)
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
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 2, 3)
        if len(current_token) == 2:
            target = owner_this(current_state)
            amount = get_value_from(current_state, current_token[1])
        else:
            target = get_value_from(current_state, current_token[1])
            amount = get_value_from(current_state, current_token[2])
        gain_stat(statname, amount, target, current_state)
    return _actual_token

def losestat_token(statname):
    def _actual_token(current_state, current_token):
        check_token_list(current_token, 2, 3)
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
    current_state["set_stat"] = current_sets
    
def lose_stat(statname, amount, target, current_state):
    gain_stat(statname, amount, target, current_state)