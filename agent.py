import asyncio
import json
import os
from enum import Enum
from typing import Any, List

import httpx
from dotenv import load_dotenv
from langfuse import Langfuse
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, ConversationItemAddedEvent
from livekit.plugins import noise_cancellation, openai, simli
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings

load_dotenv()


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

    class Config:
        env_file = ".env"


settings = KaiSettings()

gpt = AsyncOpenAI(api_key=settings.openai_api_key)

langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)

# Kai LLM Agent
from livekit.agents import Agent


class KaiSessionMetadata(BaseModel):
    voice_call_id: int


class KaiSessionParticipant(BaseModel):
    id: int
    name: str
    cefr_level: str
    native_language: str


class RequestAnalyseVoiceCallMessageRole(Enum):
    student = "student"
    kai = "kai"


class RequestAnalyseVoiceCallMessage(BaseModel):
    role: RequestAnalyseVoiceCallMessageRole
    content: str


class RequestAnalyseVoiceCall(BaseModel):
    messages: List[RequestAnalyseVoiceCallMessage]


class Kai(Agent):
    def __init__(self) -> None:
        prompt = langfuse.get_prompt("kai_voice_call_prompt")
        super().__init__(
            instructions=prompt.compile(),
        )


class KaiSession(AgentSession):
    def __init__(self, ctx: agents.JobContext):
        super().__init__(
            llm=openai.realtime.RealtimeModel(voice="echo"),
        )
        self.ctx = ctx
        self.metadata = KaiSessionMetadata(
            voice_call_id=int(ctx.room.name),
        )
        self.messages = RequestAnalyseVoiceCall(messages=[])
        self.participant = None

        if self.ctx.room.remote_participants:
            asyncio.create_task(self.on_participant_connected())

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

        await self.generate_reply(
            instructions=f"Student name is {self.participant.name}, their CEFR level is {self.participant.cefr_level}, their native language is {self.participant.native_language}"
        )

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
        asyncio.create_task(self.load_participant())


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
    kai_session = TesterSession(ctx)
    await kai_session.start(
        room=ctx.room,
        agent=Kai(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    avatar = simli.AvatarSession(
        simli_config=simli.SimliConfig(
            api_key=settings.simli_api_key,
            face_id=settings.simli_face_id,
        ),
    )
    await avatar.start(kai_session, room=ctx.room)

    @kai_session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        asyncio.create_task(kai_session.on_conversation_item_added(event))

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(event: Any):
        asyncio.create_task(kai_session.on_participant_disconnected())

    @ctx.room.on("participant_connected")
    def on_participant_connected(event: Any):
        asyncio.create_task(kai_session.on_participant_connected())

    await kai_session.load_participant()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
