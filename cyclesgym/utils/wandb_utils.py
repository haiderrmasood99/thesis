import os

# Optional environment-variable overrides so users can route runs to separate W&B projects
# without editing training code every time.
WANDB_ENTITY = os.getenv('WANDB_ENTITY') or None

CROP_PLANNING_EXPERIMENT = os.getenv(
    'WANDB_PROJECT_CROP_PLANNING',
    os.getenv('WANDB_PROJECT', 'experiments_crop_planning'),
)
FERTILIZATION_EXPERIMENT = os.getenv(
    'WANDB_PROJECT_FERTILIZATION',
    os.getenv('WANDB_PROJECT', 'agro-rl'),
)
