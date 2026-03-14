# Aloware Voice Agent Test Project

This repository contains a real-time voice agent and a simple React (Next.js) Admin UI for configuring it, built for the Aloware Engineering Test Project.

## 🚀 Setup Instructions

These instructions will get the project running locally in under 5 minutes. 

### Prerequisites
* [uv](https://github.com/astral-sh/uv) (for managing Python dependencies)
* Node.js & npm (for the Next.js frontend)
* LiveKit Cloud account and API Keys
* OpenAI / Deepgram / Cartesia API Keys (depending on your `.env` configuration)

### 1. Environment Variables
Before running the applications, set up your environment variables using the provided examples.
1. Navigate to the backend folder and copy the example file: `cp .env.example .env`
2. Fill in your LiveKit and chosen LLM/STT/TTS provider keys in the `.env` file.

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
The UI should now be running at `http://localhost:3000` (or `3001` if the port is in use).

---

## 🧠 Architecture & Decisions

### Framework Choice: Why LiveKit?
[Write here why you picked LiveKit over Pipecat]

### What I Built & Decisions Made
[Detail your implementation here. Mention the specific phone call scenario you chose, the 3 tools your agent executes, and the guardrail/safety measure you implemented. Mention that the UI edits the agent's instructions, persona, and tools without needing a database.]

### Bonus Feature
[State which ONE bonus feature you chose (Evals, MCP, Latency, or Custom) and why it excited you. Explain how you went deep into this specific feature]

### Future Improvements
[Explain what you would improve, refactor, or add if you had more than one day to work on this project.]

---

## 📹 Loom Video Demo
[Insert Link to your 5-minute Loom video here]
