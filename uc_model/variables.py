import pulp as pp


def power_generated_MW(intervals, units):
    var_power_generated_MW = \
        pp.LpVariable.dicts("Power Generation (i, u)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            cat="Continuous")
    return var_power_generated_MW


def power_generated_segment_MW(intervals, units, segments):
    var_power_generated_segment_MW = \
        pp.LpVariable.dicts("Power Generation Segment (i, u, s)",
                            ((i, u, s) for i in intervals for u in units for s in segments),
                            lowBound=0,
                            cat="Continuous")
    return var_power_generated_segment_MW


def reserve_MW(intervals, units):
    var_reserve_MW = \
        pp.LpVariable.dicts("Reserves (i, u)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            cat="Continuous")
    return var_reserve_MW


def inertia(intervals, units):
    var_inertia_MWsec = \
        pp.LpVariable.dicts("Inertia (i, u)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            cat="Continuous")
    return var_inertia_MWsec


def commitment_status(intervals, units):
    var_commitment_status = \
        pp.LpVariable.dicts("Commitment Status (i,g)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            upBound=1,
                            cat="Binary")
    return var_commitment_status


def start_up_status(intervals, units):
    var_start_up_status = \
        pp.LpVariable.dicts("Start Up Status(i, g)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            upBound=1,
                            cat="Binary")
    return var_start_up_status


def shut_down_status(intervals, units):
    var_shut_down_status = \
        pp.LpVariable.dicts("Shut Down Status(i, g)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            upBound=1,
                            cat="Binary")
    return var_shut_down_status


def unserved_demand_MW(intervals):
    var_unserved_demand_MW = \
        pp.LpVariable.dicts("Unserved Demand i",
                            (i for i in intervals),
                            lowBound=0,
                            cat="Continuous")
    return var_unserved_demand_MW


def unserved_reserve_MW(intervals):
    var_unserved_reserve_MW = \
        pp.LpVariable.dicts("Unserved Reserve i",
                            (i for i in intervals),
                            lowBound=0,
                            cat="Continuous")
    return var_unserved_reserve_MW


def unserved_inertia_MWsec(intervals):
    var_unserved_inertia_MWsec = \
        pp.LpVariable.dicts("Unserved inertia i",
                            (i for i in intervals),
                            lowBound=0,
                            cat="Continuous")
    return var_unserved_inertia_MWsec


def lineflow_MW(intervals, lines):
    var_lineflow_MW = \
        pp.LpVariable.dicts("Transmission Flow(i, n, n)",
                            ((i, l) for i in intervals for l in lines),
                            lowBound=0,
                            cat="Continuous")
    return var_lineflow_MW

def energy_in_storage_MWh(intervals, units):
    var_energy_in_storage_MWh = \
        pp.LpVariable.dicts("Stored energy in vessel (i,u)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            cat="Continuous")
    return var_energy_in_storage_MWh

def charge_after_losses_MW(intervals, units):
    var_charge_after_losses_MW = \
        pp.LpVariable.dicts("Charged energy (after losses subtracted) (i,u)",
                            ((i, u) for i in intervals for u in units),
                            lowBound=0,
                            cat="Continuous")
    return var_charge_after_losses_MW
