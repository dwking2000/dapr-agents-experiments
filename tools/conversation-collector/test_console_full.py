#!/usr/bin/env python3
"""
Test script to show full agent conversations with content
"""

import requests
from datetime import datetime

def show_agent_conversations():
    """Show actual agent conversations with full content."""
    
    print('🎭 Agent Conversations')
    print('=' * 60)
    
    try:
        # Get more messages to find ones with actual content
        response = requests.get('http://localhost:8005/conversations?limit=50', timeout=10)
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            
            # Filter for messages with actual content (not just "Agent message")
            content_messages = [
                msg for msg in messages 
                if msg.get('content', '') != 'Agent message' and len(msg.get('content', '')) > 20
            ]
            
            print(f'📊 Total messages: {data.get("total_count", 0)}')
            print(f'🎯 Messages with content: {len(content_messages)}')
            print()
            
            # Show the best examples
            for msg in content_messages[:8]:
                agent = msg.get('agent_name', 'Unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                turn = msg.get('turn_number', 0)
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%H:%M:%S')
                except:
                    formatted_time = '??:??:??'
                
                # Dynamic agent emoji assignment
                orchestrator_emojis = {
                    'RandomOrchestrator': '🎲',
                    'RoundRobinOrchestrator': '🔄',
                    'LLMOrchestrator': '🧠'
                }
                emoji = orchestrator_emojis.get(agent, '🤖')
                
                # Limit content length for readability
                if len(content) > 200:
                    content = content[:200] + '...'
                
                turn_text = f' #{turn}' if turn > 0 else ''
                print(f'[{formatted_time}] {emoji} {agent}{turn_text}:')
                print(f'  "{content}"')
                print()
            
            print('🎭 This is what the console client will show in real-time!')
            
        else:
            print('❌ Failed to get conversations')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    show_agent_conversations()