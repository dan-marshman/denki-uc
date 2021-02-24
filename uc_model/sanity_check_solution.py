def only_gen_if_committed(commit_status, power_sched):
    errors_count = 0
    for u in list(commit_status):
        for i in commit_status.index.tolist():
            if commit_status[u][i] == 0 and power_sched[u][i] != 0:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'generating when it is not committed')
                errors_count += 1
    return errors_count


def if_committed_gen_gt_mingen(commit_status, power_sched, unit_data):
    errors_count = 0
    for u in list(commit_status):
        mingen_MW \
            = unit_data['Capacity_MW'][u] \
            * unit_data['MinGen'][u]
        for i in commit_status.index.tolist():
            if commit_status[u][i] == 1 and power_sched[u][i] < mingen_MW:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'generating below its min gen')
                errors_count += 1
    return errors_count


def if_committed_gen_lt_capacity(commit_status, power_sched, unit_data):
    errors_count = 0
    for u in list(commit_status):
        unit_capacity = unit_data['Capacity_MW'][u]
        for i in commit_status.index.tolist():
            if commit_status[u][i] == 1 and power_sched[u][i] > unit_capacity:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'generating above its capacity')
                errors_count += 1
    return errors_count


def check_power_lt_capacity(self):
    errors_count = 0
    for u in list(self.sets['units']):
        unit_capacity = self.unit_data['Capacity_MW'][u]
        for i in self.sets['intervals']:
            if self.results['power_generated_MW'][u][i] > unit_capacity:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'generating above its capacity')
                errors_count += 1
    return errors_count


def check_energy_charged_lt_charge_capacity(self):
    errors_count = 0
    for u in list(self.sets['units_storage']):
        charge_capacity = self.unit_data['Capacity_MW'][u] / self.unit_data['RTEfficiency'][u]
        for i in self.sets['intervals']:
            if self.results['charge_after_losses_MW'][u][i] > charge_capacity:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'charging above its charge capacity')
                errors_count += 1
    return errors_count


def total_gen_equals_demand(self):
    errors_count = 0

    tot_gen = self.results['power_generated_MW'].sum(axis=1)
    tot_charge = self.results['charge_before_losses_MW'].sum(axis=1)
    tot_demand = self.traces['demand'].sum(axis=1)
    tot_unserved = self.results['unserved_demand_MW'].sum(axis=1)

    demand_gen_diff = \
        (tot_demand + tot_charge - tot_gen - tot_unserved).round(4).abs()
    
    if demand_gen_diff.sum() != 0:
        demand_gen_diff = demand_gen_diff[demand_gen_diff[:] != 0]
        print('Sanity check: Supply does not equal demand in intervals',
              demand_gen_diff.index.to_list())
        errors_count += len(demand_gen_diff.index.to_list())
    return errors_count


def minimum_up_time_is_respected(commit, unit_data):
    errors_count = 0
    for u in commit.columns.to_list():
        min_up_time = unit_data['MinUpTime_h'][u]
        time_on = 0
        prev_commit = 0
        for i in commit.index.to_list():
            current_commit_status = commit[u][i]
            if current_commit_status == 1:
                time_on = time_on + 1
            if current_commit_status == 0:
                if prev_commit == 1:
                    if time_on < min_up_time:
                        print("Min up time error for unit", u, "interval", i)
                        errors_count = errors_count + 1
                time_on = 0
            prev_commit = current_commit_status
    return errors_count


def minimum_down_time_is_respected(commit, unit_data):
    errors_count = 0
    for u in commit.columns.to_list():
        min_up_time = unit_data['MinDownTime_h'][u]
        time_off = 0
        prev_commit = 1
        for i in commit.index.to_list():
            current_commit_status = commit[u][i]
            if current_commit_status == 0:
                time_off = time_off + 1
            if current_commit_status == 1:
                if prev_commit == 0:
                    if time_off < min_up_time:
                        print("Min up time error for unit", u, "interval", i)
                        errors_count = errors_count + 1
                time_off = 0
            prev_commit = current_commit_status
    return errors_count


def is_there_any_unserved(unserved):
    unserved_power = unserved['Power'].sum(axis=0)
    unserved_reserve = unserved['Reserve'].sum(axis=0)
    unserved_inertia = unserved['Inertia'].sum(axis=0)
    unserved_sysstrength = unserved['SysStrength'].sum(axis=0)

    if unserved_power > 0:
        print("*** There was unserved power:", unserved_power)
    if unserved_power > 0:
        print("*** There was unserved reserve:", unserved_reserve)
    if unserved_inertia > 0:
        print("*** There was unserved inertia:", unserved_inertia)
    if unserved_sysstrength > 0:
        print("*** There was unserved system strength:", unserved_sysstrength)


def com_eq_selfcom_plus_activated_contracts(self_com, contracts, intervention, commit):
    combined_commit = self_com.add(contracts)
    combined_commit = combined_commit.add(intervention)
    exactly_the_same = combined_commit.equals(commit)
    if exactly_the_same:
        return 0
    else:
        print("Self-comitted plus activated contracts schedule"
              "does not equal the full commit schedule")
        return 1


def check_storage_continiuity(self):
    errors_count = 0
    for u in list(self.sets['units_storage']):
        for i in self.sets['intervals']:
            if i == min(self.sets['intervals']):
                initial_energy_in_storage_MWh \
                    = (self.initial_state['StorageLevel_pct'][u]
                       * self.unit_data['StorageCap_h'][u]
                       * self.unit_data['Capacity_MW'][u])
                net_flow = \
                    (
                     initial_energy_in_storage_MWh
                     - self.results['energy_in_storage_MWh'][u][i]
                     + self.results['charge_after_losses_MW'][u][i] / 2
                     - self.results['power_generated_MW'][u][i] / 2
                    )
            if i > min(self.sets['intervals']):
                net_flow = \
                    (
                     self.results['energy_in_storage_MWh'][u][i-1]
                     - self.results['energy_in_storage_MWh'][u][i]
                     + self.results['charge_after_losses_MW'][u][i] / 2
                     - self.results['power_generated_MW'][u][i] / 2
                    )
                if net_flow != 0:
                    print('Sanity Check: Unit', u, 'Interval', i,
                          'net storage flow is not zero')
                    errors_count += 1
    return errors_count


def check_stored_energy_lt_storage_capacity(self):
    errors_count = 0
    for u in list(self.sets['units_storage']):
        storage_capacity_MWh = self.unit_data['StorageCap_h'][u] * self.unit_data['Capacity_MW'][u]
        for i in self.sets['intervals']:
            if self.results['energy_in_storage_MWh'][u][i] > storage_capacity_MWh:
                print('Sanity Check: Unit', u, 'Interval', i,
                      'stored energy exceeds storage capacity')
                errors_count += 1
    return errors_count
