#!/usr/bin/env python3
"""
Test External Error Detection from MySQL Workbench, phpMyAdmin, etc.
This script demonstrates how DBA-GPT can capture and auto-resolve errors
from external MySQL clients.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.monitoring.mysql_log_monitor import MySQLLogMonitor
from core.config import Config

async def test_external_error_detection():
    """Test external MySQL error detection and auto-resolution"""
    
    print("🚀 DBA-GPT External Error Detection Test")
    print("=" * 60)
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print("✅ DBA Assistant initialized")
    
    # Initialize MySQL Log Monitor
    monitor = MySQLLogMonitor(error_callback=assistant.handle_auto_error_resolution)
    
    print("✅ MySQL Log Monitor initialized")
    print(f"📂 Monitoring {len(monitor.log_paths)} MySQL log files")
    
    for path in monitor.log_paths:
        print(f"   - {path}")
    
    if not monitor.log_paths:
        print("\n❌ No MySQL log files found!")
        print("\n🔧 To enable external error detection:")
        print("1. Enable MySQL logging:")
        print("   SET GLOBAL general_log = 'ON';")
        print("   SET GLOBAL log_error = 'ON';")
        print("\n2. Restart this script")
        print("\n3. Run SQL errors in MySQL Workbench/phpMyAdmin")
        print("   Example: SELECT * FROM non_existent_table;")
        return
    
    print("\n🎯 READY FOR EXTERNAL ERROR DETECTION!")
    print("=" * 60)
    print("\n📋 Test Instructions:")
    print("1. Open MySQL Workbench, phpMyAdmin, or MySQL command line")
    print("2. Connect to your MySQL database")
    print("3. Run these test queries to trigger errors:")
    print("\n   📝 Test Queries:")
    print("   • SELECT * FROM non_existent_table;")
    print("   • SELECT invalid_column FROM users;")
    print("   • SELECT * FROM WHERE ORDER BY;")
    print("   • INSERT INTO users VALUES ('test');")
    
    print("\n🤖 DBA-GPT will automatically detect and resolve these errors!")
    print("📊 Watch this console for auto-resolution responses...")
    print("\n⏹️  Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    try:
        # Start monitoring (this will run indefinitely)
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
    
    print("\n✅ External error detection test completed")

def print_mysql_log_setup_help():
    """Print help for setting up MySQL logging"""
    print("\n🔧 MySQL Logging Setup Help")
    print("=" * 40)
    print("\n1. Connect to MySQL as admin user:")
    print("   mysql -u root -p")
    print("\n2. Enable logging:")
    print("   SET GLOBAL general_log = 'ON';")
    print("   SET GLOBAL log_error = 'ON';")
    print("   SET GLOBAL general_log_file = '/path/to/mysql/general.log';")
    print("\n3. Check logging status:")
    print("   SHOW VARIABLES LIKE 'general_log';")
    print("   SHOW VARIABLES LIKE 'log_error';")
    print("\n4. Common log file locations:")
    print("   Windows: C:/ProgramData/MySQL/MySQL Server 8.0/Data/")
    print("   Linux:   /var/log/mysql/")
    print("   XAMPP:   C:/xampp/mysql/data/")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test DBA-GPT External Error Detection")
    parser.add_argument("--setup-help", action="store_true", 
                       help="Show MySQL logging setup instructions")
    
    args = parser.parse_args()
    
    if args.setup_help:
        print_mysql_log_setup_help()
    else:
        try:
            asyncio.run(test_external_error_detection())
        except KeyboardInterrupt:
            print("\n👋 Test stopped by user")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print_mysql_log_setup_help() 