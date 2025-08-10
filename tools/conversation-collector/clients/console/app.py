#!/usr/bin/env python3
"""
ConversationCollector Console Client

A beautiful terminal interface for monitoring real-time agent conversations.
Displays conversations in a Slack-like format with colors, emojis, and timestamps.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import websockets
import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.table import Table
from rich.spinner import Spinner
from rich import box
from rich.align import Align


class ConversationConsole:
    """Console client for displaying agent conversations."""
    
    def __init__(self, api_url: str = "http://localhost:8005", ws_url: str = "ws://localhost:8005"):
        self.api_url = api_url
        self.ws_url = ws_url
        self.console = Console()
        self.messages = []
        self.is_running = False
        
        # Dynamic agent styling - assigns colors to agents as they appear
        self.agent_styles = {}
        self.color_palette = [
            {"emoji": "🤖", "color": "blue", "role_color": "dim blue"},
            {"emoji": "🔧", "color": "green", "role_color": "dim green"},
            {"emoji": "⚡", "color": "yellow", "role_color": "dim yellow"},
            {"emoji": "🔮", "color": "magenta", "role_color": "dim magenta"},
            {"emoji": "🚀", "color": "cyan", "role_color": "dim cyan"},
            {"emoji": "💎", "color": "red", "role_color": "dim red"},
            {"emoji": "🎯", "color": "bright_blue", "role_color": "dim bright_blue"},
            {"emoji": "⭐", "color": "bright_green", "role_color": "dim bright_green"},
        ]
        self.next_color_index = 0
        
        # Special styling for orchestrators
        self.orchestrator_styles = {
            "RandomOrchestrator": {"emoji": "🎲", "color": "magenta", "role_color": "dim magenta"},
            "RoundRobinOrchestrator": {"emoji": "🔄", "color": "cyan", "role_color": "dim cyan"},
            "LLMOrchestrator": {"emoji": "🧠", "color": "red", "role_color": "dim red"},
        }
        
        # Default style for unknown agents
        self.default_style = {"emoji": "🤖", "color": "white", "role_color": "dim white"}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.is_running = False
        self.console.print("\n[dim]Shutting down gracefully...[/dim]")
        sys.exit(0)
    
    def _get_agent_style(self, agent_name: Optional[str]) -> Dict[str, str]:
        """Get styling information for an agent, assigning new colors dynamically."""
        if not agent_name:
            return self.default_style
            
        # Check if it's a known orchestrator
        if agent_name in self.orchestrator_styles:
            return self.orchestrator_styles[agent_name]
            
        # If we've seen this agent before, return their assigned style
        if agent_name in self.agent_styles:
            return self.agent_styles[agent_name]
            
        # Assign a new color to this agent
        style = self.color_palette[self.next_color_index % len(self.color_palette)]
        self.agent_styles[agent_name] = style
        self.next_color_index += 1
        
        return style
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return "??:??:??"
    
    def _format_message(self, message: Dict[str, Any]) -> Text:
        """Format a single message for display."""
        agent_name = message.get("agent_name", "Unknown")
        agent_role = message.get("agent_role", "")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        turn_number = message.get("turn_number", 0)
        message_type = message.get("message_type", "")
        
        style = self._get_agent_style(agent_name)
        formatted_time = self._format_timestamp(timestamp)
        
        # Create the message text
        text = Text()
        
        # Add timestamp
        text.append(f"[{formatted_time}] ", style="dim")
        
        # Add emoji and agent name
        text.append(f"{style['emoji']} ", style=style['color'])
        text.append(f"{agent_name}", style=f"bold {style['color']}")
        
        # Add role if available
        if agent_role and agent_role.lower() != "user":
            text.append(f" ({agent_role})", style=style['role_color'])
        
        # Add turn number for context
        if turn_number and turn_number > 0:
            text.append(f" #{turn_number}", style="dim")
        
        # Add message type indicator
        type_indicators = {
            "agent_request": "📤",
            "agent_response": "💬", 
            "orchestrator_action": "⚡",
            "workflow_start": "🚀",
            "workflow_end": "🏁"
        }
        if message_type in type_indicators:
            text.append(f" {type_indicators[message_type]}", style="dim")
        
        text.append(": ")
        
        # Add content with word wrapping
        if content:
            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "..."
            text.append(content, style="default")
        else:
            text.append("[dim italic]No content[/dim italic]")
        
        return text
    
    def _create_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append("🎭 ", style="bold")
        header_text.append("Agent ", style="bold blue")
        header_text.append("Conversation Monitor", style="bold")
        
        status_text = Text()
        if self.is_running:
            status_text.append("● LIVE", style="bold green")
        else:
            status_text.append("● CONNECTING", style="bold yellow")
        
        header_table = Table.grid(padding=1)
        header_table.add_column(justify="left")
        header_table.add_column(justify="right")
        header_table.add_row(header_text, status_text)
        
        return Panel(
            header_table,
            box=box.ROUNDED,
            style="blue",
            title="[bold white]Agent Conversations[/bold white]",
            title_align="center"
        )
    
    def _create_message_panel(self) -> Panel:
        """Create the main messages panel."""
        if not self.messages:
            empty_text = Text()
            empty_text.append("🔍 ", style="dim")
            empty_text.append("Waiting for agent conversations...", style="dim italic")
            empty_text.append("\n\n💡 Start an agent workflow to see messages here!", style="dim")
            return Panel(
                Align.center(empty_text),
                box=box.ROUNDED,
                title="[dim]Messages[/dim]",
                height=20
            )
        
        # Show last 15 messages to fit in terminal
        recent_messages = self.messages[-15:]
        
        message_text = Text()
        for i, message in enumerate(recent_messages):
            if i > 0:
                message_text.append("\n")
            message_text.append(self._format_message(message))
        
        return Panel(
            message_text,
            box=box.ROUNDED,
            title=f"[bold]Messages ({len(self.messages)} total)[/bold]",
            padding=(1, 2),
            height=25
        )
    
    def _create_stats_panel(self) -> Panel:
        """Create the statistics panel."""
        if not self.messages:
            return Panel(
                Text("No messages yet", style="dim"),
                title="[dim]Statistics[/dim]",
                box=box.ROUNDED
            )
        
        # Calculate statistics
        agent_counts = {}
        workflow_counts = {}
        message_type_counts = {}
        
        for message in self.messages:
            agent_name = message.get("agent_name", "Unknown")
            workflow_id = message.get("workflow_id", "Unknown")
            message_type = message.get("message_type", "Unknown")
            
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
            workflow_counts[workflow_id] = workflow_counts.get(workflow_id, 0) + 1
            message_type_counts[message_type] = message_type_counts.get(message_type, 0) + 1
        
        stats_table = Table.grid(padding=1)
        stats_table.add_column(justify="left", style="bold")
        stats_table.add_column(justify="right", style="cyan")
        
        stats_table.add_row("Total Messages:", str(len(self.messages)))
        stats_table.add_row("Active Workflows:", str(len(workflow_counts)))
        stats_table.add_row("Active Agents:", str(len(agent_counts)))
        
        # Top agents
        top_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for agent, count in top_agents:
            emoji = self._get_agent_style(agent)["emoji"]
            stats_table.add_row(f"{emoji} {agent}:", str(count))
        
        return Panel(
            stats_table,
            title="[bold]Statistics[/bold]",
            box=box.ROUNDED
        )
    
    def _create_layout(self) -> Layout:
        """Create the main layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(self._create_header(), size=5, name="header"),
            Layout(name="main"),
            Layout(self._create_stats_panel(), size=10, name="stats")
        )
        
        layout["main"].update(self._create_message_panel())
        
        return layout
    
    async def _test_connection(self) -> bool:
        """Test connection to the ConversationCollector API."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _load_initial_messages(self):
        """Load initial messages from the API."""
        try:
            response = requests.get(f"{self.api_url}/conversations/latest?limit=50", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.messages = data.get("messages", [])
                # Reverse to show oldest first
                self.messages.reverse()
        except Exception as e:
            self.console.print(f"[red]Error loading initial messages: {e}[/red]")
    
    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            if data.get("type") == "new_message":
                new_message = data.get("message")
                if new_message:
                    self.messages.append(new_message)
                    # Keep only last 100 messages in memory
                    if len(self.messages) > 100:
                        self.messages = self.messages[-100:]
            elif data.get("type") == "initial_messages":
                initial_messages = data.get("messages", [])
                self.messages = initial_messages[-50:]  # Keep last 50
                self.messages.reverse()  # Show oldest first
        except Exception as e:
            self.console.print(f"[red]Error processing WebSocket message: {e}[/red]")
    
    async def _websocket_listener(self):
        """Listen for WebSocket messages."""
        websocket_url = f"{self.ws_url}/conversations/live"
        
        while self.is_running:
            try:
                async with websockets.connect(websocket_url) as websocket:
                    self.console.print("[dim]Connected to live feed[/dim]")
                    async for message in websocket:
                        if not self.is_running:
                            break
                        await self._handle_websocket_message(message)
            except Exception as e:
                if self.is_running:
                    self.console.print(f"[red]WebSocket connection error: {e}[/red]")
                    self.console.print("[dim]Retrying in 5 seconds...[/dim]")
                    await asyncio.sleep(5)
    
    async def run(self):
        """Run the console client."""
        self.console.clear()
        self.console.print("[bold blue]Starting Conversation Monitor...[/bold blue]")
        
        # Test connection
        self.console.print("Testing connection to ConversationCollector...")
        if not await self._test_connection():
            self.console.print("[red]❌ Cannot connect to ConversationCollector API[/red]")
            self.console.print(f"[dim]Make sure the service is running at {self.api_url}[/dim]")
            return
        
        self.console.print("[green]✅ Connected to ConversationCollector[/green]")
        
        # Load initial messages
        self.console.print("Loading conversation history...")
        await self._load_initial_messages()
        
        self.is_running = True
        
        # Start WebSocket listener
        websocket_task = asyncio.create_task(self._websocket_listener())
        
        # Main display loop
        with Live(self._create_layout(), refresh_per_second=2, screen=True) as live:
            try:
                while self.is_running:
                    live.update(self._create_layout())
                    await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                self.is_running = False
        
        # Cleanup
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            pass


@click.command()
@click.option(
    "--api-url", 
    default="http://localhost:8005", 
    help="ConversationCollector API URL"
)
@click.option(
    "--ws-url", 
    default="ws://localhost:8005", 
    help="ConversationCollector WebSocket URL"
)
def main(api_url: str, ws_url: str):
    """
    ConversationCollector Console Client
    
    A beautiful terminal interface for monitoring real-time agent conversations.
    """
    try:
        client = ConversationConsole(api_url, ws_url)
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()