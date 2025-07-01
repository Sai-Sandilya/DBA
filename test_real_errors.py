#!/usr/bin/env python3
"""
Test Real Database Errors for Auto-Error Resolution
This script creates actual database errors to test the auto-resolution system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_real_database_errors():
    """Test auto-error resolution with real database errors"""
    
    print("🚀 REAL DATABASE ERROR TESTING")
    print("=" * 50)
    print("This will create REAL errors in your database to test auto-resolution")
    print()
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Initial error count: {len(assistant.recent_errors)}")
    print()
    
    # Test 1: Pattern matching with debugging
    print("🧪 TEST 1: Pattern Matching with Debug Logs")
    print("-" * 40)
    
    test_message = "how to fix entity not found ?"
    print(f"📝 Testing message: '{test_message}'")
    response = await assistant.chat(test_message, "mysql")
    print(f"✅ Response length: {len(response) if response else 0} characters")
    print(f"📊 Errors captured: {len(assistant.recent_errors)}")
    print()
    
    # Test 2: Create actual SQL syntax error
    print("🧪 TEST 2: Real SQL Syntax Error")
    print("-" * 40)
    
    try:
        db_config = config.databases.get("mysql")
        if db_config:
            connection = await assistant.db_connector.get_connection(db_config)
            # This will cause a syntax error
            await connection.execute_query("SELECT * FROM WHERE;")  # Invalid SQL
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}: {e}")
    
    print(f"📊 Errors after syntax error: {len(assistant.recent_errors)}")
    print()
    
    # Test 3: Create table not found error
    print("🧪 TEST 3: Real Table Not Found Error")
    print("-" * 40)
    
    try:
        if db_config:
            connection = await assistant.db_connector.get_connection(db_config)
            # This will cause table not found error
            await connection.execute_query("SELECT * FROM non_existent_table_xyz123;")
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}: {e}")
    
    print(f"📊 Errors after table not found: {len(assistant.recent_errors)}")
    print()
    
    # Test 4: Check if errors were processed
    print("🧪 TEST 4: Auto-Resolution Results")
    print("-" * 40)
        
    if assistant.recent_errors:
        print(f"🎉 SUCCESS! Captured {len(assistant.recent_errors)} errors:")
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"  {i}. Type: {error.error_type}")
            print(f"     Code: {error.error_code}")
            print(f"     Message: {error.message[:100]}...")
            print()
    else:
        print("❌ NO ERRORS CAPTURED - System not working")
    
    # Test 5: Test pattern matching with captured errors
    print("🧪 TEST 5: Pattern Matching After Errors")
    print("-" * 40)
    
    response2 = await assistant.chat("fix entity not found error", "mysql")
    print(f"✅ Response 2 length: {len(response2) if response2 else 0} characters")
    print(f"📊 Final error count: {len(assistant.recent_errors)}")
    
    return len(assistant.recent_errors) > 0

if __name__ == "__main__":
    success = asyncio.run(test_real_database_errors())
    if success:
        print("\n🎉 AUTO-ERROR RESOLUTION SYSTEM IS WORKING!")
    else:
        print("\n❌ AUTO-ERROR RESOLUTION SYSTEM NEEDS FIXING") 