def check_power_gt_min_stable_gen(sets, data, results):
    errors_count = 0

    for u in sets['units_commit'].indices:
        mingen_MW \
            = data.units['Capacity_MW'][u] \
            * data.units['MinGen'][u]

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                if results['num_commited'][u][i] > 0:
                    minimum_generation = results['num_commited'][u][i] * mingen_MW
                    if results['power_generated'][(s, u)][i] < minimum_generation:
                        print('Sanity Check: Unit', u, 'Interval', i,
                              'generating below its min stable gen')
                        errors_count += 1

    return errors_count


def check_power_lt_committed_capacity(sets, data, results):
    errors_count = 0

    for u in sets['units_commit'].indices:
        unit_capacity = data.units['Capacity_MW'][u]
        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                maximum_generation = results['num_commited'][u][i] * unit_capacity
                if results['power_generated'][(s, u)][i] > maximum_generation:
                    print('Sanity Check: Unit', u, 'Interval', i, 'generating above its capacity')
                    errors_count += 1

    return errors_count


def check_power_lt_capacity(sets, data, results):
    errors_count = 0

    for u in list(sets['units'].indices):
        total_capacity = data.units['Capacity_MW'][u] * data.units['NoUnits'][u]

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                if results['power_generated'][(s, u)][i] > total_capacity:
                    print('Sanity Check: Unit', u, 'Interval', i,
                          'generating above its capacity', '(%f > %f)' %
                          (round(results['power_generated'][u][i]), round(total_capacity)))
                    errors_count += 1

    return errors_count


def check_energy_charged_lt_charge_capacity(sets, data, results):
    errors_count = 0

    for u in list(sets['units_storage'].indices):
        charge_capacity = data.units['Capacity_MW'][u] / data.units['RTEfficiency'][u]
        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:
                if results['charge_after_losses'][(s, u)][i] > charge_capacity:
                    print('Sanity Check: Unit', u, 'Interval', i,
                          'charging above its charge capacity')
                    errors_count += 1

    return errors_count


def total_gen_equals_demand(sets, results):
    errors_count = 0

    dispatch = results['dispatch']
    df_cols = dispatch.columns.to_list()

    for s in sets['scenarios'].indices:
        filtered_cols = [c for c in df_cols if c[0] == s]
        dispatch_sum = dispatch[filtered_cols].sum(axis=1).round(4)

        if dispatch_sum.sum() != 0:
            dispatch_sum = dispatch_sum[dispatch_sum[:] != 0]
            print('Sanity check: Supply does not equal demand in intervals',
                  dispatch_sum)
            errors_count += len(dispatch_sum.index.to_list())

    return errors_count


def minimum_up_time_is_respected(sets, data, results, settings):
    errors_count = 0

    for u in sets['units_commit'].indices:
        minimum_up_time = data.units['MinUpTime_h'][u]
        time_on = 0
        prev_commit_status = 0

        for i in sets['intervals'].indices:
            current_commit_status = results['num_commited'].loc[i, u]

            if current_commit_status == 1:
                time_on += 1

            if current_commit_status == 0:
                if prev_commit_status == 1:
                    if time_on < minimum_up_time * settings['INTERVALS_PER_HOUR']:
                        print("Min up time error for unit", u, "interval", i)
                        errors_count = errors_count + 1

                time_on = 0

            prev_commit_status = current_commit_status

    return errors_count


def minimum_down_time_is_respected(sets, data, results, settings):
    errors_count = 0

    for u in sets['units_commit'].indices:
        minimum_down_time = data.units['MinDownTime_h'][u]
        time_off = 0
        prev_commit_status = 1

        for i in sets['intervals'].indices:
            current_commit_status = results['num_commited'].loc[i, u]

            if current_commit_status == 0:
                time_off += 1

            if current_commit_status == 1:
                if prev_commit_status == 0:
                    if time_off < minimum_down_time * settings['INTERVALS_PER_HOUR']:
                        print("Min down time error for unit", u, "interval", i)
                        errors_count = errors_count + 1

                time_off = 0

            prev_commit_status = current_commit_status

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


def check_storage_continiuity(sets, data, results):
    errors_count = 0

    for u in list(sets['units_storage'].indices):
        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:

                if i == min(sets['intervals'].indices):
                    initial_energy_in_storage_MWh \
                        = (data.initial_state['StorageLevel_frac'][u]
                           * data.units['StorageCap_h'][u]
                           * data.units['Capacity_MW'][u])

                    net_flow = \
                        (
                         initial_energy_in_storage_MWh
                         - results['energy_in_reservoir'][(s, u)][i]
                         + results['charge_after_losses'][(s, u)][i] / 2
                         - results['power_generated'][(s, u)][i] / 2
                        )

                if i > min(sets['intervals'].indices):
                    net_flow = \
                        (
                         results['energy_in_reservoir'][(s, u)][i-1]
                         - results['energy_in_reservoir'][(s, u)][i]
                         + results['charge_after_losses'][(s, u)][i] / 2
                         - results['power_generated'][(s, u)][i] / 2
                        )

                if net_flow.round(4) != 0:
                    print('Sanity Check: Unit', u, 'Interval', i,
                          'net storage flow is not zero:', net_flow)
                    errors_count += 1

    return errors_count


def check_stored_energy_lt_storage_capacity(sets, data, results):
    errors_count = 0

    for u in list(sets['units_storage'].indices):
        storage_capacity_MWh = data.units['StorageCap_h'][u] * data.units['Capacity_MW'][u]
        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:
                if results['energy_in_reservoir'][(s, u)][i] > storage_capacity_MWh:
                    print('Sanity Check: Unit', u, 'Interval', i,
                          'stored energy exceeds storage capacity')
                    errors_count += 1
    return errors_count


def run_sanity_checks(sets, data, results, settings):
    check_power_lt_capacity(sets, data, results)
    check_power_lt_committed_capacity(sets, data, results)
    check_power_gt_min_stable_gen(sets, data, results)
    total_gen_equals_demand(sets, results)
    check_energy_charged_lt_charge_capacity(sets, data, results)
    check_storage_continiuity(sets, data, results)
    check_stored_energy_lt_storage_capacity(sets, data, results)
    minimum_up_time_is_respected(sets, data, results, settings)
    minimum_down_time_is_respected(sets, data, results, settings)
