import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent / "settings.yaml"

# loads and returns settings.yaml as a dict
def load_settings():
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Settings file not found: {e}")
    if content is None:
        return {}
    if not isinstance(content, dict):
        raise ValueError(f"Settings file does not contain a dict: {type(content)}")
    return content