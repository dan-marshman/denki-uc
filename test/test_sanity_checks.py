import denkiuc.uc_model as uc
import os
import unittest
import denkiuc.sanity_check_solution as scs

test1_path = os.path.join(uc.path_to_tests, 'test1')
test_model = uc.ucModel('test1', test1_path)
test_model.data.units.loc['Coal1', 'NoUnits'] = 5
test_model.solve()


class economic_dispatch_sanity_checks(unittest.TestCase):
    def test_power_lt_capacity_no_error(self):
        for u in test_model.sets['units'].indices:
            units_capacity = \
                test_model.data.units['Capacity_MW'][u] * test_model.data.units['NoUnits'][u]

            for i in test_model.sets['intervals'].indices:
                for s in test_model.sets['scenarios'].indices:

                    test_model.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * 1

        test_result = \
            scs.check_power_lt_capacity(test_model.sets, test_model.data, test_model.results)

        self.assertEqual(test_result, 0)

    def test_power_lt_capacity_error(self):
        counter = 0

        for u in test_model.sets['units'].indices:
            units_capacity = \
                test_model.data.units['Capacity_MW'][u] * test_model.data.units['NoUnits'][u]

            for i in test_model.sets['intervals'].indices:
                for s in test_model.sets['scenarios'].indices:
                    counter += 1
                    test_model.results['power_generated'].loc[i, (s, u)] = \
                        units_capacity * 1.0000001

        test_result = \
            scs.check_power_lt_capacity(test_model.sets, test_model.data, test_model.results)

        self.assertEqual(test_result, counter)

    def test_energy_charged_lt_charge_capacity_no_error(self):
        for u in test_model.sets['units_storage'].indices:
            units_charge_capacity = \
                test_model.data.units['Capacity_MW'][u] * test_model.data.units['NoUnits'][u] \
                * test_model.data.units['RTEfficiency'][u]

            for i in test_model.sets['intervals'].indices:
                for s in test_model.sets['scenarios'].indices:
                    test_model.results['charge_after_losses'].loc[i, (s, u)] = \
                        units_charge_capacity * 1

        test_result = scs.check_energy_charged_lt_charge_capacity(test_model.sets,
                                                                  test_model.data,
                                                                  test_model.results)

        self.assertEqual(test_result, 0)

    def test_energy_charged_lt_charge_capacity_error(self):
        counter = 0

        for u in test_model.sets['units_storage'].indices:
            units_charge_capacity = \
                test_model.data.units['Capacity_MW'][u] * test_model.data.units['NoUnits'][u] \
                * test_model.data.units['RTEfficiency'][u]

            for i in test_model.sets['intervals'].indices:
                for s in test_model.sets['scenarios'].indices:
                    counter += 1
                    test_model.results['charge_after_losses'].loc[i, (s, u)] = \
                        units_charge_capacity * 1.0000001

        print(test_model.results['charge_after_losses'].head())

        test_result = scs.check_energy_charged_lt_charge_capacity(test_model.sets,
                                                                  test_model.data,
                                                                  test_model.results)

        self.assertEqual(test_result, counter)


class unit_commitment_sanity_checks(unittest.TestCase):
    def test_power_raise_reserves_lt_capacity_no_error(self):
        pass


if __name__ == '__main__':
    unittest.main()
