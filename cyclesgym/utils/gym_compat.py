try:
    import gymnasium as gym  # Preferred
    from gymnasium import spaces
    from gymnasium.envs.registration import register
    GYMNASIUM = True
except Exception:  # Fallback to legacy gym
    import gym  # type: ignore
    from gym import spaces  # type: ignore
    try:
        from gym.envs.registration import register  # type: ignore
    except Exception:
        register = None  # type: ignore
    GYMNASIUM = False

__all__ = ["gym", "spaces", "register", "GYMNASIUM"]

