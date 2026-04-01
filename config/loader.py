import yaml
from pathlib import Path
from hydra.plugins.config_source import ConfigLoadError

DEFAULT_CONFIG_PATH = Path(__file__).parent / "settings.yaml"

# loads and returns settings.yaml as a dict
def load_settings():
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise ConfigLoadError(f"Settings file not found: {e}")
    if content is None:
        return {}
    if not isinstance(content, dict):
        raise ConfigLoadError(f"Settings file does not contain a dict: {type(content)}")
    return content