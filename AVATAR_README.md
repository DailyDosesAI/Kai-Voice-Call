# Avatar Integration System

This document explains how to use the new avatar integration system for LiveKit Agents, which follows SOLID principles and provides easy management of multiple avatar providers.

## Overview

The avatar system provides a clean, extensible way to integrate various avatar providers with your LiveKit sessions. It includes:

- **Abstract interfaces** following the Strategy pattern
- **Error handling** that won't crash your session if avatar fails
- **Configuration management** via JSON files
- **Easy switching** between different avatar providers
- **SOLID principles** implementation

## Supported Avatar Providers

The system currently supports these avatar providers from LiveKit:

- **Beyond Presence** (`bey`) - Hyper-realistic interactive avatars
- **Anam** (`anam`) - Lifelike avatars for conversational AI
- **BitHuman** (`bithuman`) - Local CPU-based avatars
- **Hedra** (`hedra`) - Coming soon
- **Simli** (`simli`) - Coming soon
- **Tavus** (`tavus`) - Coming soon

## Quick Start

### 1. Configuration

The system uses `avatar_config.json` for configuration. Here's an example:

```json
{
  "default_avatar": "beyond_presence",
  "avatars": {
    "beyond_presence": {
      "provider": "bey",
      "enabled": true,
      "avatar_id": "your_avatar_id",
      "participant_identity": "kai_test",
      "participant_name": "Kai Avatar"
    }
  }
}
```

### 2. Usage in Code

```python
from models.avatar_config_loader import AvatarConfigLoader
from models.avatar import AvatarSession as AvatarSessionManager

# Load avatar configuration
avatar_loader = AvatarConfigLoader()
avatar_config = avatar_loader.get_avatar_config()

if avatar_config:
    avatar_session = AvatarSessionManager(avatar_config)
    
    # Start avatar with error handling
    try:
        await avatar_session.start(kai_session, room=ctx.room)
        if avatar_session.is_active:
            logger.info(f"Avatar {avatar_config.provider.value} started successfully")
        else:
            logger.warning(f"Avatar failed to start, continuing without avatar")
    except Exception as e:
        logger.error(f"Avatar error: {e}, continuing without avatar")
else:
    logger.warning("No avatar configuration found, continuing without avatar")
```

## Architecture

### SOLID Principles Implementation

1. **Single Responsibility Principle**: Each class has one responsibility
   - `AvatarProvider`: Handles avatar-specific operations
   - `AvatarSession`: Manages avatar lifecycle
   - `AvatarConfigLoader`: Handles configuration loading

2. **Open/Closed Principle**: Easy to extend with new providers
   - Add new provider by implementing `AvatarProvider` interface
   - No need to modify existing code

3. **Liskov Substitution Principle**: All providers are interchangeable
   - Each provider implements the same interface
   - Can switch providers without changing client code

4. **Interface Segregation Principle**: Clean, focused interfaces
   - `AvatarProvider` has only necessary methods
   - No unnecessary dependencies

5. **Dependency Inversion Principle**: Depends on abstractions
   - High-level modules depend on `AvatarProvider` interface
   - Low-level modules implement the interface

### Class Structure

```
AvatarProvider (Abstract)
├── BeyondPresenceAvatarProvider
├── AnamAvatarProvider
├── BitHumanAvatarProvider
└── ... (other providers)

AvatarSession (Manager)
├── Manages multiple providers
├── Handles errors gracefully
└── Won't crash session

AvatarConfigLoader
├── Loads JSON configuration
├── Creates provider-specific configs
└── Manages avatar switching
```

## Configuration Management

### Avatar Manager Utility

Use the `avatar_manager.py` script to manage configurations:

```bash
# List all avatars
python avatar_manager.py list

# Show configuration for specific avatar
python avatar_manager.py show beyond_presence

# Enable an avatar
python avatar_manager.py enable anam

# Disable an avatar
python avatar_manager.py disable beyond_presence
```

### Configuration File Structure

Each avatar configuration includes:

- **provider**: The avatar provider type
- **enabled**: Whether this avatar is active
- **avatar_participant_identity**: Participant identity in the room
- **avatar_participant_name**: Display name for the avatar
- **Provider-specific fields**: Such as avatar_id, model_path, etc.

## How LiveKit Avatars Work

Based on the [LiveKit documentation](https://docs.livekit.io/agents/integrations/avatar/), virtual avatar integrations work automatically with the `AgentSession` class:

### Architecture Overview

1. **Avatar Worker**: The plugin adds a separate participant (avatar worker) to the room
2. **Audio Routing**: The agent session sends its audio output to the avatar worker instead of directly to the room
3. **Synchronized Output**: The avatar worker publishes synchronized audio + video tracks to the room
4. **Frontend Integration**: Your frontend app receives both audio and video from the avatar worker

### Frontend Integration

In your frontend code, you need to distinguish between:
- **Agent**: Your Python program running the `AgentSession`
- **Avatar Worker**: The participant publishing synchronized audio/video

```javascript
// Identify the agent and avatar worker
const agent = room.remoteParticipants.find(
  p => p.kind === Kind.Agent && p.attributes['lk.publish_on_behalf'] === null
);

const avatarWorker = room.remoteParticipants.find(
  p => p.kind === Kind.Agent && p.attributes['lk.publish_on_behalf'] === agent.identity
);
```

### React Integration

For React apps, use the `useVoiceAssistant` hook:
```javascript
const { 
  agent,        // The agent participant
  audioTrack,   // The worker's audio track
  videoTrack,   // The worker's video track
} = useVoiceAssistant();
```

## Error Handling

The system is designed to be robust:

- **Import errors**: Gracefully handles missing plugins
- **Configuration errors**: Logs errors and continues without avatar
- **Startup failures**: Logs warnings and continues session
- **Runtime errors**: Catches exceptions and maintains session stability

**Key Feature**: If an avatar fails to start, your LiveKit session continues normally without the avatar.

## Adding New Avatar Providers

To add support for a new avatar provider:

1. **Create provider class**:
```python
class NewAvatarProvider(AvatarProvider):
    async def create_session(self) -> Any:
        # Implementation here
        pass
    
    async def start(self, agent_session: AgentSession, room: agents.Room) -> bool:
        # Implementation here
        pass
    
    async def stop(self) -> None:
        # Implementation here
        pass
```

2. **Add to factory**:
```python
@staticmethod
def create_new_provider_config(
    # parameters
) -> AvatarConfig:
    return AvatarConfig(
        provider=AvatarProviderType.NEW_PROVIDER,
        # other fields
    )
```

3. **Update configuration loader**:
```python
elif provider == "new_provider":
    return AvatarFactory.create_new_provider_config(
        # parameters
    )
```

## Required Dependencies

To use avatars with LiveKit Agents, you need to install the appropriate dependencies for your chosen avatar provider. Based on the [LiveKit documentation](https://docs.livekit.io/agents/integrations/avatar/), here are the required packages:

### Installation Commands

```bash
# For Beyond Presence (recommended for your current setup)
pip install "livekit-agents[bey]~=1.2"

# For Anam
pip install "livekit-agents[anam]~=1.2"

# For BitHuman
pip install "livekit-agents[bithuman]~=1.2"

# For Hedra
pip install "livekit-agents[hedra]~=1.2"

# For Simli
pip install "livekit-agents[simli]~=1.2"

# For Tavus
pip install "livekit-agents[tavus]~=1.2"

# For multiple providers (e.g., bey + anam)
pip install "livekit-agents[bey,anam]~=1.2"
```

### Current Requirements.txt

Your current `requirements.txt` already includes:
```txt
livekit-agents[bey]~=1.2  # Beyond Presence support
livekit-agents[simli]~=1.2  # Simli support
```

### Adding New Avatar Support

To add support for a new avatar provider (e.g., Anam):

1. **Install the dependency**:
   ```bash
   pip install "livekit-agents[anam]~=1.2"
   ```

2. **Update requirements.txt**:
   ```txt
   livekit-agents[anam]~=1.2
   ```

3. **Configure in avatar_config.json**:
   ```json
   {
     "anam": {
       "provider": "anam",
       "enabled": true,
       "avatar_id": "your_anam_avatar_id",
       "name": "your_anam_avatar_name"
     }
   }
   ```

## Environment Variables

Make sure you have the required environment variables for your chosen avatar provider:

- **Beyond Presence**: `BEY_API_KEY`
- **Anam**: `ANAM_API_KEY`
- **BitHuman**: `BITHUMAN_API_SECRET`, `BITHUMAN_MODEL_PATH`
- **Hedra**: `HEDRA_API_KEY`
- **Simli**: `SIMLI_API_KEY`
- **Tavus**: `TAVUS_API_KEY`

## Best Practices

1. **Always use error handling**: The system won't crash your session, but log errors appropriately
2. **Test configurations**: Use the avatar manager to test different configurations
3. **Monitor logs**: Check avatar startup and runtime logs for issues
4. **Fallback gracefully**: Design your UI to handle cases where avatar is not available
5. **Configuration validation**: Validate avatar configurations before deployment

## Troubleshooting

### Common Issues

1. **Avatar not starting**: Check API keys and configuration
2. **Import errors**: Ensure required plugins are installed
3. **Configuration errors**: Validate JSON syntax in config file
4. **Performance issues**: Some avatars may require specific hardware/resources

### Debug Mode

Enable debug logging to see detailed avatar operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## LiveKit Starter Apps with Avatar Support

LiveKit provides several frontend starter apps with out-of-the-box support for virtual avatars:

| Platform | Description | Repository |
|----------|-------------|------------|
| **Swift** | Native iOS, macOS, and visionOS voice AI assistant built in SwiftUI | [livekit-examples/agent-starter-swift](https://github.com/livekit-examples/agent-starter-swift) |
| **Next.js** | Web voice AI assistant built with React and Next.js | [livekit-examples/agent-starter-react](https://github.com/livekit-examples/agent-starter-react) |
| **Flutter** | Cross-platform voice AI assistant app built with Flutter | [livekit-examples/agent-starter-flutter](https://github.com/livekit-examples/agent-starter-flutter) |
| **React Native** | Native voice AI assistant app built with React Native and Expo | [livekit-examples/agent-starter-react-native](https://github.com/livekit-examples/agent-starter-react-native) |
| **Android** | Native Android voice AI assistant built with Kotlin and Jetpack Compose | [livekit-examples/agent-starter-android](https://github.com/livekit-examples/agent-starter-android) |

These starter apps automatically handle the distinction between your agent and the avatar worker, making it easy to integrate avatars into your frontend applications.

## Examples

### Basic Beyond Presence Setup

```python
# In your agent.py
avatar_loader = AvatarConfigLoader()
avatar_config = avatar_loader.get_avatar_config("beyond_presence")

if avatar_config:
    avatar_session = AvatarSessionManager(avatar_config)
    await avatar_session.start(kai_session, room=ctx.room)
```

### Dynamic Avatar Switching

```python
# Switch avatars at runtime
avatar_config = avatar_loader.get_avatar_config("anam")
if avatar_config:
    # Stop current avatar
    if avatar_session.is_active:
        await avatar_session.stop()
    
    # Start new avatar
    avatar_session = AvatarSessionManager(avatar_config)
    await avatar_session.start(kai_session, room=ctx.room)
```

This system provides a robust, maintainable way to integrate avatars with your LiveKit sessions while following software engineering best practices.
