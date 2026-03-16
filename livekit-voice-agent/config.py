from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class VoiceConfig:
    model: str
    voice: str
    speed: float = 1.0


@dataclass
class PersonaConfig:
    name: str
    greeting: str
    instructions: str
    voice: VoiceConfig
    tools: dict[str, bool] = field(default_factory=dict)


@dataclass
class TaskConfig:
    instructions: str
    greeting: str


@dataclass
class AppConfig:
    assistant: PersonaConfig
    nurse: PersonaConfig
    collect_consent: TaskConfig


CONFIG_PATH = Path(__file__).resolve().parent / "agent_config.json"


def load_app_config() -> AppConfig:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    assistant = PersonaConfig(
        name=raw["assistant"]["name"],
        greeting=raw["assistant"]["greeting"],
        instructions=raw["assistant"]["instructions"],
        voice=VoiceConfig(
            model=raw["assistant"]["voice"]["model"],
            voice=raw["assistant"]["voice"]["voice"],
            speed=raw["assistant"]["voice"].get("speed", 1.0),
        ),
        tools=raw["assistant"].get("tools", {}),
    )

    nurse = PersonaConfig(
        name=raw["nurse"]["name"],
        greeting=raw["nurse"]["greeting"],
        instructions=raw["nurse"]["instructions"],
        voice=VoiceConfig(
            model=raw["nurse"]["voice"]["model"],
            voice=raw["nurse"]["voice"]["voice"],
            speed=raw["nurse"]["voice"].get("speed", 1.0),
        ),
        tools=raw["nurse"].get("tools", {}),
    )

    collect_consent = TaskConfig(
        instructions=raw["collect_consent"]["instructions"],
        greeting=raw["collect_consent"]["greeting"],
    )

    return AppConfig(
        assistant=assistant,
        nurse=nurse,
        collect_consent=collect_consent,
    )


APP_CONFIG = load_app_config()