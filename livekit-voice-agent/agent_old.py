# import logging
# from dataclasses import dataclass, field
# import os
# from typing import Optional

# from dotenv import load_dotenv
# from livekit import agents
# from livekit.agents import Agent, AgentServer, AgentSession, JobContext, room_io, AgentTask, ChatContext
# from livekit.plugins import noise_cancellation, silero, openai, deepgram, cartesia
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
# from livekit.agents import llm, stt, tts, inference
# from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics
# from livekit.agents import function_tool, RunContext, ToolError
# from livekit.agents import mcp
# from livekit.agents.beta.tools import EndCallTool

# from database import db


# import time

# logger = logging.getLogger(__name__)

# load_dotenv(".env")

# RECEPTIONIST_TTS = cartesia.TTS(
#     model="sonic-3",
#     voice="a167e0f3-df7e-4d52-a9c3-f949145efdab",  # Blake - male
#     speed=1.1,
# )

# NURSE_TTS = cartesia.TTS(
#     model="sonic-3",
#     voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",  # Jacqueline - female
#     speed=1.05,
# )


# @function_tool()
# async def lookup_user(context: RunContext,user_id: str,) -> dict:
#     """Look up a user's information by ID."""

#     return {"name": "John Doe", "email": "john.doe@example.com"}

# @function_tool
# async def book_medical_appointment(context: RunContext, doctor_name: str, appointment_time: str, patient_name: str) -> str:
#     """Book a medical appointment and save the details.

#     Args:
#         doctor_name: The name of the doctor for the appointment.
#         appointment_time: The confirmed date and time for the appointment in strict ISO 8601 format (e.g., '2026-03-16T09:00:00').
#         patient_name: The full name of the patient.
#     """
#     selected_doctor = None
#     # await context.session.say("Booking appointment...")
#     context.disallow_interruptions()
    
#     for doc in db.doctors:
#         if doctor_name.lower() in doc['name'].lower():
#             selected_doctor = doc
#             break

#     if not selected_doctor:
#         raise ToolError(f"Error: Couldn't find a doctor named {doctor_name}. Please ask the user to clarify the doctor's name.")

#     is_time_available = False
#     for slot in selected_doctor['available_slots']:
#         if appointment_time.lower() in slot.lower() or slot.lower() in appointment_time.lower():
#             is_time_available = True
#             appointment_time = slot 
#             break

#     if not is_time_available:
#         available_str = ", ".join(selected_doctor['available_slots'])
#         raise ToolError("Error: The time '{appointment_time}' is not available for {selected_doctor['name']}. The available times are: {available_str}. Ask the user to pick one of these.")

#     booking_id = f"BK-{len(db.bookings) + 1001}"
#     booking_record = {
#         "id": booking_id,
#         "patient_name": patient_name,
#         "doctor_name": selected_doctor['name'],
#         "time": appointment_time
#     }
    
#     db.bookings.append(booking_record)
    
#     print(f"\n--- [NEW BOOKING SAVED] ---\n{booking_record}\n---------------------------\n")

#     return f"Success! The appointment is confirmed for {patient_name} with {selected_doctor['name']} at {appointment_time}. The confirmation ID is {booking_id}."


# class CollectConsent(AgentTask[bool]):
#     def __init__(self, chat_ctx=None):
#         super().__init__(
#             instructions="""
#             Ask for recording consent and get a clear yes or no answer.
#             Be polite and professional.
#             You don't need to 
#             """,
#             chat_ctx=chat_ctx,
#             tts=NURSE_TTS
#         )

#     async def on_enter(self) -> None:
#         await self.session.generate_reply(
#             instructions="""
#             Briefly introduce yourself, then ask for permission to record
#             the call for quality assurance and training purposes.
#             Make it clear that they can decline.
#             Ask after being tranfered
#             """
#         )
    
#     @function_tool()
#     async def consent_given(self) -> None:
#         """Use this when the user gives consent to record."""
#         self.complete(True)

#     @function_tool()
#     async def consent_denied(self) -> None:
#         """Use this when the user denies consent to record."""
#         self.complete(False)
        

# class Nurse(Agent):
     
#     def __init__(self, chat_ctx: ChatContext):
#         end_call_tool = EndCallTool(
#             delete_room=True,
#             extra_description="Use this only after the triage is completed and the user says they do not need anything else.",
#             end_instructions="Thank the patient, wish them well, and politely end the call."
#         )
#         super().__init__(
#             instructions="""
#             You are a hospital triage nurse that prepares patient charts before the appointment.
#             Speak naturally and briefly.
#             Ask one question at a time.
#             After consent, start the triage immediately.
#             You must collect all four triage fields by asking the patient directly.
#             Do not call triage_the_patient until you have all four values.
#             Do not use empty strings.
#             Do not infer values from the booking context.
#             After triage_the_patient is completed, ask if the patient needs anything else.
#             If the patient says no, use the end_call tool.
#             """,
#             chat_ctx=chat_ctx,
#             tts=NURSE_TTS,
#             tools=end_call_tool.tools,
#         )
        
#     async def on_enter(self) -> None:
#         consent = await CollectConsent(chat_ctx=self.chat_ctx)
        
#         if consent:
#             await self.session.generate_reply(
#                 instructions="Thank them and start the triage by asking what symptom they are feeling."
#             )
#         else:
#             await self.session.generate_reply(
#                 instructions="Acknowledge that the call will not be recorded and start the triage by asking what symptom they are feeling."
#             )
            
#     @function_tool
#     async def triage_the_patient(self, context: RunContext, main_symptom: str, reason_for_visit: str, symptom_duration: str, symptom_severity: str,) -> str:
#         """Record the completed patient triage only after all four values were asked and answered directly by the patient.
#         Args:
#             main_symptom: The main symptom or complaint the patient is feeling.
#             reason_for_visit: The patient's reason for seeking the appointment.
#             symptom_duration: How long the symptom or issue has been happening.
#             symptom_severity: How intense or serious the symptom feels to the patient.
#         """
#         if (
#             not main_symptom.strip()
#             or not reason_for_visit.strip()
#             or not symptom_duration.strip()
#             or not symptom_severity.strip()
#         ):
#             raise ToolError("Do not call this tool until all triage answers have been collected.")
    
#         triage_id = f"TR-{len(db.triage_patient) + 1001}"
        
#         triage_record = {
#             "id": triage_id,
#             "main_symptom": main_symptom,
#             "reason_for_visit": reason_for_visit,
#             "symptom_duration": symptom_duration,
#             "symptom_severity": symptom_severity,
#         }

#         db.triage_patient.append(triage_record)

#         print(f"\n--- [NEW TRIAGE SAVED] ---\n{triage_record}\n--------------------------\n")

#         return f"Thank you. I have recorded your triage information. Your triage ID is {triage_id}."
    
        
    

# class Assistant(Agent):

    
#     def __init__(self):
#         super().__init__(
#             tools=[lookup_user],
#             instructions="""
#             You are a hospital receptionist that schedules appointments.
#             Always ask for the medical specialty first and use the tool to find available doctors.
#             Tell the user which doctors are available and ask them to choose one.
#             Once they choose a doctor, collect their preferred time and full name to book the appointment.
#             Help assist with LiveKit by searching the documentation, when users ask about Livekit
#             use the docs search tool to find accurate info.
#             Speak naturally and briefly.
#             Ask one question at a time.
#             Keep your responses concise and natural, as if having a conversation over the phone.
#             After booking an appointment use the escalate_to_nurse tool.
#             """
#         )
        
        
#     @function_tool
#     async def search_doctors_by_specialty(self, context: RunContext, specialty: str) -> str:
#         """Search for available doctors within a specific medical specialty.
#         Call this tool immediately after the user provides the specialty.

#         Args:
#             specialty: The medical specialty to search for (e.g., 'Ophthalmology', 'Cardiology', 'Neurology').
#         """
#         specialty_lower = specialty.lower().strip()
        
#         if specialty_lower not in db.specialties_db:
#             raise ToolError(f"Sorry, we don't have the {specialty} specialty. Available options are: Ophthalmology, Cardiology, and Neurology.") 
        
#         doctors = db.specialties_db[specialty_lower]
#         db.doctors = doctors
        
#         result = f"Found doctors for {specialty_lower}:\n\n"
        
#         for doc in doctors:
#             result += f"• {doc['name']}\n"
#             result += f"  Available Slots: {', '.join(doc['available_slots'])}\n"
            
#         await self.update_tools(self.tools + [book_medical_appointment])
            
#         return result
    
   
#     @function_tool
#     async def escalate_to_nurse(self, context: RunContext) -> Nurse:
#         """Trasnfer to nuser after booking an appointment"""
#         return Nurse(chat_ctx=self.chat_ctx), "Transfering you to our nurse now"
        
        

# async def entrypoint(ctx: agents.JobContext):
    
#     session = AgentSession(
#         stt=stt.FallbackAdapter(
#             [
#                deepgram.STT(model="nova-3"),
#                inference.STT.from_model_string("assemblyai/universal-streaming:en"),
#             ]
#         ),
#         llm=llm.FallbackAdapter(
#             [
#                 openai.LLM(model=os.getenv("LLM_CHOICE", "gpt-4.1-mini")),
#                 inference.LLM(model="google/gemini-2.5-flash"),
#             ]
#         ),
#         tts=RECEPTIONIST_TTS,
#         vad=silero.VAD.load(),
#         # turn_detection=MultilingualModel(),
#         preemptive_generation=True,
#         mcp_servers=[
#             mcp.MCPServerHTTP(url="https://docs.livekit.io/mcp"),
#         ]
#     )
    
#     usage_collector = metrics.UsageCollector()
#     last_eou_metrics: metrics.EOUMetrics | None = None

#     @session.on("metrics_collected")
#     def _on_metrics_collected(ev: MetricsCollectedEvent):
#         nonlocal last_eou_metrics
#         if ev.metrics.type == "eou_metrics":
#             last_eou_metrics = ev.metrics
            
#         metrics.log_metrics(ev.metrics)
#         usage_collector.collect(ev.metrics)
        
#     async def log_usage():
#         summary = usage_collector.get_summary()
#         logger.info("Usage summary: %s", summary)    
        
#     ctx.add_shutdown_callback(log_usage)
    
#     @session.on("agent_state_changed")
#     def _on_agent_state_changed(ev: AgentStateChangedEvent):
#         if ev.new_state == "speaking":
#             if last_eou_metrics:
#                 elapsed = time.time() - last_eou_metrics.timestamp
#                 logger.info(f"Time to first audio: {elapsed:.3f}s")

#     await session.start(
#         room=ctx.room,
#         agent=Assistant(),
#         room_options= room_io.RoomOptions(
#             audio_input=room_io.AudioInputOptions(
#                 noise_cancellation= noise_cancellation.BVC(),
#             ),
#         ),
#     )

#     await session.generate_reply(
#         instructions="Greet the user warmly, state you are the scheduling assistant, and ask what medical specialty they need today.'"
#     )

# if __name__ == "__main__":
#     agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))