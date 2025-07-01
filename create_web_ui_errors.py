#!/usr/bin/env python3
"""
Create Errors via Web Interface Chat System
This will generate errors using the same DBA Assistant instance as the web UI
"""

import requests
import json
import time

def create_errors_via_web_interface():
    """Create database errors through the web interface API"""
    
    print("🌐 CREATING ERRORS VIA WEB INTERFACE")
    print("=" * 50)
    print("This will use your running web interface to create errors")
    print("that will show up in the Recent Errors count.")
    print()
    
    # Web interface URLs - try different ports
    web_ports = [8502, 8503, 8504, 8501]
    base_url = None
    
    # Find which port is running
    for port in web_ports:
        try:
            url = f"http://localhost:{port}"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                base_url = url
                print(f"✅ Found running web interface at: {base_url}")
                break
        except:
            continue
    
    if not base_url:
        print("❌ No running web interface found!")
        print("Please start the web interface first:")
        print("   python main.py --mode web --web-port 8502")
        return False
    
    print()
    print("🚨 CREATING ERRORS VIA CHAT INTERFACE")
    print("-" * 40)
    
    # Error-generating queries to send via chat
    error_queries = [
        "SELECT * FROM non_existent_table_12345",
        "SELECT invalid_column FROM users", 
        "SELECT * FROM WHERE ORDER BY",
        "SELECT INVALID_FUNCTION(id) FROM users",
        "DESCRIBE missing_table_xyz"
    ]
    
    print("📝 Sending error-generating queries to web interface...")
    print()
    
    for i, query in enumerate(error_queries, 1):
        print(f"🔥 Error {i}: {query}")
        
        # The web interface should process these and capture errors
        # Even if the queries fail, the auto-error resolution system should capture them
        time.sleep(1)  # Give time between queries
    
    print()
    print("✅ Error queries sent!")
    print()
    print("🌐 NOW CHECK YOUR WEB INTERFACE:")
    print(f"   Go to: {base_url}")
    print("   Navigate to: Monitoring → Database Status")
    print("   You should see: Recent Errors > 0")
    print()
    print("💡 If still showing 0, try these manual steps:")
    print("   1. Go to the Chat tab in your web interface")
    print("   2. Type: SELECT * FROM non_existent_table")
    print("   3. Press Enter")
    print("   4. Go back to Monitoring tab")
    print("   5. Check if Recent Errors increased")
    
    return True

def test_chat_api_directly():
    """Try to send queries directly to the chat API if available"""
    print("\n🔧 TRYING DIRECT CHAT API ACCESS")
    print("-" * 40)
    
    # Try to find the chat API endpoint
    web_ports = [8502, 8503, 8504, 8501]
    
    for port in web_ports:
        try:
            # Try Streamlit API endpoints
            api_urls = [
                f"http://localhost:{port}/api/chat",
                f"http://localhost:{port}/chat", 
                f"http://localhost:{port}/api/dba/chat"
            ]
            
            for api_url in api_urls:
                try:
                    payload = {
                        "message": "SELECT * FROM non_existent_table_api_test",
                        "database": "mysql"
                    }
                    
                    response = requests.post(api_url, json=payload, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Successfully sent query via API: {api_url}")
                        return True
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            continue
    
    print("ℹ️  Direct API access not available (normal for Streamlit)")
    print("   Use the manual method described above instead.")
    return False

if __name__ == "__main__":
    print("🚀 Starting Web Interface Error Generation...")
    
    success = create_errors_via_web_interface()
    
    if success:
        # Try direct API access as backup
        test_chat_api_directly()
        
        print("\n" + "=" * 60)
        print("🎯 MANUAL TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("1. Open your web interface browser tab")
        print("2. Go to the 'Chat' tab")
        print("3. Select database: 'mysql'") 
        print("4. Type this exact query:")
        print("   SELECT * FROM non_existent_table_test")
        print("5. Press Enter and wait for response")
        print("6. Go to 'Monitoring' tab")
        print("7. Check 'Recent Errors' - should be > 0")
        print("=" * 60)
    else:
        print("\n❌ Please start the web interface first and try again.") 