# Conversation Collector

A reusable utility for monitoring and displaying real-time conversations between Dapr agents in multi-agent workflows.

## Rationale

When developing and demonstrating multi-agent systems, it's crucial to understand how agents interact and collaborate. While Dapr provides excellent observability through Zipkin traces and logs, these are primarily technical views. Developers and stakeholders need a human-readable view of agent conversations that shows:

1. **Real-time Agent Interactions**: See conversations as they happen between agents like Frodo, Gandalf, and Legolas
2. **Debugging Aid**: Quickly identify conversation flow issues, agent selection patterns, and response quality
3. **Demo-Friendly Display**: Showcase agent personalities and collaboration in an engaging, Slack-like format
4. **Development Monitoring**: Understand agent behavior during workflow development and testing

## Architecture Overview

The Conversation Collector follows a clean separation of concerns with two distinct layers:

### 1. Data Collection Layer
**ConversationCollector Service** - A dedicated Dapr service that:
- Subscribes to all agent pub/sub topics using Dapr's native messaging
- Captures `TriggerAction` (requests to agents) and `AgentTaskResponse` (agent replies) messages
- Parses and structures conversation data with timestamps, agent identities, and message content
- Persists conversation history to Dapr state store (Redis) for retrieval
- Exposes REST API for accessing conversation data
- Remains completely agnostic of display mechanisms

### 2. Display Clients Layer
Multiple lightweight clients that consume the ConversationCollector API:
- **Console Client**: Real-time terminal output for development debugging
- **Web Frontend**: Browser-based conversation viewer for demos and monitoring
- **Future Integrations**: Slack webhooks, Discord bots, Teams integration, custom dashboards

## Technical Approach

### Message Flow
```
Agent Workflow → Pub/Sub Topics → ConversationCollector → State Store (Redis)
                                         ↓
Console Client ← REST/WebSocket API ← ConversationCollector → Web Frontend
```

### Data Structure
The ConversationCollector processes raw Dapr messages into structured conversation data:

```json
{
  "workflow_id": "workflow_123",
  "timestamp": "2024-01-15T14:32:15Z",
  "message_type": "agent_response|agent_request|orchestrator_action",
  "agent_name": "Frodo",
  "agent_role": "Hobbit",
  "content": "The path to Mordor is treacherous, but I must carry this burden...",
  "orchestrator": "RandomOrchestrator",
  "turn_number": 2
}
```

### API Endpoints
- `GET /conversations` - Retrieve all conversation history
- `GET /conversations/latest` - Get recent messages with configurable limit
- `GET /conversations/workflow/{workflow_id}` - Get specific workflow conversation
- `WebSocket /conversations/live` - Real-time conversation updates

### Display Formats

**Console Output:**
```
[14:32:15] 🎲 RandomOrchestrator: Starting workflow "How to get to Mordor?"
[14:32:16] 🧙‍♂️ Frodo: The path to Mordor is treacherous, but I must carry this burden...
[14:32:18] 🎲 RandomOrchestrator: Selected Gandalf for next turn
[14:32:19] 🧙‍♂️ Gandalf: Young hobbit, we must plan carefully. The Enemy has many eyes...
```

**Web Interface:** Clean conversation bubbles with agent avatars, timestamps, and workflow context.

## Integration Strategy

### Non-Intrusive Design
- No modifications required to existing agent code
- Uses standard Dapr pub/sub subscription patterns
- Can be added to any multi-agent workflow by updating the dapr run configuration
- Optional service that can be started/stopped independently

### Dapr Configuration
Add to existing `dapr-*.yaml` files:
```yaml
- appID: ConversationCollector
  appDirPath: ./tools/conversation-collector/services/collector/
  command: ["python", "app.py"]
  appPort: 8005
```

### Cross-Project Reusability
- Located in `/tools/` directory for use across all quickstarts
- Configurable topic names and agent identifiers
- Modular client architecture supports multiple display mechanisms
- Can be packaged as a Docker container for easy deployment

## Development Phases

1. **Phase 1**: Core ConversationCollector service with REST API
2. **Phase 2**: Console client for immediate development utility  
3. **Phase 3**: Simple web frontend for demo and monitoring
4. **Phase 4**: Advanced features (filtering, search, multiple workflow support)
5. **Phase 5**: External integrations (Slack, Teams, etc.)

## Project Structure

```
tools/conversation-collector/
├── README.md                   # This documentation
├── requirements.txt            # Python dependencies
├── services/
│   └── collector/              # Core data collection service
│       └── app.py              # ConversationCollector Dapr service
├── clients/                    # Display clients
│   ├── console/                # Console viewer
│   │   └── app.py              # Real-time terminal output
│   └── web/                    # Web frontend
│       ├── app.py              # Flask/FastAPI web server
│       └── static/             # HTML, CSS, JS files
└── components/                 # Dapr components if needed
    └── collector-state.yaml   # State store configuration
```

## Usage

### 1. Add to Existing Workflows
Update your `dapr-*.yaml` file to include the conversation collector:

```yaml
- appID: ConversationCollector
  appDirPath: ./tools/conversation-collector/services/collector/
  command: ["../../.venv/bin/python", "app.py"]
  appPort: 8005
```

### 2. Start Console Monitor
In a separate terminal:
```bash
cd tools/conversation-collector/clients/console
python app.py
```

### 3. Start Web Interface (Optional)
```bash
cd tools/conversation-collector/clients/web
python app.py
# Open http://localhost:8006 in browser
```

## Benefits

- **Developer Experience**: Immediate visibility into agent conversations during development
- **Debugging**: Quickly identify conversation flow issues and agent behavior patterns
- **Demonstration**: Engaging way to show stakeholders how agents collaborate
- **Monitoring**: Production-ready conversation monitoring for deployed systems
- **Extensibility**: Clean architecture supports future integration requirements
- **Reusability**: One tool that works across all Dapr agents projects

This utility transforms technical pub/sub messages into human-readable conversations, bridging the gap between system internals and user understanding.