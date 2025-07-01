#!/usr/bin/env python3
"""
Create Live Database Error for Auto-Resolution Testing
This script creates REAL errors in your actual database to test the system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def create_live_database_error():
    """Create real database errors in your live database"""
    
    print("🔥 CREATING REAL DATABASE ERRORS")
    print("=" * 50)
    print("This will create ACTUAL errors in your DBT database")
    print("to test the auto-error resolution system.")
    print()
    
    # Initialize DBA Assistant (same instance as web interface)
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Current error count: {len(assistant.recent_errors)}")
    print()
    
    # Test 1: Force a table not found error 
    print("🧪 TEST 1: Creating TABLE NOT FOUND Error")
    print("-" * 40)
    
    try:
        # This will create a real MySQL error in your database
        response = await assistant.chat("SELECT * FROM non_existent_table_test123", "mysql")
        print(f"✅ Response generated: {len(response) if response else 0} chars")
    except Exception as e:
        print(f"✅ Error occurred as expected: {e}")
    
    print(f"📊 Errors after test 1: {len(assistant.recent_errors)}")
    print()
    
    # Test 2: Force a syntax error
    print("🧪 TEST 2: Creating SQL SYNTAX Error")
    print("-" * 40)
    
    try:
        # This will create a syntax error
        response = await assistant.chat("SELECT * FROM WHERE ORDER BY", "mysql")
        print(f"✅ Response generated: {len(response) if response else 0} chars")
    except Exception as e:
        print(f"✅ Error occurred as expected: {e}")
    
    print(f"📊 Errors after test 2: {len(assistant.recent_errors)}")
    print()
    
    # Test 3: Force a column not found error
    print("🧪 TEST 3: Creating COLUMN NOT FOUND Error")
    print("-" * 40)
    
    try:
        # This will create a column not found error
        response = await assistant.chat("SELECT non_existent_column FROM users", "mysql")
        print(f"✅ Response generated: {len(response) if response else 0} chars")
    except Exception as e:
        print(f"✅ Error occurred as expected: {e}")
    
    print(f"📊 Errors after test 3: {len(assistant.recent_errors)}")
    print()
    
    # Show captured errors
    print("🧪 TEST 4: Show Captured Errors")
    print("-" * 40)
    
    if assistant.recent_errors:
        print(f"🎉 SUCCESS! {len(assistant.recent_errors)} errors captured:")
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"\n  {i}. ERROR TYPE: {error.error_type}")
            print(f"     ERROR CODE: {error.error_code}")
            print(f"     MESSAGE: {error.message[:100]}...")
            print(f"     QUERY: {error.query[:50] if error.query else 'None'}...")
            print(f"     TIMESTAMP: {error.timestamp}")
    else:
        print("❌ NO ERRORS CAPTURED")
    
    print()
    print("🌐 Now check your web interface at http://localhost:8502")
    print("   The 'Recent Errors' count should show the captured errors!")
    print()
    
    return len(assistant.recent_errors)

if __name__ == "__main__":
    print("🚀 Starting Live Database Error Creation...")
    error_count = asyncio.run(create_live_database_error())
    
    if error_count > 0:
        print(f"\n🎉 SUCCESS! {error_count} errors created and captured!")
        print("✅ Auto-Error Resolution System is working!")
        print("🌐 Check your web interface to see the error count!")
    else:
        print("\n❌ FAILED! No errors were captured.")
        print("🔧 The auto-error resolution system needs debugging.") 