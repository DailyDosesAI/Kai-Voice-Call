"""
Avatar configuration loader for easy management of avatar settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from avatar.avatar import AvatarConfig, AvatarFactory

logger = logging.getLogger(__name__)


class AvatarConfigLoader:
    """Loads and manages avatar configurations from JSON files."""
    
    def __init__(self, config_file: str = "avatar_config.json"):
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config_data = json.load(f)
                logger.info(f"Loaded avatar configuration from {self.config_file}")
            else:
                logger.warning(f"Avatar config file {self.config_file} not found, using defaults")
                self.config_data = {}
        except Exception as e:
            logger.error(f"Failed to load avatar configuration: {e}")
            self.config_data = {}
    
    def get_avatar_config(self, avatar_name: Optional[str] = None) -> Optional[AvatarConfig]:
        """Get avatar configuration by name or default."""
        if not avatar_name:
            avatar_name = self.config_data.get("default_avatar", "beyond_presence")
        
        if avatar_name not in self.config_data.get("avatars", {}):
            logger.error(f"Avatar '{avatar_name}' not found in configuration")
            return None
        
        avatar_data = self.config_data["avatars"][avatar_name]
        provider = avatar_data.get("provider", "bey")
        
        try:
            if provider == "bey":
                return AvatarFactory.create_beyond_presence_config(
                    avatar_id=avatar_data.get("avatar_id", ""),
                    participant_identity=avatar_data.get("participant_identity"),
                    participant_name=avatar_data.get("participant_name"),
                    enabled=avatar_data.get("enabled", True)
                )
            elif provider == "anam":
                return AvatarFactory.create_anam_config(
                    avatar_id=avatar_data.get("avatar_id", ""),
                    name=avatar_data.get("name", ""),
                    participant_name=avatar_data.get("participant_name"),
                    enabled=avatar_data.get("enabled", True)
                )
            elif provider == "bithuman":
                return AvatarFactory.create_bithuman_config(
                    model_path=avatar_data.get("model_path", ""),
                    enabled=avatar_data.get("enabled", True)
                )
            else:
                logger.error(f"Unsupported avatar provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create avatar configuration for {avatar_name}: {e}")
            return None
    
    def list_available_avatars(self) -> list:
        """List all available avatar names from configuration."""
        return list(self.config_data.get("avatars", {}).keys())
    
    def get_default_avatar_name(self) -> str:
        """Get the default avatar name."""
        return self.config_data.get("default_avatar", "beyond_presence")
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
