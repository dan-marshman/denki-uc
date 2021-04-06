import denkiuc.uc_model as uc
import os
import unittest
import denkiuc.sanity_check_solution as scs

test1_path = os.path.join(uc.path_to_tests, 'test1')
tM = uc.ucModel('test1', test1_path)
tM.data.units.loc['Coal1', 'NoUnits'] = 5
tM.arrange_data()
tM.solve()


class economic_dispatch_sanity_checks(unittest.TestCase):
    def test_power_lt_capacity_no_error(self):
        for u in tM.sets['units'].indices:
            units_capacity = \
                tM.data.units['Capacity_MW'][u] * tM.data.units['NoUnits'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:

                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * 1

        test_result, discard = scs.check_power_lt_capacity(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, 0)

    def test_power_lt_capacity_error(self):
        counter = 0

        for u in tM.sets['units'].indices:
            units_capacity = \
                tM.data.units['Capacity_MW'][u] * tM.data.units['NoUnits'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    counter += 1
                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * 1.0000001

        test_result, discard = scs.check_power_lt_capacity(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, counter)

    def test_energy_charged_lt_charge_capacity_no_error(self):
        for u in tM.sets['units_storage'].indices:
            units_charge_capacity = \
                tM.data.units['Capacity_MW'][u] * tM.data.units['NoUnits'][u] \
                * tM.data.units['RTEfficiency'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    tM.results['charge_after_losses'].loc[i, (s, u)] = \
                        units_charge_capacity * 1

        test_result, discard = \
            scs.check_energy_charged_lt_charge_capacity(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, 0)

    def test_energy_charged_lt_charge_capacity_error(self):
        counter = 0

        for u in tM.sets['units_storage'].indices:
            units_charge_capacity = \
                tM.data.units['Capacity_MW'][u] * tM.data.units['NoUnits'][u] \
                * tM.data.units['RTEfficiency'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    counter += 1
                    tM.results['charge_after_losses'].loc[i, (s, u)] = \
                        units_charge_capacity * 1.0000001

        test_result, discard = \
            scs.check_energy_charged_lt_charge_capacity(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, counter)


class unit_commitment_sanity_checks(unittest.TestCase):
    def test_minimum_down_time_is_respected_no_error(self):
        ints_per_hour = 3
        tM.settings['INTERVALS_PER_HOUR'] = ints_per_hour

        tM.data.units.loc[:, 'NoUnits'] = 1

        for u in tM.sets['units_commit'].indices:
            tM.data.units.loc[u, 'MinDownTime_h'] = max(2, tM.data.units['MinDownTime_h'][u])
            units_min_down_time = tM.data.units['MinDownTime_h'][u] * ints_per_hour

            for s in tM.sets['scenarios'].indices:
                tM.results['num_commited'].loc[:, (s, u)] = 1
                tM.results['num_starting_up'].loc[:, (s, u)] = 0
                tM.results['num_shutting_down'].loc[:, (s, u)] = 0

                tM.results['num_shutting_down'].loc[2, (s, u)] = 1

                for i in range(16, 16 + units_min_down_time):
                    tM.results['num_commited'].loc[i, (s, u)] = 0

        test_result, discard = \
            scs.minimum_down_time_is_respected(tM.sets, tM.data, tM.results, tM.settings)

        self.assertEqual(test_result, 0)

    def test_minimum_down_time_is_respected_error(self):
        counter = 0
        ints_per_hour = 3
        tM.settings['INTERVALS_PER_HOUR'] = ints_per_hour

        tM.data.units.loc[:, 'NoUnits'] = 1

        for u in tM.sets['units_commit'].indices:
            tM.data.units.loc[u, 'MinDownTime_h'] = max(2, tM.data.units['MinDownTime_h'][u])
            units_min_down_time = tM.data.units['MinDownTime_h'][u] * ints_per_hour

            for s in tM.sets['scenarios'].indices:
                counter += 1

                tM.results['num_commited'].loc[:, (s, u)] = 1
                tM.results['num_starting_up'].loc[:, (s, u)] = 0
                tM.results['num_shutting_down'].loc[:, (s, u)] = 0

                tM.results['num_shutting_down'].loc[2, (s, u)] = 1

                for i in range(16, 16 + units_min_down_time - 1):
                    tM.results['num_commited'].loc[i, (s, u)] = 0

        test_result, discard = \
            scs.minimum_down_time_is_respected(tM.sets, tM.data, tM.results, tM.settings)

        self.assertEqual(test_result, counter)

    def test_minimum_up_time_is_respected_no_error(self):
        ints_per_hour = 3
        tM.settings['INTERVALS_PER_HOUR'] = ints_per_hour

        tM.data.units.loc[:, 'NoUnits'] = 1

        for u in tM.sets['units_commit'].indices:
            tM.data.units.loc[u, 'MinUpTime_h'] = max(2, tM.data.units['MinUpTime_h'][u])
            units_min_up_time = tM.data.units['MinUpTime_h'][u] * ints_per_hour

            for s in tM.sets['scenarios'].indices:
                tM.results['num_commited'].loc[:, (s, u)] = 0
                tM.results['num_starting_up'].loc[:, (s, u)] = 0
                tM.results['num_shutting_down'].loc[:, (s, u)] = 0

                tM.results['num_starting_up'].loc[2, (s, u)] = 1

                for i in range(16, 16 + units_min_up_time):
                    tM.results['num_commited'].loc[i, (s, u)] = 1

        test_result, discard = \
            scs.minimum_up_time_is_respected(tM.sets, tM.data, tM.results, tM.settings)

        self.assertEqual(test_result, 0)

    def test_minimum_up_time_is_respected_error(self):
        ints_per_hour = 3
        tM.settings['INTERVALS_PER_HOUR'] = ints_per_hour
        counter = 0

        tM.data.units.loc[:, 'NoUnits'] = 1

        for u in tM.sets['units_commit'].indices:
            tM.data.units.loc[u, 'MinUpTime_h'] = max(2, tM.data.units['MinUpTime_h'][u])
            units_min_up_time = tM.data.units['MinUpTime_h'][u] * ints_per_hour

            for s in tM.sets['scenarios'].indices:
                counter += 1

                tM.results['num_commited'].loc[:, (s, u)] = 0
                tM.results['num_starting_up'].loc[:, (s, u)] = 0
                tM.results['num_shutting_down'].loc[:, (s, u)] = 0

                tM.results['num_starting_up'].loc[2, (s, u)] = 1

                for i in range(10, 10 + units_min_up_time - 1):
                    tM.results['num_commited'].loc[i, (s, u)] = 1

        test_result, discard = \
            scs.minimum_up_time_is_respected(tM.sets, tM.data, tM.results, tM.settings)

        self.assertEqual(test_result, counter)

    def test_power_raise_reserves_lt_capacity_no_error(self):
        val = 0.1

        for u in tM.sets['units_commit'].indices:
            units_capacity = \
                tM.data.units['Capacity_MW'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    tM.results['num_commited'].loc[i, (s, u)] = \
                        max(1, tM.data.units['NoUnits'][u] - 1)
                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * tM.results['num_commited'].loc[i, (s, u)]

                    for r in tM.sets['raise_reserves'].indices:
                        tM.results['reserve_enabled'].loc[i, (s, u, r)] = val
                        tM.results['power_generated'].loc[i, (s, u)] -= val

        test_result, discard = \
            scs.check_power_raise_reserves_lt_commit_cap(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, 0)

    def test_power_raise_reserves_lt_capacity_error(self):
        val = 0.1
        counter = 0

        for u in tM.sets['units_commit'].indices:
            units_capacity = \
                tM.data.units['Capacity_MW'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    tM.results['num_commited'].loc[i, (s, u)] = \
                        max(1, tM.data.units['NoUnits'][u] - 1)
                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * tM.results['num_commited'].loc[i, (s, u)]

                    counter += 1
                    for r in tM.sets['raise_reserves'].indices:
                        tM.results['reserve_enabled'].loc[i, (s, u, r)] = 2*val
                        tM.results['power_generated'].loc[i, (s, u)] -= val

        test_result, discard = \
            scs.check_power_raise_reserves_lt_commit_cap(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, counter)

    def test_power_lower_reserves_gt_min_gen_no_error(self):
        val = 0.1

        for u in tM.sets['units_commit'].indices:
            units_min_gen = \
                tM.data.units['Capacity_MW'][u] \
                * tM.data.units['MinGen'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    tM.results['num_commited'].loc[i, (s, u)] = \
                        max(1, tM.data.units['NoUnits'][u] - 1)
                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_min_gen * tM.results['num_commited'].loc[i, (s, u)]

                    for r in tM.sets['lower_reserves'].indices:
                        tM.results['reserve_enabled'].loc[i, (s, u, r)] = val
                        tM.results['power_generated'].loc[i, (s, u)] += val

        test_result, discard = \
            scs.check_power_lower_reserves_gt_min_gen(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, 0)

    def test_power_lower_reserves_gt_min_gen_error(self):
        val = 0.1
        counter = 0

        for u in tM.sets['units_commit'].indices:
            units_min_gen = \
                tM.data.units['Capacity_MW'][u] \
                * tM.data.units['MinGen'][u]

            for i in tM.sets['intervals'].indices:
                for s in tM.sets['scenarios'].indices:
                    tM.results['num_commited'].loc[i, (s, u)] = \
                        max(1, tM.data.units['NoUnits'][u] - 1)
                    tM.results['power_generated'].loc[i, (s, u)] = \
                        units_min_gen * tM.results['num_commited'].loc[i, (s, u)]

                    counter += 1
                    for r in tM.sets['lower_reserves'].indices:
                        tM.results['reserve_enabled'].loc[i, (s, u, r)] = 2 * val
                        tM.results['power_generated'].loc[i, (s, u)] += val

        test_result, discard = \
            scs.check_power_lower_reserves_gt_min_gen(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, counter)


if __name__ == '__main__':
    unittest.main()
