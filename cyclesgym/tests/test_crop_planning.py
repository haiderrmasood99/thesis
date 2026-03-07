from cyclesgym.envs.crop_planning import CropPlanning
from cyclesgym.envs.weather_generator import FixedWeatherGenerator
import unittest
import shutil
import subprocess

from cyclesgym.managers import CropManager
from cyclesgym.utils.utils import diff_pd
from cyclesgym.utils.paths import CYCLES_PATH, CYCLES_EXE, TEST_PATH
import time


class TestCropPlanning(unittest.TestCase):

    @staticmethod
    def _call_cycles(ctrl):
        subprocess.run([str(CYCLES_PATH.joinpath(CYCLES_EXE)), '-b', ctrl], cwd=CYCLES_PATH, check=True)

    @staticmethod
    def _extract_done(step_out):
        if len(step_out) == 5:
            return bool(step_out[2] or step_out[3])
        return bool(step_out[2])

    def setUp(self):
        self.fnames = ['CropPlanningTest.ctrl',
                       'CropPlanningTest.operation']
        for n in self.fnames:
            src = TEST_PATH.joinpath(n)
            dest = CYCLES_PATH.joinpath('input', n)
            shutil.copy(src, dest)
        self.custom_sim_id = lambda: '1'  # This way the output does not depend on time and can be deleted by teardown

    def _test_policy(self, policy):
        self._call_cycles(self.fnames[0].replace('.ctrl', ''))
        crop_from_sim_1 = CropManager(CYCLES_PATH.joinpath('output',
                                                           self.fnames[0].replace('.ctrl', ''),
                                                           'CornSilageRM.90.dat'))
        crop_from_sim_2 = CropManager(CYCLES_PATH.joinpath('output',
                                                           self.fnames[0].replace('.ctrl', ''),
                                                           'SoybeanMG.3.dat'))

        env = CropPlanning(start_year=1980, end_year=1990, rotation_crops=['CornSilageRM.90',
                                                                           'SoybeanMG.3'],
                           crop_file='GenericCrops.crop',
                           soil_file='GenericHagerstown.soil',
                           weather_generator_class=FixedWeatherGenerator,
                           weather_generator_kwargs={
                               'base_weather_file': CYCLES_PATH.joinpath('input', 'RockSprings.weather')
                           })
        env._create_sim_id = self.custom_sim_id

        env.reset()
        year = 0

        start = time.time()
        while True:
            a = policy[year % 2]
            done = self._extract_done(env.step(a))
            year += 1
            if done:
                break

        crop_from_env_1 = env.crop_output_manager[0]
        crop_from_env_2 = env.crop_output_manager[1]
        print(time.time() - start)
        return crop_from_env_1, crop_from_env_2, crop_from_sim_1, crop_from_sim_2

    def test_equal(self):
        policy = [(0, 0, 10, 9), (1, 2, 8, 9)]

        crop_from_env_1, crop_from_env_2, crop_from_sim_1, crop_from_sim_2 = self._test_policy(policy)

        assert crop_from_env_1.crop_state.equals(crop_from_sim_1.crop_state), \
            diff_pd(crop_from_env_1.crop_state, crop_from_sim_1.crop_state)
        assert crop_from_env_2.crop_state.equals(crop_from_sim_2.crop_state), \
            diff_pd(crop_from_env_2.crop_state, crop_from_sim_2.crop_state)

    def test_different(self):
        policy = [(0, 5, 8, 5), (1, 3, 8, 5)]

        crop_from_env_1, crop_from_env_2, crop_from_sim_1, crop_from_sim_2 = self._test_policy(policy)

        assert not crop_from_env_1.crop_state.equals(crop_from_sim_1.crop_state), \
            diff_pd(crop_from_env_1.crop_state, crop_from_sim_1.crop_state)
        assert not crop_from_env_2.crop_state.equals(crop_from_sim_2.crop_state), \
            diff_pd(crop_from_env_2.crop_state, crop_from_sim_2.crop_state)


if __name__ == '__main__':
    unittest.main()
