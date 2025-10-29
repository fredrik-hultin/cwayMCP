#!/usr/bin/env python3
"""
Simple WebSocket client to test dashboard logging.
Connects to the dashboard WebSocket and prints all messages received.
"""

import asyncio
import socketio
import sys

async def test_dashboard_connection():
    """Connect to dashboard WebSocket and print messages."""
    sio = socketio.AsyncClient()
    
    @sio.on('log_message')
    async def on_log_message(data):
        """Handle incoming log messages."""
        print(f"📨 LOG RECEIVED: {data}")
    
    @sio.on('connect')
    async def on_connect():
        print("✅ Connected to dashboard WebSocket at http://localhost:8080")
        print("🎧 Listening for log messages... (Press Ctrl+C to stop)")
    
    @sio.on('disconnect')
    async def on_disconnect():
        print("❌ Disconnected from dashboard")
    
    try:
        await sio.connect('http://localhost:8080')
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    print("🧪 WebSocket Dashboard Test Client")
    print("=" * 50)
    asyncio.run(test_dashboard_connection())
