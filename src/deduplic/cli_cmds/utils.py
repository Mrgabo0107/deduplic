import logging
import pickle
from pathlib import Path
from platformdirs import user_config_dir

from deduplic.config import Settings, settings

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(user_config_dir("deduplic"))
CONFIG_FILE = CONFIG_DIR / "config.pkl"


def get_cli_settings() -> Settings:
    """Loads the Settings instance from the binary file and updates the Singleton."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f: 
                saved_settings = pickle.load(f)

            for key, value in saved_settings.__dict__.items():
                setattr(settings, key, value)

            logger.debug(f"CLI settings loaded from binary file: {CONFIG_FILE}")
        except Exception as e:
            logger.warning(
                f"Error reading binary configuration ({e}). Using default settings."
            )
    return settings


def set_cli_settings(current_settings: Settings = settings) -> None:
    """Saves the complete Settings instance as a binary file in user_config_dir."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "wb") as f:  # 'wb' mode: Write Binary
            pickle.dump(current_settings, f)

        logger.debug(f"CLI settings saved to binary file: {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving binary configuration to '{CONFIG_FILE}': {e}")