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

        test_result = \
            scs.check_power_lt_capacity(tM.sets, tM.data, tM.results)

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

        test_result = \
            scs.check_power_lt_capacity(tM.sets, tM.data, tM.results)

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

        test_result = scs.check_energy_charged_lt_charge_capacity(tM.sets,
                                                                  tM.data,
                                                                  tM.results)

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

        test_result = scs.check_energy_charged_lt_charge_capacity(tM.sets,
                                                                  tM.data,
                                                                  tM.results)

        self.assertEqual(test_result, counter)


class unit_commitment_sanity_checks(unittest.TestCase):
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

        test_result = \
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

        test_result = \
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

        test_result = \
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

        test_result = \
            scs.check_power_lower_reserves_gt_min_gen(tM.sets, tM.data, tM.results)

        self.assertEqual(test_result, counter)


if __name__ == '__main__':
    unittest.main()
