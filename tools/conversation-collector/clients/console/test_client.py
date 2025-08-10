#!/usr/bin/env python3
"""
Test the console client functionality
"""

import asyncio
from app import ConversationConsole

async def test_console_client():
    """Test the console client basic functionality."""
    print("🧪 Testing Agent Conversation Console Client...")
    
    try:
        # Create client instance
        client = ConversationConsole()
        
        # Test API connection
        print("Testing API connection...")
        connected = await client._test_connection()
        if connected:
            print("✅ API connection successful!")
        else:
            print("❌ API connection failed!")
            return
        
        # Test loading messages
        print("Loading initial messages...")
        await client._load_initial_messages()
        print(f"✅ Loaded {len(client.messages)} messages")
        
        # Show a preview of how messages would be displayed
        if client.messages:
            print("\n📝 Console display preview:")
            print("-" * 60)
            for i, message in enumerate(client.messages[-3:]):  # Show last 3
                formatted_msg = client._format_message(message)
                print(formatted_msg.plain)  # Use .plain to get text without Rich formatting
            
            print("-" * 60)
            print("🎭 Console client is working! Run 'uv run python app.py' for full interface")
        else:
            print("⚠️  No messages found - start a workflow to see conversations")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_console_client())