#!/usr/bin/env python3
"""
Simple launcher for the Agent Conversation Monitor Web Client
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import sys
from pathlib import Path

def start_server(port=8080, directory=None):
    """Start HTTP server for the web client."""
    if directory is None:
        directory = Path(__file__).parent
    
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
        
        def end_headers(self):
            # Add CORS headers for local development
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Starting Agent Conversation Monitor Web Client...")
            print(f"📍 Server: http://localhost:{port}")
            print(f"📁 Directory: {directory}")
            print("🔗 Opening browser...")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(f"http://localhost:{port}")
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            print("\n✅ Web client is running!")
            print("💡 Make sure ConversationCollector service is running on port 8005")
            print("⏹️  Press Ctrl+C to stop the server")
            print("-" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down web server...")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python start.py --port {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the Agent Conversation Monitor Web Client")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")
    
    args = parser.parse_args()
    start_server(args.port)