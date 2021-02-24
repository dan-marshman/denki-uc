import pandas as pd


def energy_price_to_df(self):
    energy_price = pd.DataFrame(columns=['VIC'], index=self.sets['intervals'])

    for i in self.sets['intervals']:
        energy_price.loc[i, 'VIC'] \
            = self.mod.constraints['meet_demand_i_%d' % i].pi
    return energy_price


def power_generated_to_df(self):
    power_generated_MW = pd.DataFrame(columns=self.sets['units'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units']:
            power_generated_MW.loc[i, u] = self.vars['power_generated_MW'][i, u].value()
    return power_generated_MW


def inertia_sched_to_df(self):
    inertia_sched = pd.DataFrame(columns=self.sets['units_commitable'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_commitable']:
            inertia_sched.loc[i, u] = self.vars['inertia_MWsec'][i, u].value()
    return inertia_sched


def commit_status_to_df(self):
    commit_status = pd.DataFrame(columns=self.sets['units_commit'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_commit']:
            commit_status.loc[i, u] = self.vars['commit_status'][i, u].value()
    return commit_status


def start_sched_to_df(self):
    start_sched = pd.DataFrame(columns=self.sets['units_commitable'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_commitable']:
            start_sched.loc[i, u] = self.vars['start_up_status'][i, u].value()
    return start_sched


def unserved_demand_to_df(self):
    unserved_df = pd.DataFrame(columns=['Unserved Demand'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        unserved_df.loc[i, 'Unserved Demand'] = self.vars['unserved_demand_MW'][i].value()
    return unserved_df 


def charge_before_losses_to_df(self):
    charge_before_losses_MW = \
        pd.DataFrame(columns=self.sets['units_storage'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_storage']:
            charge_before_losses_MW.loc[i, u] = \
                self.vars['charge_after_losses_MW'][i, u].value() \
                / self.unit_data['RTEfficiency'][u]
    return charge_before_losses_MW 


def charge_after_losses_to_df(self):
    charge_after_losses_MW = \
        pd.DataFrame(columns=self.sets['units_storage'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_storage']:
            charge_after_losses_MW.loc[i, u] = \
                self.vars['charge_after_losses_MW'][i, u].value()
    return charge_after_losses_MW 


def energy_in_storage_to_df(self):
    energy_in_storage_MWh = \
        pd.DataFrame(columns=self.sets['units_storage'], index=self.sets['intervals'])
    for i in self.sets['intervals']:
        for u in self.sets['units_storage']:
            energy_in_storage_MWh.loc[i, u] = \
                self.vars['energy_in_storage_MWh'][i, u].value()
    return energy_in_storage_MWh 
