#!/usr/bin/env python3
"""
Force Real Database Errors - Direct SQL Execution
This script directly executes SQL queries to generate real database errors
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def force_real_database_errors():
    """Force real database errors by direct SQL execution"""
    
    print("💥 FORCING REAL DATABASE ERRORS")
    print("=" * 50)
    print("This will execute BAD SQL queries directly in your database")
    print("to generate REAL errors for the auto-resolution system.")
    print()
    
    # Initialize DBA Assistant and get database connection
    config = Config()
    assistant = DBAAssistant(config)
    
    # Get database configuration
    db_config = config.databases.get("mysql")
    if not db_config:
        print("❌ No MySQL database configuration found!")
        return 0
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Initial error count: {len(assistant.recent_errors)}")
    print(f"🔗 Database: {db_config.database} on {db_config.host}:{db_config.port}")
    print()
    
    error_count = 0
    
    # ERROR 1: Table Not Found
    print("💥 ERROR 1: Creating TABLE NOT FOUND Error")
    print("-" * 40)
    
    try:
        connection = await assistant.db_connector.get_connection(db_config)
        # This WILL cause a table not found error
        await connection.execute_query("SELECT * FROM non_existent_table_xyz123")
    except Exception as e:
        print(f"✅ Database error caught: {type(e).__name__}: {e}")
        error_count += 1
    
    print(f"📊 Errors captured: {len(assistant.recent_errors)}")
    print()
    
    # ERROR 2: SQL Syntax Error  
    print("💥 ERROR 2: Creating SQL SYNTAX Error")
    print("-" * 40)
    
    try:
        connection = await assistant.db_connector.get_connection(db_config)
        # This WILL cause a syntax error
        await connection.execute_query("SELECT * FROM WHERE ORDER BY INVALID")
    except Exception as e:
        print(f"✅ Database error caught: {type(e).__name__}: {e}")
        error_count += 1
    
    print(f"📊 Errors captured: {len(assistant.recent_errors)}")
    print()
    
    # ERROR 3: Column Not Found
    print("💥 ERROR 3: Creating COLUMN NOT FOUND Error")
    print("-" * 40)
    
    try:
        connection = await assistant.db_connector.get_connection(db_config)
        # This WILL cause a column not found error
        await connection.execute_query("SELECT non_existent_column_xyz FROM users")
    except Exception as e:
        print(f"✅ Database error caught: {type(e).__name__}: {e}")
        error_count += 1
    
    print(f"📊 Errors captured: {len(assistant.recent_errors)}")
    print()
    
    # ERROR 4: Invalid Function
    print("💥 ERROR 4: Creating INVALID FUNCTION Error")
    print("-" * 40)
    
    try:
        connection = await assistant.db_connector.get_connection(db_config)
        # This WILL cause an invalid function error
        await connection.execute_query("SELECT INVALID_FUNCTION(id) FROM users")
    except Exception as e:
        print(f"✅ Database error caught: {type(e).__name__}: {e}")
        error_count += 1
    
    print(f"📊 Errors captured: {len(assistant.recent_errors)}")
    print()
    
    # Show Results
    print("🎯 FINAL RESULTS")
    print("-" * 40)
    
    if assistant.recent_errors:
        print(f"🎉 SUCCESS! {len(assistant.recent_errors)} errors captured:")
        print()
        
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"  {i}. 🚨 {error.error_type}")
            print(f"     📋 Code: {error.error_code}")
            print(f"     💬 Message: {error.message[:80]}...")
            print(f"     📝 Query: {error.query[:50] if error.query else 'None'}...")
            print(f"     🕒 Time: {error.timestamp.strftime('%H:%M:%S')}")
            print()
            
        print("🌐 NOW CHECK YOUR WEB INTERFACE!")
        print(f"   http://localhost:8502 should show 'Recent Errors: {len(assistant.recent_errors)}'")
        print()
        
    else:
        print("❌ NO ERRORS CAPTURED - System not working correctly")
    
    return len(assistant.recent_errors)

async def test_web_interface_connection():
    """Test if the web interface shares the same error storage"""
    print("\n🔗 TESTING WEB INTERFACE CONNECTION")
    print("-" * 40)
    
    # Try using the same assistant instance pattern as web interface
    config = Config()
    assistant = DBAAssistant(config)
    
    # Force an error through the pattern we know works
    try:
        db_config = config.databases.get("mysql")
        connection = await assistant.db_connector.get_connection(db_config)
        await connection.execute_query("SELECT * FROM definitely_missing_table_test")
    except Exception as e:
        print(f"✅ Test error created: {e}")
    
    print(f"📊 Test assistant error count: {len(assistant.recent_errors)}")
    
    return assistant

if __name__ == "__main__":
    print("🚀 Starting Direct Database Error Generation...")
    
    try:
        error_count = asyncio.run(force_real_database_errors())
        
        print("\n" + "=" * 60)
        if error_count > 0:
            print(f"🎉 SUCCESS! {error_count} REAL database errors created!")
            print("✅ Auto-Error Resolution System is capturing errors!")
            print("🌐 Check your web interface to see the error count!")
        else:
            print("❌ FAILED! No errors were captured.")
            print("🔧 The auto-error resolution system needs debugging.")
            
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Script error: {e}")
        import traceback
        traceback.print_exc() 