import unittest
import shutil

from cyclesgym.envs.implementers import Fertilizer, RotationPlanter, FixedRateNPKFertilizer
from cyclesgym.managers import OperationManager
from cyclesgym.envs.utils import ydoy2date
from cyclesgym.utils.pakistan_crop_calendar import get_calendar_windows_for_crops

from cyclesgym.utils.paths import TEST_PATH


class TestFertilizer(unittest.TestCase):
    def setUp(self) -> None:
        # Copy file to make sure we do not modify the original one
        src = TEST_PATH.joinpath('NCornTest.operation')
        self.op_fname = TEST_PATH.joinpath('NCornTest_copy.operation')
        shutil.copy(src, self.op_fname)

        # Init observer
        self.op_manager = OperationManager(self.op_fname)

        # Init Fertilizer
        self.fert = Fertilizer(operation_manager=self.op_manager,
                               operation_fname=self.op_fname,
                               affected_nutrients= ['N_NH4', 'N_NO3'],
                               start_year=1980)

    def tearDown(self) -> None:
        # Remove copied operation file
        self.op_fname.unlink()

    def test_new_action(self):
        # No action on a day where nothing used to happen => Not new
        assert not self.fert._is_new_action(
            year=1, doy=105, new_masses={'N_NH4': 0, 'N_NO3': 0})

        # Same fertilization action as the one already in the file => Not new
        assert not self.fert._is_new_action(
            year=1, doy=106, new_masses={'N_NH4': 112.5, 'N_NO3': 37.5})

        # No action on a day when we used to fertilize => New
        assert self.fert._is_new_action(
            year=1, doy=106, new_masses={'N_NH4': 0, 'N_NO3': 0})

        # Fertilize on a day when we used to do nothing => New
        assert self.fert._is_new_action(
            year=1, doy=105, new_masses={'N_NH4': 112.5, 'N_NO3': 37.5})

    def test_update_operation(self):
        # Incremental mode
        base_op = {'SOURCE': 'UreaAmmoniumNitrate', 'MASS': 80,
                   'FORM': 'Liquid', 'METHOD': 'Broadcast', 'LAYER': 1,
                   'C_Organic': 0.5, 'C_Charcoal': 0., 'N_Organic': 0.,
                   'N_Charcoal': 0., 'N_NH4': 0., 'N_NO3': 0.,
                   'P_Organic': 0., 'P_CHARCOAL': 0., 'P_INORGANIC': 0.,
                   'K': 0.5, 'S': 0.}

        year = 1
        doy = 106
        new_op = self.fert._update_operation(
            year=1, doy=106, old_op=base_op,
            new_masses={'N_NH4': 15, 'N_NO3': 5}, mode='increment')

        target_new_op = base_op.copy()
        target_new_op.update(
            {'MASS': 100., 'C_Organic': 0.4, 'K': 0.4, 'N_NH4': 0.15,
             'N_NO3': 0.05})

        assert target_new_op == new_op[(year, doy, 'FIXED_FERTILIZATION')]

        # Absolute mode
        base_op = {'SOURCE': 'UreaAmmoniumNitrate', 'MASS': 80,
                   'FORM': 'Liquid', 'METHOD': 'Broadcast', 'LAYER': 1,
                   'C_Organic': 0.25, 'C_Charcoal': 0, 'N_Organic': 0,
                   'N_Charcoal': 0, 'N_NH4': 0.25, 'N_NO3': 0.25,
                   'P_Organic': 0, 'P_CHARCOAL': 0, 'P_INORGANIC': 0,
                   'K': 0.25, 'S': 0}

        new_op = self.fert._update_operation(
            year=1, doy=106, old_op=base_op,
            new_masses={'N_NH4': 0, 'N_NO3': 0}, mode='absolute')

        target_new_op = base_op.copy()
        target_new_op.update(
            {'MASS': 40, 'C_Organic': 0.5, 'K': 0.5, 'N_NH4': 0, 'N_NO3': 0})

        assert target_new_op == new_op[(year, doy, 'FIXED_FERTILIZATION')]

    def test_implement_with_collision(self):
        operations = self.fert.operation_manager.op_dict.copy()
        target_op = operations[(1, 106, 'FIXED_FERTILIZATION')].copy()
        target_op.update({'MASS': 20.0, 'N_NH4': 0.75, 'N_NO3': 0.25})
        operations.update({(1, 106, 'FIXED_FERTILIZATION'): target_op})

        self.fert.implement_action(date=ydoy2date(1980, 106),
                                   operation_details={'N_NH4': 15.,
                                                      'N_NO3': 5.})

        # Check manager is equal
        assert self.fert.operation_manager.op_dict == operations

        # Check file is equal
        new_manager = OperationManager(self.fert.operation_fname)
        assert new_manager.op_dict == self.fert.operation_manager.op_dict

    def test_implement_no_collision(self):
        operations = self.fert.operation_manager.op_dict.copy()
        target_op = {'SOURCE': 'Unknown', 'MASS': 20.0,
                     'FORM': 'Unknown', 'METHOD': 'Unknown', 'LAYER': 1.,
                     'C_Organic': 0., 'C_Charcoal': 0., 'N_Organic': 0.,
                     'N_Charcoal': 0., 'N_NH4': 0.75, 'N_NO3': 0.25,
                     'P_Organic': 0., 'P_CHARCOAL': 0., 'P_INORGANIC': 0.,
                     'K': 0., 'S': 0.}
        operations.update({(1, 105, 'FIXED_FERTILIZATION'): target_op})

        self.fert.implement_action(date=ydoy2date(1980, 105),
                                   operation_details={'N_NH4': 15.,
                                                      'N_NO3': 5.})

        # Check manager is equal
        assert self.fert.operation_manager.op_dict == operations

        # Check file is equal
        new_manager = OperationManager(self.fert.operation_fname)
        assert new_manager.op_dict == self.fert.operation_manager.op_dict

    def test_reset(self):
        pass

    def test_normalize_fractions_for_cycles_tiny_overflow(self):
        fractions = {
            'N_NH4': 0.3093195186823687,
            'N_NO3': 0.10310650622745622,
            'P_INORGANIC': 0.20938309153232268,
            'K': 0.3781908835578526,
        }
        # Simulate floating-point drift seen in real runs.
        assert sum(fractions.values()) > 1.0

        cleaned = self.fert._normalize_fractions_for_cycles(fractions)
        assert sum(cleaned.values()) <= 1.0
        assert all(v >= 0 for v in cleaned.values())


class TestRotationPlanterCalendar(unittest.TestCase):
    def setUp(self) -> None:
        self.op_manager = OperationManager(None)
        self.op_fname = TEST_PATH.joinpath('dummy_rotation.operation')

    def test_default_mapping_is_unchanged(self):
        planter = RotationPlanter(operation_manager=self.op_manager,
                                  operation_fname=self.op_fname,
                                  rotation_crops=['CornRM.100', 'SoybeanMG.3'],
                                  start_year=1980)
        op = planter.convert_action_to_dict(crop_categorical=0, doy=0, end_doy=9, max_smc=5)
        assert op['DOY'] == 90
        assert op['END_DOY'] == 153

    def test_calendar_mapping_for_configured_crop(self):
        planter = RotationPlanter(operation_manager=self.op_manager,
                                  operation_fname=self.op_fname,
                                  rotation_crops=['CornRM.100', 'SoybeanMG.3'],
                                  start_year=1980,
                                  crop_calendar_windows={'CornRM.100': (166, 196)})
        op_start = planter.convert_action_to_dict(crop_categorical=0, doy=0, end_doy=9, max_smc=5)
        op_end = planter.convert_action_to_dict(crop_categorical=0, doy=13, end_doy=9, max_smc=5)
        op_fallback = planter.convert_action_to_dict(crop_categorical=1, doy=0, end_doy=9, max_smc=5)

        assert op_start['DOY'] == 166
        assert op_start['END_DOY'] == 196
        assert op_end['DOY'] == 196
        assert op_end['END_DOY'] == 196
        # Soybean has no configured window here, so legacy mapping applies
        assert op_fallback['DOY'] == 90

    def test_invalid_calendar_window_raises(self):
        with self.assertRaises(AssertionError):
            RotationPlanter(operation_manager=self.op_manager,
                            operation_fname=self.op_fname,
                            rotation_crops=['CornRM.100'],
                            start_year=1980,
                            crop_calendar_windows={'CornRM.100': (300, 100)})

    def test_calendar_window_lookup_for_rotation(self):
        windows = get_calendar_windows_for_crops(['CornRM.100', 'SoybeanMG.3', 'WinterWheat'])
        assert windows['CornRM.100'] == (166, 196)
        assert windows['WinterWheat'] == (305, 334)
        assert 'SoybeanMG.3' not in windows


class TestFixedRateNPKFertilizer(unittest.TestCase):
    def setUp(self) -> None:
        src = TEST_PATH.joinpath('NCornTest.operation')
        self.op_fname = TEST_PATH.joinpath('NCornTest_npk_copy.operation')
        shutil.copy(src, self.op_fname)
        self.op_manager = OperationManager(self.op_fname)
        self.fert = FixedRateNPKFertilizer(
            operation_manager=self.op_manager,
            operation_fname=self.op_fname,
            n_nh4_rate=0.75,
            start_year=1980
        )

    def tearDown(self) -> None:
        self.op_fname.unlink()

    def test_convert_mass(self):
        masses = self.fert.convert_mass(mass_n=20.0, mass_p=10.0, mass_k=5.0)
        assert masses == {
            'N_NH4': 15.0,
            'N_NO3': 5.0,
            'P_INORGANIC': 10.0,
            'K': 5.0,
        }

    def test_implement_action_from_dict(self):
        self.fert.implement_action(date=ydoy2date(1980, 105),
                                   action={'N': 20.0, 'P': 10.0, 'K': 5.0})
        op = self.fert.operation_manager.op_dict[(1, 105, 'FIXED_FERTILIZATION')]
        assert op['MASS'] == 35.0
        assert op['N_NH4'] == 15.0 / 35.0
        assert op['N_NO3'] == 5.0 / 35.0
        assert op['P_INORGANIC'] == 10.0 / 35.0
        assert op['K'] == 5.0 / 35.0


if __name__ == '__main__':
    unittest.main()
