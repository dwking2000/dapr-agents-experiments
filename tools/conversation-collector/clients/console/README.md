# Console Client

A beautiful terminal interface for monitoring real-time agent conversations in Slack-like format.

## Features

- 🎭 **Real-time Display**: Live agent conversations with automatic updates
- 🌈 **Color-coded Agents**: Each agent (Frodo, Gandalf, Legolas) has unique colors and emojis
- 📊 **Live Statistics**: Message counts, active workflows, and agent activity
- ⏰ **Timestamps**: Human-readable time stamps for each message
- 🔄 **Auto-refresh**: Updates every 0.5 seconds for smooth real-time experience
- 📱 **Responsive**: Adapts to terminal size with scrolling message history

## Agent Styling

- 🤖 **Agents** - Automatically assigned unique colors and emojis from palette
- 🎲 **RandomOrchestrator** - Magenta (dice emoji)
- 🔄 **RoundRobinOrchestrator** - Cyan (cycle emoji)
- 🧠 **LLMOrchestrator** - Red (brain emoji)

New agents are dynamically assigned colors from: blue, green, yellow, magenta, cyan, red, bright_blue, bright_green

## Usage

### Quick Start

```bash
# Navigate to the console client directory
cd tools/conversation-collector/clients/console

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the monitor
python app.py
```

### Alternative Launcher

```bash
# Use the launcher script
python monitor.py
```

### Command Line Options

```bash
# Specify custom API endpoints
python app.py --api-url http://localhost:8005 --ws-url ws://localhost:8005

# Show help
python app.py --help
```

## Prerequisites

1. **ConversationCollector Service**: Must be running on localhost:8005
2. **Multi-agent Workflow**: Must have agent conversations happening
3. **Terminal**: Works best in terminals that support colors and emojis

## Display Layout

```
┌─────────────────────────────────────────────────────────┐
│                 🎭 Dapr Agents Conversation Monitor       │
│                                              ● LIVE     │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                    Messages (181 total)                  │
│                                                         │
│ [14:32:15] 🧙‍♂️ Frodo #2 💬: The path to Mordor is...     │
│ [14:32:18] 🧙‍♂️ Gandalf #3 💬: Young hobbit, we must...   │
│ [14:32:21] 🏹 Legolas #4 💬: My keen eyes see the...      │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                      Statistics                         │
│                                                         │
│ Total Messages:        181                              │
│ Active Workflows:        3                              │
│ Active Agents:           3                              │
│ 🧙‍♂️ Frodo:              67                              │
│ 🧙‍♂️ Gandalf:            58                              │
│ 🏹 Legolas:              56                              │
└─────────────────────────────────────────────────────────┘
```

## Keyboard Controls

- **Ctrl+C**: Gracefully shutdown the monitor
- **Terminal resize**: Automatically adapts to new size

## Troubleshooting

### "Cannot connect to ConversationCollector API"
- Ensure ConversationCollector service is running: `curl http://localhost:8005/health`
- Check if port 8005 is available
- Verify Dapr agents workflow is running

### "WebSocket connection error"
- ConversationCollector WebSocket endpoint may be unavailable
- Monitor will retry connection automatically every 5 seconds

### Display Issues
- Ensure terminal supports Unicode emojis and colors
- Try a different terminal (iTerm2, Terminal.app, Windows Terminal)
- Increase terminal size for better display