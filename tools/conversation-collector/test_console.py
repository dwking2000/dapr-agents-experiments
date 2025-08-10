#!/usr/bin/env python3
"""
Test script for ConversationCollector Console Client
"""

import requests
import json
from datetime import datetime

def test_conversation_collector():
    """Test the ConversationCollector API and preview console output."""
    
    print('🔍 Testing ConversationCollector API...')
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8005/health', timeout=5)
        if response.status_code == 200:
            print('✅ API connection successful!')
            
            # Test conversations endpoint
            response = requests.get('http://localhost:8005/conversations/latest?limit=5', timeout=5)
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                total = data.get('total_count', 0)
                print(f'✅ Found {len(messages)} recent messages (total: {total})')
                print()
                print('📝 Recent agent conversations:')
                print('=' * 60)
                
                # Show sample messages with beautiful formatting
                for msg in messages[:5]:
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
                    
                    # Truncate long content for preview
                    if len(content) > 100:
                        content = content[:100] + '...'
                    
                    turn_text = f' #{turn}' if turn > 0 else ''
                    print(f'[{formatted_time}] {emoji} {agent}{turn_text}:')
                    print(f'  {content}')
                    print()
                
                print('🎭 Console client is ready to display these conversations live!')
                print('📱 Run: cd tools/conversation-collector/clients/console && uv run python app.py')
                
            else:
                print('❌ Failed to get conversations')
        else:
            print('❌ API connection failed')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        print('💡 Make sure ConversationCollector service is running!')

if __name__ == '__main__':
    test_conversation_collector()