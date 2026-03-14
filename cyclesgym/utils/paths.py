import pathlib
import sys

__all__ = [
    'PROJECT_PATH',
    'CYCLES_PATH',
    'AGENTS_PATH',
    'FIGURES_PATH',
    'DATA_PATH',
    'LOCAL_ARCHIVE_PATH',
    'ARTIFACTS_PATH',
    'FINAL_SUCCESSFUL_RUNS_PATH',
    'FINAL_SUCCESSFUL_RUN_BUNDLES_PATH',
    'FINAL_113_RUNS_PATH',
    'FINAL_113_BUNDLES_PATH',
    'CYCLES_EXE',
]

PROJECT_PATH = pathlib.Path(__file__).parents[2]
CYCLES_PATH = PROJECT_PATH.joinpath('cycles')
AGENTS_PATH = PROJECT_PATH.joinpath('agents')
FIGURES_PATH = PROJECT_PATH.joinpath('figures')
DATA_PATH = PROJECT_PATH.joinpath('data')
LOCAL_ARCHIVE_PATH = PROJECT_PATH.joinpath('Local Files and Folders')
ARTIFACTS_PATH = PROJECT_PATH.joinpath('artifacts')
FINAL_SUCCESSFUL_RUNS_PATH = ARTIFACTS_PATH.joinpath('final_successful_runs')
FINAL_SUCCESSFUL_RUN_BUNDLES_PATH = FINAL_SUCCESSFUL_RUNS_PATH.joinpath('bundles')
FINAL_113_RUNS_PATH = FINAL_SUCCESSFUL_RUNS_PATH.joinpath('final_113')
FINAL_113_BUNDLES_PATH = FINAL_113_RUNS_PATH.joinpath('bundles')
TEST_PATH = PROJECT_PATH.joinpath('cyclesgym', 'tests')

# Platform-specific Cycles executable name
CYCLES_EXE = 'Cycles.exe' if sys.platform == 'win32' else 'Cycles'

CYCLES_PATH.mkdir(exist_ok=True, parents=True)
AGENTS_PATH.mkdir(exist_ok=True, parents=True)
FIGURES_PATH.mkdir(exist_ok=True, parents=True)
DATA_PATH.mkdir(exist_ok=True, parents=True)
ARTIFACTS_PATH.mkdir(exist_ok=True, parents=True)
FINAL_SUCCESSFUL_RUNS_PATH.mkdir(exist_ok=True, parents=True)
FINAL_SUCCESSFUL_RUN_BUNDLES_PATH.mkdir(exist_ok=True, parents=True)
FINAL_113_RUNS_PATH.mkdir(exist_ok=True, parents=True)
FINAL_113_BUNDLES_PATH.mkdir(exist_ok=True, parents=True)
