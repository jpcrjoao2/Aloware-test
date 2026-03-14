# Aloware Voice Agent Test Project

This repository contains a real-time voice agent and a simple React (Next.js) Admin UI for configuring it.

## 🚀 Setup Instructions

### Prerequisites
* [uv](https://github.com/astral-sh/uv) (for managing Python dependencies)
* Node.js & npm (for the Next.js frontend)
* LiveKit Cloud account and API Keys
* OpenAI / Deepgram / Cartesia API Keys (.env)

### 1. Environment Variables
Before running the applications, set up your environment variables using the provided examples.

**Backend:**
1. Navigate to the backend folder (`livekit-voice-agente`) and copy the example file: `cp .env.example .env`
2. Fill in your LiveKit and chosen LLM/STT/TTS provider keys in the `.env` file.

**Frontend:**
1. Navigate to the frontend folder (`UI/my-app`) and copy the example file: `cp .env.example .env.local` (or `.env`)
2. Fill in the required frontend environment variables (like your LiveKit URLs/keys).

### 2. Backend Setup (LiveKit Voice Agent)
Open a terminal and run the following commands to install dependencies, download the necessary models, and start the agent:

```bash
cd livekit-voice-agent
uv init livekit-voice-agent --bare
uv add "livekit-agents[silero,turn-detector,mcp]~=1.3" "livekit-plugins-noise-cancellation~=0.2" livekit-plugins-openai livekit-plugins-deepgram python-dotenv rich
uv run python agent.py download-files
uv run python agent.py dev
```

### 3. Frontend Setup (React / Next.js Admin UI)
Open a **new** terminal window and run the following commands to start the configuration UI:


```bash
cd UI/my-app/
npm i
npm run dev
```
The UI should now be running at `http://localhost:3000`.

If you want to explore or change the Cartesia voice models used by the agents via the Admin UI or configuration, you can find the available voice IDs in the official documentation here:
[Cartesia TTS Models - LiveKit Docs](https://docs.livekit.io/agents/models/tts/cartesia/)

---

## 🧠 Architecture & Decisions

### Framework Choice: Why LiveKit?
I chose LiveKit over Pipecat because, after reviewing the job description and seeing LiveKit mentioned, I decided to dive deep into their ecosystem. The experience was excellent: their documentation is thorough, and the available online resources, tutorials, and community support made the learning curve much smoother. Since I had already started familiarizing myself with LiveKit's architecture and was enjoying the developer experience, it made perfect sense to continue using it for this project rather than pivoting to Pipecat.

### What I Built & Decisions Made
I built a two-agent healthcare system: a **Scheduling Assistant** and a **Triage Nurse**. I wanted to avoid building a generic, single-purpose bot, so I designed a multi-step scenario that requires a handoff between two distinct personas.

**The Scenario & Tools:**
1.  **Search Doctors:** The user asks for a specific medical specialty (e.g., Cardiology, Neurology). The Assistant searches a mock database and returns available doctors and time slots.
2.  **Book Appointment:** The user selects a doctor and time. The Assistant collects their name, confirms the slot, and generates a booking ID.
3.  **Escalate to Nurse:** Once the booking is confirmed, the Assistant automatically calls a tool to transfer the call to the Triage Nurse.
4.  **Triage Patient (Nurse):** The Nurse asks the patient for their main symptom, reason for the visit, symptom duration, and severity, saving this to a triage database.

**Guardrails & Safety Measures:**
* **Mandatory Search Before Booking:** Initially, the LLM tried to book appointments without checking availability. I implemented a guardrail where the booking tool is only injected into the context *after* the doctor search tool is executed successfully.
* **Data Standardization:** The LLM would sometimes output dates in conversational formats like "next Wednesday". I enforced strict parameter validation to ensure the data matched the exact format expected by the database.
* **Preventing Hallucinations in Triage:** During early tests, the Nurse agent inferred the patient's symptoms based on the chosen doctor's specialty (e.g., assuming heart issues for a Cardiologist) and executed the triage tool with empty or assumed strings. I implemented strict instructions and validation to ensure the Nurse *must* ask the patient directly for all four triage parameters before calling the tool.
* **Context Isolation on Handoff:** When transferred, the Nurse initially repeated the Assistant's confirmation messages. I adjusted the prompt context so the Nurse starts directly with the triage introduction without repeating the previous agent's dialog.

### Bonus Feature
I chose to focus on **Latency**. Minimizing latency in voice agents is fascinating because human conversations are highly sensitive to delay. In a text chat, an 800ms delay is barely noticeable, but in a voice call, an 800ms pause creates awkward silences, causing users to think the agent didn't hear them, leading to interruptions and a poor user experience.

To optimize and measure latency, I implemented several strategies:
* **Pre-warming VAD:** I implemented VAD pre-warming so the model is loaded into memory before the call starts, reducing initial startup time.
* **Preemptive Generation:** I enabled `preemptive_generation`, which streams context to the LLM while the user is still speaking. This drastically reduces the Time to First Token (TTFT) when the user finishes their sentence.
* **Turn Detection (Multilingual Model):** I used the multilingual turn detector to accurately predict the End of Utterance (EOU). This prevents the agent from interrupting the user when they take natural conversational pauses (like saying "I think I want..." and pausing to think), which would otherwise ruin the context window.
* **Rich Metrics Logging:** I utilized LiveKit's `metrics` module and the `Rich` library to capture and display detailed tables in the console. This allowed me to track Time to First Audio, Time to First Token, End of Utterance delays, and the percentage of turns completed in under 1000ms.

### Future Improvements
If I had more time, I would focus on the following:
* **Consistency in Latency:** While I achieved low latency on average, the response times can still be inconsistent depending on the complexity of the LLM's reasoning. I would investigate ways to standardize response times to make the conversation feel more rhythmic and predictable.
* **Expanded Test Coverage:** I would add automated evaluations to test edge cases, such as users trying to book appointments for specialties that don't exist or refusing to answer the triage questions.

---

## 📹 Loom Video Demo
[Watch the 5-minute Loom Demo Here](https://www.loom.com/share/a340da86e43842ab93889f95b485896d)
