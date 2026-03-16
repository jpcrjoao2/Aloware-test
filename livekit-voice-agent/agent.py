import logging
import os
import time

import asyncio
from statistics import mean
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, AgentTask, ChatContext, room_io
from livekit.plugins import noise_cancellation, silero, openai, deepgram, cartesia
from livekit.agents import llm, stt, inference
from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import function_tool, RunContext, ToolError
from livekit.agents import mcp
from livekit.agents.beta.tools import EndCallTool

from database import db
from config import load_app_config

logger = logging.getLogger(__name__)

load_dotenv(".env")

console = Console()


def to_ms(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 1000, 2)
    
def prewarm(proc: agents.JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    
def print_llm_metrics_table(metric) -> None:
    table = Table(
        title="[bold blue]LLM Metrics[/bold blue]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    table.add_row("Speech ID", str(getattr(metric, "speech_id", "-")))
    table.add_row("Duration", f"{to_ms(metric.duration)} ms")
    table.add_row("TTFT", f"{to_ms(metric.ttft)} ms")
    table.add_row("Prompt Tokens", str(metric.prompt_tokens))
    table.add_row("Completion Tokens", str(metric.completion_tokens))
    table.add_row("Total Tokens", str(metric.total_tokens))
    table.add_row("Tokens/Second", f"{metric.tokens_per_second:.2f}")

    console.print()
    console.print(table)
    console.print()


def print_tts_metrics_table(metric) -> None:
    table = Table(
        title="[bold magenta]TTS Metrics[/bold magenta]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    table.add_row("Speech ID", str(getattr(metric, "speech_id", "-")))
    table.add_row("TTFB", f"{to_ms(metric.ttfb)} ms")
    table.add_row("Duration", f"{to_ms(metric.duration)} ms")
    table.add_row("Audio Duration", f"{to_ms(metric.audio_duration)} ms")
    table.add_row("Characters", str(metric.characters_count))
    table.add_row("Streamed", str(metric.streamed))

    console.print()
    console.print(table)
    console.print()


def print_turn_latency_table(speech_id: str, eou_ms: float | None, llm_ttft_ms: float | None, tts_ttfb_ms: float | None) -> None:
    if eou_ms is None or llm_ttft_ms is None or tts_ttfb_ms is None:
        return

    total_latency_ms = round(eou_ms + llm_ttft_ms + tts_ttfb_ms, 2)

    table = Table(
        title="[bold green]Turn Latency[/bold green]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green",
    )

    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Speech ID", speech_id)
    table.add_row("EOU Delay", f"{eou_ms} ms")
    table.add_row("LLM TTFT", f"{llm_ttft_ms} ms")
    table.add_row("TTS TTFB", f"{tts_ttfb_ms} ms")
    table.add_row("Estimated Total", f"{total_latency_ms} ms")

    console.print()
    console.print(table)
    console.print()


def print_final_latency_summary(turn_metrics: dict[str, dict], usage_summary) -> None:
    complete_turns = [
        turn for turn in turn_metrics.values()
        if turn["eou_ms"] is not None and turn["llm_ttft_ms"] is not None and turn["tts_ttfb_ms"] is not None
    ]

    total_latencies = [
        round(turn["eou_ms"] + turn["llm_ttft_ms"] + turn["tts_ttfb_ms"], 2)
        for turn in complete_turns
    ]

    avg_total = round(sum(total_latencies) / len(total_latencies), 2) if total_latencies else None
    min_total = round(min(total_latencies), 2) if total_latencies else None
    max_total = round(max(total_latencies), 2) if total_latencies else None
    under_1000_count = len([v for v in total_latencies if v < 1000])

    table = Table(
        title="[bold white on dark_green]Latency Summary[/bold white on dark_green]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
    )

    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Turns observed", str(len(turn_metrics)))
    table.add_row("Turns with full latency", str(len(complete_turns)))
    table.add_row("Average total latency", f"{avg_total} ms" if avg_total is not None else "-")
    table.add_row("Min total latency", f"{min_total} ms" if min_total is not None else "-")
    table.add_row("Max total latency", f"{max_total} ms" if max_total is not None else "-")
    table.add_row("Under 1000ms", str(under_1000_count))
    table.add_row("Usage summary", str(usage_summary))

    console.print()
    console.print(Panel.fit("Session finished", border_style="blue"))
    console.print(table)
    console.print()

    
def build_cartesia_tts(voice_cfg):
    return cartesia.TTS(
        model=voice_cfg.model,
        voice=voice_cfg.voice,
        speed=float(voice_cfg.speed),
    )
    
@function_tool()
async def book_medical_appointment(
    context: RunContext,
    doctor_name: str,
    appointment_time: str,
    patient_name: str,
) -> str:
    """Book a medical appointment and save the details.

    Args:
        doctor_name: The name of the doctor for the appointment.
        appointment_time: The confirmed date and time for the appointment in strict ISO 8601 format (e.g., '2026-03-16T09:00:00').
        patient_name: The full name of the patient.
    """
    selected_doctor = None
    context.disallow_interruptions()

    for doc in db.doctors:
        if doctor_name.lower() in doc["name"].lower():
            selected_doctor = doc
            break

    if not selected_doctor:
        raise ToolError(
            f"Error: Couldn't find a doctor named {doctor_name}. Please ask the user to clarify the doctor's name."
        )

    is_time_available = False
    for slot in selected_doctor["available_slots"]:
        if appointment_time.lower() in slot.lower() or slot.lower() in appointment_time.lower():
            is_time_available = True
            appointment_time = slot
            break

    if not is_time_available:
        available_str = ", ".join(selected_doctor["available_slots"])
        raise ToolError(
            f"Error: The time '{appointment_time}' is not available for {selected_doctor['name']}. "
            f"The available times are: {available_str}. Ask the user to pick one of these."
        )

    booking_id = f"BK-{len(db.bookings) + 1001}"
    booking_record = {
        "id": booking_id,
        "patient_name": patient_name,
        "doctor_name": selected_doctor["name"],
        "time": appointment_time,
    }

    db.bookings.append(booking_record)

    print(f"\n--- [NEW BOOKING SAVED] ---\n{booking_record}\n---------------------------\n")

    return (
        f"Success! The appointment is confirmed for {patient_name} "
        f"with {selected_doctor['name']} at {appointment_time}. "
        f"The confirmation ID is {booking_id}."
        "Booking completed successfully. Immediately call the escalate_to_nurse tool now. "
        "Do not tell the user you are transferring before calling the tool."
    )


class CollectConsent(AgentTask[bool]):
    def __init__(self, chat_ctx=None):
        app_cfg = load_app_config()
        super().__init__(
            instructions=app_cfg.collect_consent.instructions,
            chat_ctx=chat_ctx,
            tts=build_cartesia_tts(app_cfg.nurse.voice),
        )
        self.app_cfg = app_cfg

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=self.app_cfg.collect_consent.greeting
        )

    @function_tool()
    async def consent_given(self) -> None:
        """Use this when the user gives consent to record."""
        self.complete(True)

    @function_tool()
    async def consent_denied(self) -> None:
        """Use this when the user denies consent to record."""
        self.complete(False)


class Nurse(Agent):
    def __init__(self, chat_ctx: ChatContext):
        app_cfg = load_app_config()
        self.cfg = app_cfg.nurse

        end_call_tool = EndCallTool(
            delete_room=True,
            extra_description="Use this only after the triage is completed and the user says they do not need anything else.",
            end_instructions="Thank the patient, wish them well, and politely end the call.",
        )

        tools = []
        if self.cfg.tools.get("triage_the_patient"):
            tools.append(
                function_tool(
                    self.triage_the_patient,
                    name="triage_the_patient",
                )
            )
        if self.cfg.tools.get("end_call"):
            tools.extend(end_call_tool.tools)

        super().__init__(
            instructions=f"""
            You are {self.cfg.name}.
            {self.cfg.instructions}.
            """,
            chat_ctx=chat_ctx,
            tts=build_cartesia_tts(self.cfg.voice),
            tools=tools,
        )
        
        

    async def on_enter(self) -> None:
        
        await self.session.generate_reply(
            instructions=f"""I'm {self.cfg.name}. 
            greetings: {self.cfg.greeting}"""
        )
        
        consent = await CollectConsent(chat_ctx=self.chat_ctx)

        if consent:
            await self.session.generate_reply(
                instructions="Thank them and start the triage by asking what symptom they are feeling."
            )
        else:
            await self.session.generate_reply(
                instructions="Acknowledge that the call will not be recorded and start the triage by asking what symptom they are feeling."
            )

    async def triage_the_patient(
        self,
        context: RunContext,
        main_symptom: str,
        reason_for_visit: str,
        symptom_duration: str,
        symptom_severity: str,
    ) -> str:
        """Record the completed patient triage only after all four values were asked and answered directly by the patient.

        Args:
            main_symptom: The main symptom or complaint the patient is feeling.
            reason_for_visit: The patient's reason for seeking the appointment.
            symptom_duration: How long the symptom or issue has been happening.
            symptom_severity: How intense or serious the symptom feels to the patient.
        """
        if (
            not main_symptom.strip()
            or not reason_for_visit.strip()
            or not symptom_duration.strip()
            or not symptom_severity.strip()
        ):
            raise ToolError("Do not call this tool until all triage answers have been collected.")

        triage_id = f"TR-{len(db.triage_patient) + 1001}"

        triage_record = {
            "id": triage_id,
            "main_symptom": main_symptom,
            "reason_for_visit": reason_for_visit,
            "symptom_duration": symptom_duration,
            "symptom_severity": symptom_severity,
        }

        db.triage_patient.append(triage_record)

        print(f"\n--- [NEW TRIAGE SAVED] ---\n{triage_record}\n--------------------------\n")

        return "The triage has been recorded. Ask the patient if they need anything else."


class Assistant(Agent):
    def __init__(self):
        app_cfg = load_app_config()
        self.cfg = app_cfg.assistant

        tools = []
        if self.cfg.tools.get("search_doctors_by_specialty"):
            tools.append(
                function_tool(
                    self.search_doctors_by_specialty,
                    name="search_doctors_by_specialty",
                )
            )
        # if self.cfg.tools.get("book_medical_appointment"):
        #     tools.append(book_medical_appointment)
        if self.cfg.tools.get("escalate_to_nurse"):
            tools.append(
                function_tool(
                    self.escalate_to_nurse,
                    name="escalate_to_nurse",
                )
            )
        
        super().__init__(
            instructions=f"""
            You are {self.cfg.name}.
            {self.cfg.instructions}.
            """,
            tts=build_cartesia_tts(self.cfg.voice),
            tools=tools,
        )
        

    async def search_doctors_by_specialty(self, context: RunContext, specialty: str) -> str:
        """Search for available doctors within a specific medical specialty.
        Call this tool immediately after the user provides the specialty.

        Args:
            specialty: The medical specialty to search for (e.g., 'Ophthalmology', 'Cardiology', 'Neurology').
        """
        specialty_lower = specialty.lower().strip()

        if specialty_lower not in db.specialties_db:
            raise ToolError(
                f"Sorry, we don't have the {specialty} specialty. "
                f"Available options are: Ophthalmology, Cardiology, and Neurology."
            )

        doctors = db.specialties_db[specialty_lower]
        db.doctors = doctors

        result = f"Found doctors for {specialty_lower}:\n\n"

        for doc in doctors:
            result += f"• {doc['name']}\n"
            result += f"  Available Slots: {', '.join(doc['available_slots'])}\n"
            
        await self.update_tools(self.tools + [book_medical_appointment])

        return result

    async def escalate_to_nurse(self, context: RunContext) -> Nurse:
        """Trasnfer to nuser after booking an appointment"""
        return Nurse(chat_ctx=self.chat_ctx), "Transfering you to our nurse now"


async def entrypoint(ctx: agents.JobContext):
    app_cfg = load_app_config()

    session = AgentSession(
        stt=stt.FallbackAdapter(
            [
                deepgram.STT(model="nova-3"),
                inference.STT.from_model_string("assemblyai/universal-streaming:en"),
            ]
        ),
        llm=llm.FallbackAdapter(
            [
                openai.LLM(model=os.getenv("LLM_CHOICE", "gpt-4.1-mini")),
                inference.LLM(model="google/gemini-2.5-flash"),
            ]
        ),
        tts=build_cartesia_tts(app_cfg.assistant.voice),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        turn_detection=MultilingualModel(),
    )

    usage_collector = metrics.UsageCollector()
    last_eou_metrics: metrics.EOUMetrics | None = None

    turn_metrics: dict[str, dict] = {}

    def get_turn_metrics(speech_id: str) -> dict:
        if speech_id not in turn_metrics:
            turn_metrics[speech_id] = {
                "eou_ms": None,
                "llm_ttft_ms": None,
                "tts_ttfb_ms": None,
            }
        return turn_metrics[speech_id]

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        nonlocal last_eou_metrics

        usage_collector.collect(ev.metrics)
        metrics.log_metrics(ev.metrics)

        metric = ev.metrics

        if metric.type == "eou_metrics":
            last_eou_metrics = metric

            turn = get_turn_metrics(metric.speech_id)
            turn["eou_ms"] = to_ms(metric.end_of_utterance_delay)

            print_turn_latency_table(
                metric.speech_id,
                turn["eou_ms"],
                turn["llm_ttft_ms"],
                turn["tts_ttfb_ms"],
            )

        elif metric.type == "llm_metrics":
            speech_id = getattr(metric, "speech_id", None)
            if speech_id:
                turn = get_turn_metrics(speech_id)
                turn["llm_ttft_ms"] = to_ms(metric.ttft)

                print_llm_metrics_table(metric)

                print_turn_latency_table(
                    speech_id,
                    turn["eou_ms"],
                    turn["llm_ttft_ms"],
                    turn["tts_ttfb_ms"],
                )

        elif metric.type == "tts_metrics":
            speech_id = getattr(metric, "speech_id", None)
            if speech_id:
                turn = get_turn_metrics(speech_id)
                turn["tts_ttfb_ms"] = to_ms(metric.ttfb)

                print_tts_metrics_table(metric)

                print_turn_latency_table(
                    speech_id,
                    turn["eou_ms"],
                    turn["llm_ttft_ms"],
                    turn["tts_ttfb_ms"],
                )

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev: AgentStateChangedEvent):
        if ev.new_state == "speaking" and last_eou_metrics:
            elapsed = time.time() - last_eou_metrics.timestamp
            logger.info("Time to first audio: %.3fs", elapsed)

    async def print_session_summary():
        usage_summary = usage_collector.get_summary()
        print_final_latency_summary(turn_metrics, usage_summary)

    ctx.add_shutdown_callback(print_session_summary)

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions=app_cfg.assistant.greeting
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
