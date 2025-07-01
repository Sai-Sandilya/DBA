#!/usr/bin/env python3
"""
Test Error Counter in Web UI
This script generates database errors and verifies they show up in the web interface
"""

import asyncio
import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.database.connector import DatabaseError
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_web_ui_errors():
    """Test that errors show up in the web UI"""
    
    print("🧪 TESTING ERROR COUNTER IN WEB UI")
    print("=" * 50)
    print("This will generate errors that should show up in the web interface")
    print()
    
    # Initialize DBA Assistant (same as web interface)
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Initial error count: {len(assistant.recent_errors)}")
    print()
    
    # Test SQL queries that will generate errors
    test_queries = [
        "SELECT * FROM non_existent_table_ui_test",
        "SELECT invalid_column FROM users",
        "SELECT * FROM WHERE invalid syntax",
        "INSERT INTO non_existent_table VALUES (1, 'test')"
    ]
    
    print("🔥 Generating database errors...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query[:50]}... ---")
        
        try:
            # Execute the query through the chat system (like web interface does)
            response = await assistant.chat(query, "mysql")
            print(f"Response: {response[:100]}...")
            
        except Exception as e:
            print(f"Error (expected): {e}")
        
        print(f"Current error count: {len(assistant.recent_errors)}")
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n📈 FINAL RESULTS:")
    print(f"✅ Total errors generated: {len(assistant.recent_errors)}")
    print(f"✅ Error details:")
    
    for i, error in enumerate(assistant.recent_errors, 1):
        print(f"  {i}. {error.error_type} - {error.message[:60]}...")
    
    print(f"\n🌐 WEB INTERFACE CHECK:")
    print(f"Now go to your web interface monitoring tab and verify:")
    print(f"- Recent Errors count shows: {len(assistant.recent_errors)}")
    print(f"- Error details are displayed in the interface")
    
    # Create a shared error file for web interface to read
    error_data = {
        "timestamp": time.time(),
        "error_count": len(assistant.recent_errors),
        "errors": [
            {
                "type": error.error_type,
                "code": error.error_code,
                "message": error.message,
                "timestamp": error.timestamp.isoformat() if error.timestamp else None
            } for error in assistant.recent_errors
        ]
    }
    
    with open("recent_errors.json", "w") as f:
        json.dump(error_data, f, indent=2)
    
    print(f"📁 Error data saved to: recent_errors.json")
    
    return len(assistant.recent_errors)

if __name__ == "__main__":
    error_count = asyncio.run(test_web_ui_errors())
    print(f"\n🎯 TEST COMPLETED: {error_count} errors generated") 