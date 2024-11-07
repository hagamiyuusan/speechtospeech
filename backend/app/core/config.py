from pathlib import Path
from functools import lru_cache
import yaml
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = ConfigDict(
        extra='allow',  # Allows extra fields that aren't declared
        env_file=str(PROJECT_ROOT / ".env")  # Convert Path to string for env_file
    )

    @classmethod
    def from_yaml(cls) -> "Settings":
        yaml_path = PROJECT_ROOT / "config.yaml"
        with open(yaml_path) as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings.from_yaml()