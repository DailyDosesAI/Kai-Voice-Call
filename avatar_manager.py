#!/usr/bin/env python3
"""
Avatar Manager - Utility script for managing avatar configurations.
"""

import json
import logging
from pathlib import Path
from models.avatar_config_loader import AvatarConfigLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def list_avatars():
    """List all available avatars."""
    loader = AvatarConfigLoader()
    avatars = loader.list_available_avatars()
    default = loader.get_default_avatar_name()
    
    print(f"Available avatars (default: {default}):")
    for avatar in avatars:
        print(f"  - {avatar}")
    
    return avatars


def show_avatar_config(avatar_name: str):
    """Show configuration for a specific avatar."""
    loader = AvatarConfigLoader()
    config = loader.get_avatar_config(avatar_name)
    
    if config:
        print(f"Configuration for avatar '{avatar_name}':")
        print(f"  Provider: {config.provider.value}")
        print(f"  Enabled: {config.enabled}")
        print(f"  Participant Identity: {config.avatar_participant_identity}")
        print(f"  Participant Name: {config.avatar_participant_name}")
        
        if config.provider.value == "bey":
            print(f"  Avatar ID: {config.bey_avatar_id}")
        elif config.provider.value == "anam":
            print(f"  Avatar ID: {config.anam_avatar_id}")
            print(f"  Name: {config.anam_name}")
        elif config.provider.value == "bithuman":
            print(f"  Model Path: {config.bithuman_model_path}")
    else:
        print(f"Avatar '{avatar_name}' not found or invalid configuration")


def enable_avatar(avatar_name: str):
    """Enable a specific avatar."""
    config_file = Path("avatar_config.json")
    
    if not config_file.exists():
        print("Avatar configuration file not found")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if avatar_name in config.get("avatars", {}):
        # Disable all avatars first
        for avatar in config["avatars"]:
            config["avatars"][avatar]["enabled"] = False
        
        # Enable the specified avatar
        config["avatars"][avatar_name]["enabled"] = True
        config["default_avatar"] = avatar_name
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Avatar '{avatar_name}' enabled and set as default")
    else:
        print(f"Avatar '{avatar_name}' not found")


def disable_avatar(avatar_name: str):
    """Disable a specific avatar."""
    config_file = Path("avatar_config.json")
    
    if not config_file.exists():
        print("Avatar configuration file not found")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if avatar_name in config.get("avatars", {}):
        config["avatars"][avatar_name]["enabled"] = False
        
        # If this was the default avatar, set a new default
        if config.get("default_avatar") == avatar_name:
            for avatar, avatar_config in config["avatars"].items():
                if avatar_config.get("enabled", False):
                    config["default_avatar"] = avatar
                    break
            else:
                # No enabled avatars, set first one as default
                config["default_avatar"] = list(config["avatars"].keys())[0]
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Avatar '{avatar_name}' disabled")
    else:
        print(f"Avatar '{avatar_name}' not found")


def main():
    """Main function for the avatar manager."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python avatar_manager.py <command> [avatar_name]")
        print("Commands:")
        print("  list                    - List all available avatars")
        print("  show <avatar_name>      - Show configuration for an avatar")
        print("  enable <avatar_name>    - Enable an avatar and set as default")
        print("  disable <avatar_name>   - Disable an avatar")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_avatars()
    elif command == "show":
        if len(sys.argv) < 3:
            print("Please specify an avatar name")
            return
        show_avatar_config(sys.argv[2])
    elif command == "enable":
        if len(sys.argv) < 3:
            print("Please specify an avatar name")
            return
        enable_avatar(sys.argv[2])
    elif command == "disable":
        if len(sys.argv) < 3:
            print("Please specify an avatar name")
            return
        disable_avatar(sys.argv[2])
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
