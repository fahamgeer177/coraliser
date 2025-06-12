### LiveKit Restaurant Agent (with Central Coordinator Prompt & Coral MCP Integration)

#### Dependencies Installation

```bash
# Install core dependencies and all required plugins
pip install "livekit-agents[openai,cartesia,deepgram,silero,mcp]" python-dotenv duckduckgo-search
```

#### API Keys and Configuration

Create a `.env` file in your working directory and set the following environment variables as needed by your STT/LLM/TTS providers:

```
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
# ...add others as needed
```

#### Running the Agent

```bash
python restaurant_agent.py console
```

- For LiveKit integration, set these environment variables:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_livekit_api_key
  LIVEKIT_API_SECRET=your_livekit_api_secret
  ```
- For development mode (hot reload, multi-agent support):
  ```bash
  python restaurant_agent.py dev
  ```
- For production:
  ```bash
  python restaurant_agent.py start
  ```

#### Notes

- The agent now acts as a central coordinator, using the new prompt.
- Coral MCP server is connected at:
  ```
  http://localhost:5555/devmode/exampleApplication/privkey/session1/sse?waitForAgents=1&agentId=voice_assistant&agentDescription=You+are+a+helpful+voice+AI+assistant.
  ```
- Make sure the MCP server is running and accessible at the above URL.

---

**You can use the above `restaurant_agent.py` directly. All modifications are included and ready to run.**
