# Web Client

A modern, responsive web interface for monitoring real-time agent conversations with beautiful UI and powerful features.

## Features

### 🎭 **Real-time Display**
- Live agent conversations with automatic updates via WebSocket
- Beautiful message cards with smooth animations
- Auto-scroll to new messages (toggleable)

### 🌈 **Dynamic Styling**
- Automatically assigns unique colors to agents as they appear
- Special emojis for orchestrators (🎲 🔄 🧠)
- Generic emojis for agents (🤖 🔧 ⚡ 🔮 🚀 💎 🎯 ⭐)
- Color-coded message borders and agent names

### 📊 **Live Statistics**
- Total message count
- Active workflows and agents
- Individual agent message counts
- Sortable agent list with activity

### 🎛️ **Advanced Controls**
- Filter conversations by specific agent
- Clear all messages
- Export conversations to JSON
- Responsive design for desktop and mobile

### ⚙️ **Customizable Settings**
- Toggle timestamps display
- Toggle agent roles display
- Configure maximum messages to display (10-1000)
- Settings persist in browser localStorage

## Usage

### Quick Start

1. **Ensure ConversationCollector service is running** on localhost:8005

2. **Open the web client** in your browser:
   ```bash
   # Option 1: Open directly
   open index.html
   
   # Option 2: Serve with Python (recommended)
   python3 -m http.server 8080
   # Then visit: http://localhost:8080
   
   # Option 3: Serve with Node.js
   npx http-server -p 8080
   # Then visit: http://localhost:8080
   ```

3. **Start agent workflows** to see conversations in real-time

### API Endpoints Used

- `GET /health` - Connection health check
- `GET /conversations/latest?limit=50` - Initial message loading
- `WebSocket /conversations/live` - Real-time message updates

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  🎭 Agent Conversation Monitor              ● Connected         │
└─────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────┐ ┌─────────────────────────────┐
│  💬 Live Conversations           │ │  📊 Statistics              │
│  ┌─────────────────────────────┐ │ │                             │
│  │ 🤖 Agent1 #2 💬: Processing │ │ │  Total Messages:      42    │
│  │ Task completed successfully │ │ │  Active Workflows:     2    │
│  │                            │ │ │  Active Agents:        3    │
│  │ 🔧 Agent2 #3 💬: Analyzing │ │ │                             │
│  │ Data patterns detected...   │ │ │  🤖 Agent1:           15    │
│  │                            │ │ │  🔧 Agent2:           14    │
│  │ ⚡ Agent3 #4 💬: Results   │ │ │  ⚡ Agent3:           13    │
│  └─────────────────────────────┘ │ │                             │
│  ☑ Auto-scroll to new messages   │ └─────────────────────────────┘
└──────────────────────────────────┘ ┌─────────────────────────────┐
                                     │  🎛️ Controls                │
                                     │                             │
                                     │  [Clear Messages]           │
                                     │  [Export Conversations]     │
                                     │                             │
                                     │  Filter: [All Agents ▼]    │
                                     └─────────────────────────────┘
                                     ┌─────────────────────────────┐
                                     │  ⚙️ Settings                │
                                     │                             │
                                     │  ☑ Show timestamps          │
                                     │  ☑ Show agent roles         │
                                     │  Max messages: [100]        │
                                     └─────────────────────────────┘
```

## Message Display Format

Each message shows:
- **Agent emoji and name** (color-coded)
- **Agent role** (if available, toggleable)
- **Turn number** (conversation context)
- **Message type indicator** (📤 💬 ⚡ 🚀 🏁)
- **Timestamp** (toggleable)
- **Full message content** (truncated if very long)

## Responsive Design

- **Desktop**: Full sidebar with all panels
- **Tablet**: Sidebar converts to grid layout below messages
- **Mobile**: Single column layout with collapsible panels

## Browser Compatibility

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers with WebSocket support

## Configuration

The web client automatically detects the ConversationCollector service at:
- **API**: `http://localhost:8005`
- **WebSocket**: `ws://localhost:8005`

To use different endpoints, modify the `apiUrl` and `wsUrl` variables in `app.js`.

## Local Storage

Settings are automatically saved to browser localStorage:
- Auto-scroll preference
- Show timestamps setting
- Show agent roles setting
- Maximum messages display count

## Troubleshooting

### "Cannot connect to ConversationCollector API"
- Ensure ConversationCollector service is running on port 8005
- Check browser console for CORS errors
- Try serving the web client via HTTP server instead of file:// protocol

### Messages not updating in real-time
- Check WebSocket connection status in header
- ConversationCollector service may be down
- Browser may have blocked WebSocket connections

### Styling issues
- Ensure all CSS files are loading correctly
- Check browser developer tools for CSS errors
- Try hard refresh (Ctrl+F5 / Cmd+Shift+R)

## Performance

- Automatically limits messages to prevent memory issues
- Efficient DOM updates for smooth real-time experience
- Lazy loading of historical messages
- Optimized CSS animations and transitions