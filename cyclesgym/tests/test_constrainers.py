import unittest

from cyclesgym.envs.constrainers import FertilizationEventConstrainer, TotalNitrogenConstrainer


class TestActionAwareConstrainers(unittest.TestCase):
    def test_fertilization_event_scalar(self):
        c = FertilizationEventConstrainer()
        assert c.compute_constraint(date=None, action=0.0)['cost_n_fertilization_events'] == 0
        assert c.compute_constraint(date=None, action=1.0)['cost_n_fertilization_events'] == 1

    def test_fertilization_event_dict(self):
        c = FertilizationEventConstrainer()
        assert c.compute_constraint(date=None, action={'N': 0.0, 'P': 0.0, 'K': 0.0})['cost_n_fertilization_events'] == 0
        assert c.compute_constraint(date=None, action={'N': 0.0, 'P': 0.0, 'K': 5.0})['cost_n_fertilization_events'] == 1

    def test_total_nitrogen_from_dict(self):
        c = TotalNitrogenConstrainer()
        val = c.compute_constraint(date=None, action={'N_NH4': 10.0, 'N_NO3': 5.0, 'P_INORGANIC': 100.0})['cost_total_n']
        assert val == 15.0


if __name__ == '__main__':
    unittest.main()
