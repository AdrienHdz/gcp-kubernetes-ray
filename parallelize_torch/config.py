from pydantic import BaseSettings


class MainConfig(BaseSettings):
    # hyperparameters
    num_workers: int = 4
    use_gpu: bool = True
    smoke_test: bool = False

    # smoke test params
    num_cpus_smoke_test: int = 3

    class Config:
        env_prefix = "TRAINING_"
