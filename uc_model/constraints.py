import pulp as pp

def supply_eq_demand(self, mod):
    for i in self.sets['intervals']:
        label = 'meet_demand_i_%d' % i
        condition = \
            (
             pp.lpSum([self.vars['power_generated_MW'][(i, u)]
                      for u in self.sets['units']])
             + self.vars['unserved_demand_MW'][i]
             ==
             self.traces['demand']['VIC'][i]
             + pp.lpSum([self.vars['charge_after_losses_MW'][(i, u)]
                         * (1 / self.unit_data['RTEfficiency'][u])
                        for u in self.sets['units_storage']])
             )
        mod += condition, label
    return mod


def intermittent_resource_availability(self, mod):

    def get_resource_trace(region, technology):
        if technology == 'Wind':
            trace = self.traces['wind']['VIC'].to_dict()
        elif technology == 'SolarPV':
            trace = self.traces['solarPV']['VIC'].to_dict()
        else:
            print('Technology not known')
            exit()
        return trace
    
    for u in self.sets['units_variable']:
        region = self.unit_data['Region'][u]
        technology = self.unit_data['Technology'][u]
        trace = get_resource_trace(region, technology)
        for i in self.sets['intervals']:
            label = 'variable_resource_availability_u_%s_i_%s' % (u, i)
            condition = self.vars['power_generated_MW'][(i, u)] \
                <= trace[i] * self.unit_data['Capacity_MW'][u]
            mod += condition, label

    return mod


def power_lt_committed_capacity(self, mod):
    for i in self.sets['intervals']:
        for u in self.sets['units']:
            label = 'power_lt_cap_%s_int_%s' % (u, i)
            condition = \
                (self.vars['power_generated_MW'][(i, u)] + self.vars['reserve_MW'][(i, u)]
                 <=
                 self.vars['commit_status'][(i, u)] * self.unit_data['Capacity_MW'][u])
            mod += condition, label
    return mod


def power_lt_capacity(self, mod):
    for i in self.sets['intervals']:
        for u in self.sets['units']:
            label = 'power_lt_cap_%s_int_%s' % (u, i)
            condition = \
                (self.vars['power_generated_MW'][(i, u)] + self.vars['reserve_MW'][(i, u)]
                 <=
                 self.unit_data['Capacity_MW'][u])
            mod += condition, label
    return mod


def energy_storage_continuity(self, mod):
    for i in self.sets['intervals']:
        if i > min(self.sets['intervals']):
            for u in self.sets['units_storage']:
                label = 'storage_continuity_%s_int_%s' % (u, i)
                condition = \
                    (self.vars['energy_in_storage_MWh'][(i, u)]
                     ==
                     self.vars['energy_in_storage_MWh'][(i-1, u)]
                     + self.vars['charge_after_losses_MW'][(i, u)] * (1 / self.INTERVALS_PER_HOUR)
                     - self.vars['power_generated_MW'][(i, u)] * (1 / self.INTERVALS_PER_HOUR))
                mod += condition, label
    return mod


def energy_storage_continuity_first_interval(self, mod):
    for u in self.sets['units_storage']:
        i = min(self.sets['intervals'])
        initial_energy_in_storage_MWh \
            = (self.initial_state['StorageLevel_pct'][u]
               * self.unit_data['StorageCap_h'][u]
               * self.unit_data['Capacity_MW'][u])
        label = 'storage_continuity_%s_int_%s' % (u, i)
        condition = \
            (self.vars['energy_in_storage_MWh'][(i, u)]
             ==
             initial_energy_in_storage_MWh
             + self.vars['charge_after_losses_MW'][(i, u)] * (1 / self.INTERVALS_PER_HOUR)
             - self.vars['power_generated_MW'][(i, u)] * (1 / self.INTERVALS_PER_HOUR))
        mod += condition, label
    return mod


def max_stored_energy(self, mod):
    for i in self.sets['intervals']:
        for u in self.sets['units_storage']:
            label = 'max_stored_energy_%s_int_%s' % (u, i)
            condition = \
                (self.vars['energy_in_storage_MWh'][(i, u)]
                 <=
                 self.unit_data['StorageCap_h'][u]
                 * self.unit_data['Capacity_MW'][u])
            mod += condition, label
    return mod


def max_charge(self, mod):
    for i in self.sets['intervals']:
        for u in self.sets['units_storage']:
            label = 'max_charge_%s_int_%s' % (u, i)
            condition = \
                (self.vars['charge_after_losses_MW'][(i, u)]
                 <=
                 self.unit_data['RTEfficiency'][u]
                 * self.unit_data['Capacity_MW'][u])
            mod += condition, label
    return mod


def create_constraints_df(self):
    import os
    import pandas as pd

    self.constraints_df = pd.read_csv(os.path.join(self.inputs_path, 'constraints.csv'), index_col=0)
    return self


def add_all_constraints_to_dataframe(self):

    if self.constraints_df['Include']['supply_eq_demand'] == 1:
        self.mod = supply_eq_demand(self, self.mod)

    if self.constraints_df['Include']['power_lt_capacity'] == 1:
        self.mod = power_lt_capacity(self, self.mod)

    if self.constraints_df['Include']['intermittent_resource_availability'] == 1:
        self.mod = intermittent_resource_availability(self, self.mod)
    
    if self.constraints_df['Include']['energy_storage_continuity'] == 1:
        self.mod = energy_storage_continuity(self, self.mod)
    
    if self.constraints_df['Include']['energy_storage_continuity_first_interval'] == 1:
        self.mod = energy_storage_continuity_first_interval(self, self.mod)
    
    if self.constraints_df['Include']['max_stored_energy'] == 1:
        self.mod = max_stored_energy(self, self.mod)

    if self.constraints_df['Include']['max_charge'] == 1:
        self.mod = max_charge(self, self.mod)


    return self
