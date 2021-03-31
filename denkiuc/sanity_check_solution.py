def process_error_msg(warnings, settings):
    if settings['PRINT_WARNINGS']:
        for warning in warnings:
            print()
            print('Warning: ' + warning)
    else:
        pass


def check_power_lower_reserves_gt_min_gen(sets, data, results):
    warnings = []
    errors_count = 0
    lower_reserves = sets['lower_reserves'].indices

    for u in sets['units_commit'].indices:
        mingen_MW \
            = data.units['Capacity_MW'][u] \
            * data.units['MinGen'][u] \

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                minimum_generation = results['num_commited'][(s, u)][i] * mingen_MW
                power = results['power_generated'][(s, u)][i]
                lower_reserve_enable = \
                    sum(results['reserve_enabled'][(s, u, r)][i] for r in lower_reserves)

                if power - lower_reserve_enable < minimum_generation - 0.005:
                    warnings.append(
                        'Warning: Unit ' + u + ' Interval ' + str(i) + ' scenario ' +
                        str(s) + ' gen less lower reserve less than capacity '
                        + ' \nPower: ' + str(power)
                        + ' \nLower reserve: ' + str(lower_reserve_enable)
                        + ' \nMinimum gen (given commited cap.): ' + str(minimum_generation)
                        )
                    errors_count += 1

    return errors_count, warnings


def check_power_raise_reserves_lt_commit_cap(sets, data, results):
    warnings = []
    errors_count = 0
    raise_reserves = sets['raise_reserves'].indices

    for u in sets['units_commit'].indices:
        unit_capacity = data.units['Capacity_MW'][u]

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                maximum_generation = results['num_commited'][(s, u)][i] * unit_capacity
                power = results['power_generated'][(s, u)][i]
                raise_reserve_enable = \
                    sum(results['reserve_enabled'][(s, u, r)][i] for r in raise_reserves)

                if power + raise_reserve_enable > maximum_generation + 0.005:
                    warnings.append('Warning: Unit ' + u + ' Interval ' + str(i) + ' scenario ' +
                        str(s) + ' gen plus raise reserve greater than capacity '
                        + ' \nPower: ' + str(power)
                        + ' \nRaise reserve: ' + str(raise_reserve_enable)
                        + ' \nCommitted capacity: ' + str(maximum_generation))
                    errors_count += 1

    return errors_count, warnings


def check_power_lt_capacity(sets, data, results):
    warnings = []
    errors_count = 0

    for u in list(sets['units'].indices):
        total_capacity = data.units['Capacity_MW'][u] * data.units['NoUnits'][u]

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                if results['power_generated'][(s, u)][i] > total_capacity:
                    warnings.append('Warning: Unit' + u + 'Interval' + str(i)
                        + 'generating above capacity' +
                        '(%f > %f)' % (results['power_generated'][(s, u)][i], total_capacity))
                    errors_count += 1

    return errors_count, warnings


def check_energy_charged_lt_charge_capacity(sets, data, results):
    warnings = []
    errors_count = 0

    for u in sets['units_storage'].indices:
        charge_capacity = \
            data.units['NoUnits'][u] * data.units['Capacity_MW'][u] * data.units['RTEfficiency'][u]
        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:
                if results['charge_after_losses'][(s, u)][i] > charge_capacity:
                    warnings.append('Warning: Unit' + u + 'Interval' + str(i) +
                        'charging above its charge capacity')
                    errors_count += 1

    return errors_count, warnings


def total_gen_equals_demand(sets, results):
    warnings = []
    errors_count = 0

    dispatch = results['dispatch']
    df_cols = dispatch.columns.to_list()

    for s in sets['scenarios'].indices:
        filtered_cols = [c for c in df_cols if c[0] == s]
        dispatch_sum = dispatch[filtered_cols].sum(axis=1).round(4)

        if dispatch_sum.sum() != 0:
            dispatch_sum = dispatch_sum[dispatch_sum[:] != 0]
            warnings.append('Sanity check: Supply doesnt equal demand in intervals', dispatch_sum)
            errors_count += len(dispatch_sum.index.to_list())

    return errors_count, warnings


def minimum_up_time_is_respected(sets, data, results, settings):
    warnings = []
    errors_count = 0

    i0 = min(sets['intervals'].indices)

    for u in sets['units_commit'].indices:
        minimum_up_time = data.units['MinUpTime_h'][u]
        for s in sets['scenarios'].indices:
            time_on = 0
            prev_commit_status = 0
            for i in sets['intervals'].indices:
                current_commit_status = results['num_commited'].loc[i, (s, u)]

                if current_commit_status == 1:
                    time_on += 1

                if current_commit_status == 0:
                    if prev_commit_status == 1:
                        if i > i0 + minimum_up_time + settings['INTERVALS_PER_HOUR']:
                            if time_on < minimum_up_time * settings['INTERVALS_PER_HOUR']:
                                warnings.append('Min up time error for unit', u, 'interval', i, 'scenario',
                                    s, 'time on is', time_on, 'periods', 'min_up_time is',
                                    minimum_up_time * settings['INTERVALS_PER_HOUR'], 'periods')
                                errors_count = errors_count + 1

                    time_on = 0

                prev_commit_status = current_commit_status

    return errors_count, warnings


def minimum_down_time_is_respected(sets, data, results, settings):
    warnings = []
    errors_count = 0

    i0 = min(sets['intervals'].indices)

    for u in sets['units_commit'].indices:
        minimum_down_time = data.units['MinDownTime_h'][u]
        time_off = 0
        prev_commit_status = 1

        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                if i > i0 + minimum_down_time * settings['INTERVALS_PER_HOUR']:
                    current_commit_status = results['num_commited'].loc[i, (s, u)]

                    if current_commit_status == 0:
                        time_off += 1

                    if current_commit_status == 1:
                        if prev_commit_status == 0:
                            if time_off < minimum_down_time * settings['INTERVALS_PER_HOUR']:
                                warnings.append('Min down time error for unit', u, 'interval', i,
                                    'scenario', s)
                                errors_count = errors_count + 1

                        time_off = 0

                    prev_commit_status = current_commit_status

    return errors_count, warnings


def is_there_any_unserved(unserved):
    warnings = []
    unserved_power = unserved['Power'].sum(axis=0)
    unserved_reserve = unserved['Reserve'].sum(axis=0)
    unserved_inertia = unserved['Inertia'].sum(axis=0)
    unserved_sysstrength = unserved['SysStrength'].sum(axis=0)

    if unserved_power > 0:
        warnings.append('*** There was unserved power:', unserved_power)

    if unserved_power > 0:
        warnings.append('*** There was unserved reserve:', unserved_reserve)

    if unserved_inertia > 0:
        warnings.append('*** There was unserved inertia:', unserved_inertia)

    if unserved_sysstrength > 0:
        warnings.append('*** There was unserved system strength:', unserved_sysstrength)


def check_storage_continiuity(sets, data, results):
    warnings = []
    errors_count = 0

    for u in list(sets['units_storage'].indices):
        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:

                if i == min(sets['intervals'].indices):
                    initial_energy_in_storage_MWh \
                        = data.initial_state['StorageLevel_frac'][u] \
                        * data.units['StorageCap_h'][u] \
                        * data.units['Capacity_MW'][u] \
                        * data.units['NoUnits'][u]

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
                    warnings.append('Warning: Unit', u, 'Interval', i,
                        'net storage flow is not zero:', net_flow)
                    errors_count += 1

    return errors_count, warnings


def check_stored_energy_lt_storage_capacity(sets, data, results):
    warnings = []
    errors_count = 0

    for u in sets['units_storage'].indices:
        storage_capacity_MWh = \
            data.units['StorageCap_h'][u] \
            * data.units['Capacity_MW'][u] \
            * data.units['NoUnits'][u]

        for s in sets['scenarios'].indices:
            for i in sets['intervals'].indices:
                if results['energy_in_reservoir'][(s, u)][i] > storage_capacity_MWh:
                    warnings.append('Warning: Unit', u, 'Interval', i, 'scenario', s,
                        'stored energy exceeds storage capacity')

                    errors_count += 1

    return errors_count, warnings


def check_reserve_lt_capability(sets, data, results):
    warnings = []
    import denkiuc.misc_functions as mf

    errors_count = 0

    for u in sets['units_commit'].indices:
        for r in sets['reserves'].indices:
            max_reserves_per_unit = mf.get_max_reserves_per_unit(u, r, data.units)

            for i in sets['intervals'].indices:
                for s in sets['scenarios'].indices:
                    max_reserves = max_reserves_per_unit * results['num_commited'][(s, u)][i]

                    if results['reserve_enabled'][(s, u, r)][i] > max_reserves:
                        warnings.append('Warning: Unit', u, 'Interval', i, 'scenario', s,
                            'reserve', r, '\nReserve enablement exceeds reserve capability',
                            '\nUnit committed: ', results['num_commited'][(s, u)][i],
                            '\nMax reserve (total): ', max_reserves)

                        errors_count += 1

    return errors_count, warnings


def check_max_rocof(sets, results):
    warnings = []
    errors_count = 0

    for i in sets['intervals'].indices:
        max_rocof = results['max_rocof']['MaxRocof'][i]
        rocof_limit = results['max_rocof']['RocofLimit'][i]
        if max_rocof > rocof_limit:
            warnings.append('Warning: Interval', i, ': Max RoCoF of', max_rocof,
                'exceeds RoCoF limit of', rocof_limit)

            errors_count += 1
    return errors_count, warnings


def run_sanity_checks(sets, data, results, settings):
    errors_count, warnings = check_power_lt_capacity(sets, data, results)
    errors_count, warnings = total_gen_equals_demand(sets, results)
    errors_count, warnings = check_energy_charged_lt_charge_capacity(sets, data, results)
    errors_count, warnings = check_storage_continiuity(sets, data, results)
    errors_count, warnings = check_stored_energy_lt_storage_capacity(sets, data, results)
    errors_count, warnings = check_reserve_lt_capability(sets, data, results)

    if settings['INCL_UNIT_COMMITMENT']:
        # errors_count, warnings = minimum_up_time_is_respected(sets, data, results, settings)
        # errors_count, warnings = minimum_down_time_is_respected(sets, data, results, settings)
        errors_count, warnings = check_max_rocof(sets, results)
        errors_count, warnings = check_power_raise_reserves_lt_commit_cap(sets, data, results)
        errors_count, warnings = check_power_lower_reserves_gt_min_gen(sets, data, results)
