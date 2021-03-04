import pulp as pp


def physical_obj_fn_terms(self):
    physical_obj_fn = \
        build_obj_start_cost_term(self) \
        + build_obj_fuel_term(self) \
        + build_obj_start_cost_term(self)
    return physical_obj_fn


def build_obj_vom_term(self):
    obj_vom = \
        pp.lpSum([self.vars['power_generated_MW'][(i, u)]
                 * self.unit_data['VOM_$pMWh'][u]
                  for i in self.sets['intervals'] for u in self.sets['units']]) \
        / self.INTERVALS_PER_HOUR
    return obj_vom


def build_obj_fuel_term(self):
    obj_fuel = \
        pp.lpSum([self.vars['power_generated_MW'][(i, u)]
                  * 3.6
                  * self.unit_data['FuelCost_$pGJ'][u]
                  / self.unit_data['ThermalEfficiency'][u]
                  for i in self.sets['intervals'] for u in self.sets['units_commit']]) \
        / self.INTERVALS_PER_HOUR
    return obj_fuel


def build_obj_start_cost_term(self):
    obj_start_ups = \
        pp.lpSum([self.vars['start_up_status'][(i, u)]
                  * self.unit_data['StartCost_$'][u]
                  for i in self.sets['intervals'] for u in self.sets['units_commit']])
    return obj_start_ups


def unserved_obj_fn_terms(self):
    obj_uns_demand = \
        pp.lpSum([self.UNS_LOAD_PNTY*self.vars['unserved_demand_MW'][i]
                  for i in self.sets['intervals']]) \
        / self.INTERVALS_PER_HOUR

    obj_uns_reserve = \
        pp.lpSum([self.UNS_RESERVE_PNTY*self.vars['unserved_reserve_MW'][i]
                  for i in self.sets['intervals']]) \
        / self.INTERVALS_PER_HOUR

    obj_uns_inertia = \
        pp.lpSum([self.UNS_INERTIA_PNTY*self.vars['unserved_inertia_MWsec'][i]
                  for i in self.sets['intervals']]) \
        / self.INTERVALS_PER_HOUR
    
    unserved_terms = obj_uns_demand + obj_uns_reserve + obj_uns_inertia
    return unserved_terms


def obj_fn(self):
    obj_fn = \
        physical_obj_fn_terms(self) \
        + unserved_obj_fn_terms(self)
    return obj_fn
