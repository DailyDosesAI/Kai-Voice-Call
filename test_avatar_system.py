#!/usr/bin/env python3
"""
Test script for the avatar integration system.
"""

import asyncio
import logging
from models.avatar_config_loader import AvatarConfigLoader
from models.avatar import AvatarSession as AvatarSessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_avatar_system():
    """Test the avatar system functionality."""
    print("Testing Avatar Integration System...")
    print("=" * 50)
    
    # Test configuration loading
    print("\n1. Testing Configuration Loading...")
    try:
        avatar_loader = AvatarConfigLoader()
        print(f"✓ Configuration loader created successfully")
        
        # List available avatars
        avatars = avatar_loader.list_available_avatars()
        print(f"✓ Available avatars: {avatars}")
        
        # Get default avatar
        default_avatar = avatar_loader.get_default_avatar_name()
        print(f"✓ Default avatar: {default_avatar}")
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False
    
    # Test avatar configuration creation
    print("\n2. Testing Avatar Configuration...")
    try:
        avatar_config = avatar_loader.get_avatar_config()
        if avatar_config:
            print(f"✓ Avatar configuration created successfully")
            print(f"  Provider: {avatar_config.provider.value}")
            print(f"  Enabled: {avatar_config.enabled}")
            print(f"  Participant Identity: {avatar_config.avatar_participant_identity}")
        else:
            print("✗ Failed to create avatar configuration")
            return False
            
    except Exception as e:
        print(f"✗ Avatar configuration creation failed: {e}")
        return False
    
    # Test avatar session creation
    print("\n3. Testing Avatar Session Creation...")
    try:
        avatar_session = AvatarSessionManager(avatar_config)
        print(f"✓ Avatar session created successfully")
        print(f"  Is active: {avatar_session.is_active}")
        
    except Exception as e:
        print(f"✗ Avatar session creation failed: {e}")
        return False
    
    # Test factory methods
    print("\n4. Testing Factory Methods...")
    try:
        from models.avatar import AvatarFactory, AvatarProviderType
        
        # Test Beyond Presence config
        bey_config = AvatarFactory.create_beyond_presence_config(
            avatar_id="test_id",
            participant_identity="test_identity",
            participant_name="Test Avatar"
        )
        print(f"✓ Beyond Presence config created: {bey_config.provider.value}")
        
        # Test Anam config
        anam_config = AvatarFactory.create_anam_config(
            avatar_id="test_anam_id",
            name="Test Anam Avatar"
        )
        print(f"✓ Anam config created: {anam_config.provider.value}")
        
        # Test BitHuman config
        bithuman_config = AvatarFactory.create_bithuman_config(
            model_path="./test_model.imx"
        )
        print(f"✓ BitHuman config created: {bithuman_config.provider.value}")
        
    except Exception as e:
        print(f"✗ Factory methods failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Avatar system is working correctly.")
    return True


def test_avatar_manager():
    """Test the avatar manager utility."""
    print("\nTesting Avatar Manager Utility...")
    print("=" * 50)
    
    try:
        from avatar_manager import list_avatars, show_avatar_config
        
        # Test listing avatars
        print("\n1. Testing avatar listing...")
        avatars = list_avatars()
        print(f"✓ Avatar listing works: {len(avatars)} avatars found")
        
        # Test showing avatar config
        if avatars:
            print(f"\n2. Testing avatar config display...")
            show_avatar_config(avatars[0])
            print(f"✓ Avatar config display works")
        
        print("\n✓ Avatar manager utility tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Avatar manager utility tests failed: {e}")
        return False


def main():
    """Main test function."""
    print("Avatar Integration System Test Suite")
    print("=" * 50)
    
    # Test core system
    core_success = asyncio.run(test_avatar_system())
    
    # Test utility
    utility_success = test_avatar_manager()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Core System: {'✓ PASSED' if core_success else '✗ FAILED'}")
    print(f"Utility: {'✓ PASSED' if utility_success else '✗ FAILED'}")
    
    if core_success and utility_success:
        print("\n🎉 All tests passed! Your avatar system is ready to use.")
        print("\nNext steps:")
        print("1. Configure your avatar in avatar_config.json")
        print("2. Set required environment variables")
        print("3. Run your agent with: python agent.py")
        print("4. Use avatar_manager.py to manage configurations")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return core_success and utility_success


if __name__ == "__main__":
    main()
