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
    

def make_all_variables(sets):
    
    vars = dict()    

    intervals_units = [sets['intervals'], sets['units']]
    vars['power_generated'] = Variable('power_generated', 'MW', intervals_units)
    vars['reserve_enablment'] = Variable('reserve_enablment', 'MW', intervals_units)
    
    intervals_units_commit = [sets['intervals'], sets['units_commit']]
    vars['commit_status'] = Variable('commit_status', 'Binary', intervals_units_commit)
    vars['start_up_status'] = Variable('start_up_status', 'Binary', intervals_units_commit)
    vars['shut_down_status'] = Variable('shut_down_status', 'Binary', intervals_units_commit)
    vars['inertia_provided'] = Variable('inertia_provided', 'Binary', intervals_units_commit)
    
    intervals_units_storage = [sets['intervals'], sets['units_storage']]
    vars['energy_in_reservoir'] = Variable('energy_in_reservoir', 'MWh', intervals_units_storage)
    vars['charge_after_losses'] = Variable('charge_after_losses', 'MW', intervals_units_storage)
    
    vars['unserved_power'] = Variable('unserved_power', 'MW', [sets['intervals']])
    vars['unserved_reserve'] = Variable('unserved_reserve', 'MW', [sets['intervals']])
    vars['unserved_inertia'] = Variable('unserved_inertia', 'MW.s', [sets['intervals']])
    
    return vars

class Variable():
    def __init__(self, name, units, sets):
        self.name = name
        self.units = units
        self.sets = sets
        self.sets_indices = self.make_var_indices(sets)
        self.make_pulp_variable(self.sets_indices)

    def make_var_indices(self, sets):
        import itertools
        
        list_of_set_indices = [x.indices for x in self.sets]
        
        next_set = list_of_set_indices.pop(0)
        indices_permut = itertools.product(next_set)
        indices_permut_list = [x[0] for x in indices_permut]

        for n in range(len(list_of_set_indices)):
            next_set = list_of_set_indices.pop(0)
            indices_permut = itertools.product(indices_permut_list, next_set)
            indices_permut_list = list(indices_permut)

            if n > 0:
                temp_list = list()
                for x in indices_permut_list:
                    xlist = list(x[0])
                    xlist.append(x[1])
                    temp_list.append(tuple(xlist))
                indices_permut_list = temp_list

        return indices_permut_list

    def make_pulp_variable(self, sets_indices):
        var = pp.LpVariable.dicts("Power Generation (i, u)",
                                  (ind for ind in sets_indices),
                                  lowBound=0,
                                  cat="Continuous")
        return var


