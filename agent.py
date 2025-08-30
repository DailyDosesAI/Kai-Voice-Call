import asyncio
import json
import logging
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, List
from typing import Optional

import httpx
from dotenv import load_dotenv
from langfuse import Langfuse
from livekit import agents
from livekit.agents import Agent
from livekit.agents import AgentSession, RoomInputOptions
from livekit.agents import ConversationItemAddedEvent
from livekit.plugins import noise_cancellation, openai
from livekit.rtc import RpcInvocationData
from openai import AsyncOpenAI
from openai.types.beta.realtime.session import TurnDetection
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from models.language_level import LanguageLevel
from avatar.avatar import AvatarSession as AvatarSessionManager
from avatar.avatar_config_loader import AvatarConfigLoader

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptSettings(BaseModel):
    voice_call_prompt_a: str
    voice_call_prompt_b_and_c: str

    @classmethod
    def load_from_file(cls, path: str):
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Prompt file {p} not found")
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


class KaiSettings(BaseSettings):
    openai_api_key: str

    livekit_api_key: str
    livekit_api_secret: str
    livekit_url: str

    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str

    kai_api_base_url: str
    kai_api_secret_key: str

    simli_api_key: str
    simli_face_id: str

    prompt: PromptSettings = Field(
        default_factory=lambda: PromptSettings.load_from_file(os.getenv("PROMPTS_FILE", "prompts.json")))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = KaiSettings()

gpt = AsyncOpenAI(api_key=settings.openai_api_key)

langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


class KaiSessionMetadata(BaseModel):
    voice_call_id: int


class KaiSessionParticipant(BaseModel):
    id: int
    name: Optional[str] = None
    cefr_level: Optional[str] = None
    native_language: Optional[str] = None


class RequestAnalyseVoiceCallMessageRole(Enum):
    student = "student"
    kai = "kai"


class RequestAnalyseVoiceCallMessage(BaseModel):
    role: RequestAnalyseVoiceCallMessageRole
    content: str


class RequestAnalyseVoiceCall(BaseModel):
    messages: List[RequestAnalyseVoiceCallMessage]


class Kai(Agent):
    def __init__(self, *args, **kwargs) -> None:
        prompt = langfuse.get_prompt("kai_voice_call_prompt")
        if not 'instructions' in kwargs:
            kwargs['instructions'] = prompt.compile()
        super().__init__(*args, **kwargs)

    async def adjust_speed(self, speed: str):
        if speed not in {"slow", "normal"}:
            return "Invalid speed. Use 'slow' or 'normal'."

        base_instructions = self.instructions or ""
        cleaned_instructions = re.sub(r"\n{1,2}System speed setting:.*\Z", "", base_instructions, flags=re.S)
        if speed == "slow":
            speed_guidance = (
                "Speaking speed: slow. Speak clearly at a relaxed pace; prefer shorter sentences and brief pauses."
            )
            new_instructions = f"{cleaned_instructions}\n\nSystem speed setting: {speed_guidance}"
        else:
            new_instructions = f"{cleaned_instructions}"
        await self.update_instructions(new_instructions)


class KaiSession(AgentSession):
    def __init__(self, ctx: agents.JobContext):
        super().__init__(
            llm=openai.realtime.RealtimeModel(voice="echo", turn_detection=TurnDetection(
                type="semantic_vad",
                # silence_duration_ms= 1500  # wait 1.5 seconds after you stop talking
            )),
        )
        self.ctx = ctx
        self.metadata = KaiSessionMetadata(
            voice_call_id=int(ctx.room.name),
        )
        self.messages = RequestAnalyseVoiceCall(messages=[])
        self.participant = None

        if self.ctx.room.remote_participants:
            asyncio.create_task(self.on_participant_connected())

    async def get_prompt(self) -> str:
        if not self.participant:
            raise ValueError("Student is not set")

        voice_call_prompt_id = settings.prompt.voice_call_prompt_a if self.participant.cefr_level in [LanguageLevel.A1,
                                                                                                      LanguageLevel.A2] else settings.prompt.voice_call_prompt_b_and_c
        voice_call_prompt = langfuse.get_prompt(voice_call_prompt_id)

        return voice_call_prompt.compile(
            user_name=self.participant.name if self.participant.name else "<UNKNOWN>",
            user_cefr_level=(
                self.participant.cefr_level if self.participant.cefr_level else "<UNKNOWN>"
            ),
            user_native_language=(
                self.participant.native_language
                if self.participant.native_language
                else "<UNKNOWN>"
            ),
        )

    async def load_participant(self):
        if self.participant is not None:
            return
        for _, participant in self.ctx.room.remote_participants.items():
            self.participant = KaiSessionParticipant.model_validate_json(
                participant.metadata
            )
            break

        if self.participant is None:
            return

    async def _analyze_messages(self, messages: RequestAnalyseVoiceCall):
        if self.participant is None:
            return

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.kai_api_base_url}/kai/voice-call/{self.metadata.voice_call_id}/analyze/",
                    json=messages.model_dump(mode="json"),
                    headers={"Authorization": f"ApiKey {settings.kai_api_secret_key}"},
                )
                response.raise_for_status()
            except Exception as e:
                print(f"while analyzing conversation got {e}")
                # TODO: catch properly and log properly

    async def on_conversation_item_added(self, event: ConversationItemAddedEvent):
        asyncio.create_task(self.load_participant())
        if len(self.messages.messages) >= 4:
            await self._analyze_messages(self.messages)
            self.messages.messages = []

        if event.item.role == "user":
            self.messages.messages.append(
                RequestAnalyseVoiceCallMessage(
                    role=RequestAnalyseVoiceCallMessageRole.student,
                    content="\n".join(event.item.content),
                )
            )
        elif event.item.role == "assistant":
            self.messages.messages.append(
                RequestAnalyseVoiceCallMessage(
                    role=RequestAnalyseVoiceCallMessageRole.kai,
                    content="\n".join(event.item.content),
                )
            )

    async def on_participant_disconnected(self):
        await self._analyze_messages(self.messages)
        self.messages.messages = []

    async def on_participant_connected(self):
        await self.load_participant()
        await self.current_agent.update_instructions(await self.get_prompt())


class TesterSession(KaiSession):
    def __init__(self, ctx: agents.JobContext):
        super().__init__(ctx)
        os.makedirs("temp", exist_ok=True)
        self.file_name = f"temp/voice_call_{ctx.room.name}.jsonl"
        self.conversation = list()

    async def on_conversation_item_added(self, event: ConversationItemAddedEvent):
        await super().on_conversation_item_added(event)
        if event.item.role == "user":
            self.conversation.append(f"Student: {event.item.content[0]}")
        elif event.item.role == "assistant":
            self.conversation.append(f"Kai: {event.item.content[0]}")

    async def on_participant_disconnected(self):
        await super().on_participant_disconnected()
        if self.conversation:
            with open(self.file_name, "w") as out:
                out.write(json.dumps({"conversation": self.conversation}) + "\n")
            try:
                await gpt.files.create(file=open(self.file_name, "rb"), purpose="evals")
            except Exception as e:
                print(f"while uploading to gpt got {e}")
                # TODO: catch properly and log properly
            os.remove(self.file_name)
            self.conversation.clear()


# Entrypoint
async def entrypoint(ctx: agents.JobContext):
    kai_session = KaiSession(ctx)

    await kai_session.start(
        room=ctx.room,
        agent=Kai(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    @kai_session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        asyncio.create_task(kai_session.on_conversation_item_added(event))

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(event: Any):
        asyncio.create_task(kai_session.on_participant_disconnected())

    @ctx.room.on("participant_connected")
    def on_participant_connected(event: Any):
        asyncio.create_task(kai_session.on_participant_connected())

    @ctx.room.local_participant.register_rpc_method("set_voice_speed")
    async def adjust_speed_rpc(data: RpcInvocationData) -> str:
        speed = json.loads(data.payload).get("preset")
        normalized = (speed or "").strip().lower()
        if normalized not in {"slow", "normal"}:
            return "Invalid speed. Use 'slow' or 'normal'."

        if normalized == "slow":
            await kai_session.current_agent.adjust_speed(speed=speed)
            kai_session.llm.update_options(speed=0.7)
        else:
            await kai_session.current_agent.adjust_speed(speed=speed)
            kai_session.llm.update_options(speed=1)

    # Create and start avatar using the configuration loader
    avatar_loader = AvatarConfigLoader()
    avatar_config = avatar_loader.get_avatar_config()
    
    if avatar_config:
        avatar_session = AvatarSessionManager(avatar_config)
        
        # Start avatar with error handling - won't crash the session if avatar fails
        try:
            await avatar_session.start(kai_session, room=ctx.room)
            if avatar_session.is_active:
                logger.info(f"Avatar {avatar_config.provider.value} started successfully")
            else:
                logger.warning(f"Avatar {avatar_config.provider.value} failed to start, continuing without avatar")
        except Exception as e:
            logger.error(f"Avatar error: {e}, continuing without avatar")
    else:
        logger.warning("No avatar configuration found, continuing without avatar")
    
    await kai_session.load_participant()
    await kai_session.generate_reply(instructions="start")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
