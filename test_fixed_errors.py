#!/usr/bin/env python3
"""
Test Fixed Auto-Error Resolution System
This tests the improved error capture and SQL execution
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_fixed_error_system():
    """Test the fixed auto-error resolution system"""
    
    print("🧪 TESTING FIXED AUTO-ERROR RESOLUTION SYSTEM")
    print("=" * 60)
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Initial error count: {len(assistant.recent_errors)}")
    
    # Test 1: SQL query that should fail (TABLE NOT FOUND)
    print("\n🧪 TEST 1: Table Not Found Error")
    print("-" * 40)
    
    test_sql = "SELECT * FROM non_existent_table_test123"
    print(f"Testing SQL: {test_sql}")
    
    try:
        response = await assistant.chat(test_sql, db_name="mysql")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Exception (expected): {e}")
    
    print(f"📊 Error count after test 1: {len(assistant.recent_errors)}")
    
    # Test 2: SQL syntax error
    print("\n🧪 TEST 2: SQL Syntax Error")
    print("-" * 40)
    
    test_sql2 = "SELECT * FROM WHERE ORDER BY INVALID"
    print(f"Testing SQL: {test_sql2}")
    
    try:
        response = await assistant.chat(test_sql2, db_name="mysql")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Exception (expected): {e}")
    
    print(f"📊 Error count after test 2: {len(assistant.recent_errors)}")
    
    # Test 3: Column not found error
    print("\n🧪 TEST 3: Column Not Found Error")
    print("-" * 40)
    
    test_sql3 = "SELECT non_existent_column FROM users"
    print(f"Testing SQL: {test_sql3}")
    
    try:
        response = await assistant.chat(test_sql3, db_name="mysql")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Exception (expected): {e}")
    
    print(f"📊 Error count after test 3: {len(assistant.recent_errors)}")
    
    # Test 4: Valid SQL (should succeed)
    print("\n🧪 TEST 4: Valid SQL Query")
    print("-" * 40)
    
    test_sql4 = "SELECT 1 as test_column"
    print(f"Testing SQL: {test_sql4}")
    
    try:
        response = await assistant.chat(test_sql4, db_name="mysql")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Unexpected exception: {e}")
    
    print(f"📊 Final error count: {len(assistant.recent_errors)}")
    
    # Display captured errors
    if assistant.recent_errors:
        print("\n🎯 CAPTURED ERRORS:")
        print("-" * 40)
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"{i}. {error.error_type} (Code: {error.error_code})")
            print(f"   Message: {error.message[:100]}...")
            print(f"   Query: {error.query[:50]}...")
            print()
    
    print("\n" + "=" * 60)
    if assistant.recent_errors:
        print(f"🎉 SUCCESS! {len(assistant.recent_errors)} errors captured!")
        print("🌐 Now check your web interface at http://localhost:8506")
        print("   Recent Errors should show:", len(assistant.recent_errors))
    else:
        print("❌ No errors captured - system may need further debugging")

if __name__ == "__main__":
    asyncio.run(test_fixed_error_system()) 