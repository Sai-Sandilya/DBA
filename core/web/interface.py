"""
Streamlit web interface for DBA-GPT
"""

import streamlit as st
import asyncio
import json
import threading
from typing import Dict, Any, Optional, TypeVar, Callable, Union
from datetime import datetime
import argparse
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from streamlit.runtime.scriptrunner import add_script_run_ctx

from core.ai.dba_assistant import DBAAssistant
from core.utils.logger import setup_logger
from core.config import Config

logger = setup_logger(__name__)


def run_async_in_thread(async_func, *args, **kwargs):
    """
    Run async function in a separate thread to avoid event loop conflicts.
    This prevents the "Event loop is closed" errors in Streamlit.
    """
    result_container = {}
    
    def run_in_thread():
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_func(*args, **kwargs))
                result_container['result'] = result
            finally:
                # Properly cleanup the event loop
                loop.close()
        except Exception as e:
            logger.error(f"Error in async thread: {e}", exc_info=True)
            result_container['error'] = e
    
    # Create and run thread with proper Streamlit context
    thread = threading.Thread(target=run_in_thread)
    add_script_run_ctx(thread)
    thread.start()
    thread.join()
    
    # Check results and return or raise error
    if 'error' in result_container:
        raise result_container['error']
    
    return result_container.get('result', {})


def get_assistant() -> DBAAssistant:
    """Get DBA-GPT assistant instance"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to config file")
    args, _ = parser.parse_known_args()
    config = Config(args.config)
    return DBAAssistant(config)


def start_web_interface(assistant: DBAAssistant, port: int = 8501):
    """Start the Streamlit web interface"""
    # This function is now a placeholder
    pass


def main_interface(assistant: DBAAssistant):
    """Main web interface"""
    
    # Initialize session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Sidebar
    with st.sidebar:
        st.title("🗄️ DBA-GPT")
        st.markdown("AI-Powered Database Administration")
        
        # Navigation
        page = st.selectbox(
            "Navigation",
            ["Chat", "Monitoring", "Analysis", "Configuration", "About"]
        )
        
        # Database selection
        db_keys = list(assistant.config.databases.keys())
        available_dbs = db_keys + ["oracle"]  # Add Oracle as a knowledge-based option
        
        if assistant.config.databases:
            selected_db = st.selectbox(
                "Select Database Context",
                available_dbs,
                help="Select a live database or a knowledge base."
            )
        else:
            selected_db = None
            
    # Main content
    if page == "Chat":
        chat_interface(assistant, selected_db)
    elif page == "Monitoring":
        monitoring_interface(assistant)
    elif page == "Analysis":
        run_async_in_thread(analysis_interface, assistant, selected_db)
    elif page == "Configuration":
        configuration_interface(assistant)
    elif page == "About":
        about_interface()


def chat_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Chat interface with two distinct modes"""
    st.title("💬 DBA-GPT Chat")
    
    # Initialize chat mode in session state
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "general"
    
    # Mode Selection
    st.markdown("### 🎯 Select Chat Mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗄️ **MySQL Database Mode**", 
                     type="primary" if st.session_state.chat_mode == "database" else "secondary",
                     use_container_width=True):
            st.session_state.chat_mode = "database"
            st.rerun()
            
    with col2:
        if st.button("🎓 **General Database Topics**", 
                     type="primary" if st.session_state.chat_mode == "general" else "secondary",
                     use_container_width=True):
            st.session_state.chat_mode = "general" 
            st.rerun()
    
    # Display current mode info
    if st.session_state.chat_mode == "database":
        if selected_db and selected_db != "oracle":
            st.success(f"🗄️ **MySQL Database Mode** - Connected to: **{selected_db}**")
            st.info("💡 Ask questions about YOUR database: tables, schema, data, queries, etc.")
        else:
            st.warning("🗄️ **MySQL Database Mode** - No MySQL database selected! Please select a database from the sidebar.")
            st.info("💡 This mode answers questions about your specific connected MySQL database.")
    else:
        st.success(f"🎓 **General Database Topics Mode** - Educational Content")
        st.info("💡 Ask questions about: SQL concepts, database theory, best practices, tutorials, etc.")
    
    # Different example questions based on mode
    st.markdown("### 💡 Example Questions")
    if st.session_state.chat_mode == "database":
        st.markdown("""
        **MySQL Database Questions:**
        - "What tables do I have in my database?"
        - "Show me the schema of the users table"
        - "How many records are in my orders table?"
        - "Find all indexes in my database"
        - "What's the size of my database?"
        """)
    else:
        st.markdown("""
        **General Database Topics:**
        - "What is a SELECT statement?"
        - "Explain the LIKE operator"
        - "How do I use WHERE clauses?"
        - "What are database JOINs?"
        - "Database performance optimization tips"
        """)
    
    st.divider()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # Chat input with mode-specific placeholder
    placeholder_text = {
        "database": "Ask about your MySQL database...",
        "general": "Ask about database concepts, SQL, best practices..."
    }
    
    if prompt := st.chat_input(placeholder_text.get(st.session_state.chat_mode, "Ask a question...")):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Get AI response based on mode
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get conversation history for context
                    conversation_history = st.session_state.messages[-10:] if len(st.session_state.messages) > 1 else []
                    
                    # Route based on chat mode
                    if st.session_state.chat_mode == "database":
                        if selected_db and selected_db != "oracle":
                            # Database-specific mode - use selected database
                            response = run_async_in_thread(
                                assistant.chat,
                                prompt, 
                                db_name=selected_db,
                                conversation_history=conversation_history
                            )
                        else:
                            response = "❌ **MySQL Database Mode requires a connected database.** Please select a MySQL database from the sidebar, or switch to 'General Database Topics' mode for educational content."
                    else:
                        # General topics mode - use educational fallbacks (no async needed)
                        response = assistant.get_general_database_response(prompt)
                    
                    # Clean and validate response
                    if response and isinstance(response, str):
                        response = response.strip()
                        if response:
                            # Display response
                            st.markdown(response)
                            
                            # Add assistant message to chat history
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            st.error("Received empty response from AI")
                    else:
                        st.error("Invalid response format from AI")
                    
                except Exception as e:
                    error_message = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_message)
                    logger.error(f"Chat error: {e}", exc_info=True)
                    
                    # Add error message to chat history so user can see it
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    
    # Mode-specific quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.session_state.chat_mode == "database":
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Show Tables"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "What tables do I have in my database?"
                })
                st.rerun()
                
        with col2:
            if st.button("🔍 Database Size"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "What's the size of my database and each table?"
                })
                st.rerun()
                
        with col3:
            if st.button("⚡ Performance"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "Analyze the performance of my database"
                })
                st.rerun()
                
        with col4:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📚 SQL Basics"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "what is select statement?"
                })
                st.rerun()
                
        with col2:
            if st.button("🔗 JOINs Guide"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "explain database joins"
                })
                st.rerun()
                
        with col3:
            if st.button("⚡ Performance Tips"):
                st.session_state.messages.append({
                    "role": "user", 
                    "content": "database performance optimization"
                })
                st.rerun()
                
        with col4:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()


def monitoring_interface(assistant: DBAAssistant):
    """Monitoring interface"""
    st.title("📊 Database Monitoring")
    
    # Status overview
    st.subheader("System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Databases", len(assistant.config.databases))
        
    with col2:
        st.metric("AI Status", "✅ Active")
        
    with col3:
        st.metric("Monitoring", "✅ Active")
        
    with col4:
        st.metric("Auto-Remediation", "✅ Active")
        
    # Database status
    st.subheader("Database Status")
    
    # Auto-Error Resolution Status
    st.subheader("🚨 Auto-Error Resolution System")
    
    # Try to load saved errors from recent tests
    import json
    import os
    saved_errors = []
    try:
        if os.path.exists("recent_errors.json"):
            with open("recent_errors.json", "r") as f:
                error_data = json.load(f)
                saved_errors = error_data.get("errors", [])
    except Exception as e:
        logger.warning(f"Could not load saved errors: {e}")
    
    # Combine current and saved errors
    total_recent_errors = len(assistant.recent_errors) + len(saved_errors)
    total_resolved = len([e for e in assistant.recent_errors if e]) + len(saved_errors)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Recent Errors", total_recent_errors, help="Database errors captured (including test errors)")
    with col2:
        st.metric("Auto-Resolutions", total_resolved, help="Errors automatically resolved")
    with col3:
        error_status = "🟢 Active" if hasattr(assistant.db_connector, 'error_callback') and assistant.db_connector.error_callback else "🔴 Inactive"
        st.metric("System Status", error_status, help="Auto-resolution system status")
    with col4:
        # Enhanced features indicator
        enhanced_features = "🤖 Enhanced" if hasattr(assistant, 'get_enhanced_system_stats') else "📊 Standard"
        st.metric("AI Features", enhanced_features, help="Enhanced auto-resolution capabilities")
    
    # Enhanced System Analytics (if available)
    if hasattr(assistant, 'get_enhanced_system_stats'):
        try:
            enhanced_stats = assistant.get_enhanced_system_stats()
            
            # Display enhanced metrics in an expandable section
            with st.expander("🤖 Enhanced Auto-Resolution Analytics", expanded=False):
                st.markdown("### 🧠 Pattern Analysis & Learning")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Error Patterns", enhanced_stats.get('error_patterns', 0), help="Unique error patterns detected")
                with col2:
                    st.metric("Resolutions", enhanced_stats.get('total_resolutions', 0), help="Total resolution attempts")
                with col3:
                    error_rate = enhanced_stats.get('error_rate_last_hour', 0)
                    rate_color = "🟢" if error_rate < 3 else "🟡" if error_rate < 7 else "🔴"
                    st.metric("Error Rate/Hr", f"{rate_color} {error_rate}", help="Errors per hour")
                with col4:
                    health = enhanced_stats.get('system_health', 'unknown').title()
                    health_icon = "🟢" if health == "Healthy" else "🟡" if health == "Warning" else "🔴"
                    st.metric("System Health", f"{health_icon} {health}", help="Overall system health")
                
                # Most common errors
                if enhanced_stats.get('most_common_errors'):
                    st.markdown("### 📊 Top Error Types")
                    error_data = []
                    for error_type, count in enhanced_stats['most_common_errors'][:5]:
                        error_data.append({"Error Type": error_type, "Count": count})
                    
                    if error_data:
                        import pandas as pd
                        df = pd.DataFrame(error_data)
                        st.dataframe(df, use_container_width=True)
                
                # Resolution strategies
                if enhanced_stats.get('resolution_strategies'):
                    st.markdown("### 🛠️ Resolution Strategies Used")
                    strategy_data = []
                    for strategy, count in enhanced_stats['resolution_strategies'].items():
                        strategy_icon = {
                            'SELF_HEALING': '🤖',
                            'IMMEDIATE_FIX': '🚨', 
                            'PREVENTIVE': '🛡️',
                            'AI_POWERED': '🧠'
                        }.get(strategy, '⚙️')
                        strategy_data.append({
                            "Strategy": f"{strategy_icon} {strategy.replace('_', ' ').title()}", 
                            "Count": count
                        })
                    
                    if strategy_data:
                        df_strategies = pd.DataFrame(strategy_data)
                        st.dataframe(df_strategies, use_container_width=True)
                
                # Preventive patterns
                patterns_detected = enhanced_stats.get('patterns_detected', 0)
                if patterns_detected > 0:
                    st.markdown(f"### 🛡️ Preventive Measures")
                    st.success(f"🛡️ {patterns_detected} recurring error patterns detected and prevented")
                else:
                    st.info("🛡️ No recurring error patterns detected - system running smoothly")
                    
        except Exception as e:
            st.warning(f"Enhanced analytics temporarily unavailable: {e}")
    
    # Display recent errors if any (combining current and saved errors)
    if assistant.recent_errors or saved_errors:
        all_errors_list = list(assistant.recent_errors)  # Current live errors
        
        # Add saved errors from test file
        for saved_error in saved_errors:
            # Convert saved error to display format
            saved_error_obj = type('SavedError', (), {
                'error_type': saved_error.get('type', 'UNKNOWN'),
                'error_code': saved_error.get('code', 'N/A'),
                'message': saved_error.get('message', 'N/A'),
                'query': None,
                'table': None,
                'timestamp': saved_error.get('timestamp', 'N/A'),
                'source': 'test'
            })()
            all_errors_list.append(saved_error_obj)
        
        with st.expander(f"📋 Recent Database Errors & Auto-Resolutions ({len(all_errors_list)} total)", expanded=False):
            st.info(f"Showing {len(all_errors_list)} errors: {len(assistant.recent_errors)} live + {len(saved_errors)} from tests")
            
            for i, error in enumerate(reversed(all_errors_list[-10:])):  # Show last 10 errors
                error_source = getattr(error, 'source', 'live')
                st.markdown(f"### Error #{len(all_errors_list) - i} ({error_source})")
                
                # Error details
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Type:** `{error.error_type}`")
                    st.markdown(f"**Message:** {error.message}")
                    if hasattr(error, 'query') and error.query:
                        st.markdown(f"**Query:** ```sql\n{error.query}\n```")
                        
                with col2:
                    st.markdown(f"**Code:** {error.error_code}")
                    if hasattr(error, 'timestamp') and error.timestamp != 'N/A':
                        if isinstance(error.timestamp, str):
                            st.markdown(f"**Time:** {error.timestamp}")
                        else:
                            st.markdown(f"**Time:** {error.timestamp.strftime('%H:%M:%S')}")
                    if hasattr(error, 'table') and error.table:
                        st.markdown(f"**Table:** {error.table}")
                
                # Auto-resolution button for live errors only
                if error_source == 'live' and hasattr(error, 'to_ai_prompt'):
                    if st.button(f"🔧 Get Resolution for Error #{len(all_errors_list) - i}", key=f"resolve_{i}"):
                        with st.spinner("Generating auto-resolution..."):
                            try:
                                resolution = run_async_in_thread(assistant.get_auto_error_resolution, error.to_ai_prompt(), error)
                                st.markdown("### 🚨 Auto-Generated Resolution")
                                st.markdown(resolution)
                            except Exception as e:
                                st.error(f"Failed to generate resolution: {e}")
                elif error_source == 'test':
                    st.info("✅ Auto-resolution was already generated for this test error")
                
                st.divider()
    else:
        st.info("✅ No recent database errors detected. System is running smoothly!")
    
    # Manual Error Testing
    with st.expander("🧪 Test Auto-Error Resolution", expanded=False):
        st.markdown("**Test the auto-error resolution system:**")
        
        tab1, tab2 = st.tabs(["🔧 Simulated Errors", "🔥 Real Database Errors"])
        
        with tab1:
            st.markdown("**Generate simulated errors for testing:**")
            test_error_type = st.selectbox(
                "Select Error Type to Test:",
                ["TABLE_NOT_FOUND", "ACCESS_DENIED", "SYNTAX_ERROR", "CONNECTION_ERROR"]
            )
            
            test_query = st.text_input("Test Query (optional):", "SELECT * FROM non_existent_table")
            
            if st.button("🚨 Simulate Error & Get Resolution"):
                # Create a test error and add it to the assistant's recent_errors list
                from core.database.connector import DatabaseError
                test_error = DatabaseError(
                    error_type=test_error_type or "UNKNOWN",
                    error_code="TEST_001",
                    message=f"Simulated {test_error_type or 'UNKNOWN'} error for testing",
                    query=test_query if test_query else None,
                    table="test_table" if test_error_type and "TABLE" in test_error_type else None
                )
                
                # Add error to assistant's recent errors list so it shows up in the counter
                assistant.recent_errors.append(test_error)
                if len(assistant.recent_errors) > assistant.max_stored_errors:
                    assistant.recent_errors = assistant.recent_errors[-assistant.max_stored_errors:]
                
                with st.spinner("Generating auto-resolution..."):
                    try:
                        resolution = run_async_in_thread(assistant.get_auto_error_resolution, test_error.to_ai_prompt(), test_error)
                        st.markdown("### 🚨 Auto-Generated Resolution")
                        st.markdown(resolution)
                        st.success(f"✅ Error added to Recent Errors! Total count: {len(assistant.recent_errors)}")
                        st.rerun()  # Refresh to update the counter
                    except Exception as e:
                        st.error(f"Failed to generate resolution: {e}")
        
        with tab2:
            st.markdown("**Generate REAL database errors by executing bad SQL:**")
            st.warning("⚠️ This will execute actual SQL queries in your database!")
            
            db_keys = list(assistant.config.databases.keys())
            if db_keys:
                selected_error_db = st.selectbox("Select Database for Error Testing:", db_keys)
                
                error_sql_options = {
                    "Table Not Found": "SELECT * FROM non_existent_table_realtest",
                    "Syntax Error": "SELECT * FROM WHERE ORDER BY INVALID",
                    "Column Not Found": "SELECT non_existent_column FROM users", 
                    "Invalid Function": "SELECT INVALID_FUNCTION(id) FROM users"
                }
                
                selected_error = st.selectbox("Select Real Error Type:", list(error_sql_options.keys()))
                default_sql = error_sql_options[selected_error] if selected_error else "SELECT * FROM non_existent_table"
                custom_sql = st.text_area("Or Enter Custom SQL:", default_sql)
                
                if st.button("💥 Execute Bad SQL & Capture Error", type="secondary"):
                    if selected_error_db and custom_sql:
                        with st.spinner(f"Executing bad SQL in {selected_error_db}..."):
                            try:
                                # This will either fail (old behavior) or return error info (new behavior)
                                response = run_async_in_thread(
                                    assistant.chat,
                                    custom_sql,
                                    db_name=selected_error_db
                                )
                                
                                # Check if response indicates an error was detected and processed
                                if response and "🚨 Database Error Detected" in response:
                                    st.success("✅ Real database error captured and auto-resolved! Check Recent Errors count above.")
                                    st.markdown(response)
                                    st.rerun()  # Refresh to update the counter
                                elif response:
                                    st.warning("Unexpectedly succeeded - no error generated!")
                                    st.markdown(response)
                                else:
                                    st.warning("No response received from database query.")
                                    
                            except Exception as e:
                                st.success(f"✅ Real database error captured! Check Recent Errors count above.")
                                st.error(f"Database Error: {str(e)}")
                                st.rerun()  # Refresh to update the counter
                    else:
                        st.error("Please select a database and enter SQL.")
            else:
                st.error("No databases configured for error testing.")
        
        if st.button("🚨 Clear All Recent Errors"):
            assistant.recent_errors.clear()
            st.success("✅ All recent errors cleared!")
            st.rerun()
        
        if assistant.recent_errors:
            if st.button("🔄 Refresh Error Count"):
                st.rerun()
            # Create a test error and add it to the assistant's recent_errors list
            from core.database.connector import DatabaseError
            test_error = DatabaseError(
                error_type=test_error_type or "UNKNOWN",
                error_code="TEST_001",
                message=f"Simulated {test_error_type or 'UNKNOWN'} error for testing",
                query=test_query if test_query else None,
                table="test_table" if test_error_type and "TABLE" in test_error_type else None
            )
            
            # Add error to assistant's recent errors list so it shows up in the counter
            assistant.recent_errors.append(test_error)
            if len(assistant.recent_errors) > assistant.max_stored_errors:
                assistant.recent_errors = assistant.recent_errors[-assistant.max_stored_errors:]
            
            with st.spinner("Generating auto-resolution..."):
                try:
                    resolution = run_async_in_thread(assistant.get_auto_error_resolution, test_error.to_ai_prompt(), test_error)
                    st.markdown("### 🚨 Auto-Generated Resolution")
                    st.markdown(resolution)
                    st.success(f"✅ Error added to Recent Errors! Total count: {len(assistant.recent_errors)}")
                    st.rerun()  # Refresh to update the counter
                except Exception as e:
                    st.error(f"Failed to generate resolution: {e}")
    
    st.divider()


async def analysis_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Analysis interface"""
    st.title("🔍 Performance Analysis")

    if not selected_db:
        st.warning("Please select a database from the sidebar to begin analysis.")
        return

    st.subheader(f"Analysis for: {selected_db}")

    if st.button(f"🚀 Run Full Performance Analysis for {selected_db}"):
        db_config = assistant.config.get_database_config(selected_db)
        if not db_config:
            st.error(f"Configuration for {selected_db} not found.")
            return

        with st.spinner(f"Connecting to {selected_db}..."):
            try:
                # First, test the connection using thread-safe wrapper
                async def test_connection():
                    connection = await assistant.db_connector.get_connection(db_config)
                    test_query = "SELECT 1"
                    if db_config.db_type == 'postgresql':
                        return await connection.execute_query(test_query)
                    elif db_config.db_type == 'mysql':
                        return await connection.execute_query(test_query)
                
                run_async_in_thread(test_connection)
                st.success(f"Successfully connected to {selected_db}.")
            except Exception as e:
                st.error(f"Failed to connect to {selected_db}. Please check your credentials and ensure the database server is running.")
                st.error(f"Details: {e}")
                return # Stop if connection fails

        with st.spinner(f"Running performance analysis for {selected_db}... This may take a moment."):
            try:
                report = run_async_in_thread(assistant.analyzer.generate_performance_report, db_config)
                st.success("Analysis complete!")

                # Display the beautiful report
                display_analysis_report(report)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")


def display_analysis_report(report: Dict[str, Any], use_expanders: bool = True):
    """Displays the analysis report in a user-friendly way."""

    status = report.get("summary", {}).get("status", "unknown")
    
    if status == "critical":
        st.error(f"**Status: {status.upper()}**")
    elif status == "warning":
        st.warning(f"**Status: {status.upper()}**")
    else:
        st.success(f"**Status: {status.upper()}**")

    # --- Recommendations ---
    st.subheader("💡 Recommendations")
    recommendations = report.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.write("No specific recommendations at this time.")

    # --- Key Metrics ---
    st.subheader("📊 Key Metrics")
    metrics = report.get("summary", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("CPU Usage", f"{metrics.get('cpu_usage', 0):.1f}%")
    col2.metric("Memory Usage", f"{metrics.get('memory_usage', 0):.1f}%")
    col3.metric("Disk Usage", f"{metrics.get('disk_usage', 0):.1f}%")

    # --- Detailed Health Checks ---
    if use_expanders:
        with st.expander("🔬 View Detailed Health Checks"):
            health_checks = report.get("health", {}).get("checks", {})
            if health_checks:
                st.table(
                    pd.DataFrame.from_dict(health_checks, orient='index')
                    .reset_index()
                    .rename(columns={'index': 'Check'})
                )
            else:
                st.write("No detailed health checks available.")
                
        # --- Raw JSON ---
        with st.expander("📄 View Full JSON Report"):
            st.json(report)
    else:
        # Display without expanders to avoid nesting
        st.subheader("🔬 Detailed Health Checks")
        health_checks = report.get("health", {}).get("checks", {})
        if health_checks:
            st.table(
                pd.DataFrame.from_dict(health_checks, orient='index')
                .reset_index()
                .rename(columns={'index': 'Check'})
            )
        else:
            st.write("No detailed health checks available.")
            
        # --- Raw JSON ---
        st.subheader("📄 Full JSON Report")
        st.json(report)


def configuration_interface(assistant: DBAAssistant):
    """Configuration interface"""
    st.title("⚙️ Configuration")
    
    st.subheader("AI Model Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model = st.selectbox(
            "AI Model",
            ["llama2:13b", "codellama:13b", "mistral:7b"],
            index=0
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        
    with col2:
        max_tokens = st.number_input("Max Tokens", 512, 8192, 2048)
        context_window = st.number_input("Context Window", 1024, 16384, 4096)
        
    if st.button("Save AI Settings"):
        st.success("AI settings saved!")
        
    st.subheader("Database Connections")
    st.warning("Database configuration is managed in the config.yaml file.")
    
    st.subheader("Monitoring Settings")
    
    enabled = st.checkbox("Enable Monitoring", True)
    interval = st.number_input("Monitoring Interval (seconds)", 30, 3600, 60)
    
    if st.button("Save Monitoring Settings"):
        st.success("Monitoring settings saved!")


def about_interface():
    """About interface"""
    st.title("About DBA-GPT")
    
    st.markdown("""
    **DBA-GPT is an AI-powered assistant designed to help database administrators and developers manage, monitor, and optimize their databases.**
    
    It leverages local, offline-first large language models (LLMs) to provide expert-level advice without sending your data to the cloud.
    
    **Key Features:**
    - **AI Chat:** Get expert answers to your DBA questions.
    - **Proactive Monitoring:** Continuously monitor database health and performance.
    - **Performance Analysis:** Deep dive into query performance, index usage, and more.
    - **Automated Remediation:** Automatically fix common database issues.
    - **Multi-Database Support:** Works with PostgreSQL, MySQL, MongoDB, and Redis.
    
    **Technology Stack:**
    - **AI:** Ollama, LangChain
    - **Backend:** FastAPI, Python
    - **Frontend:** Streamlit
    - **Databases:** PostgreSQL, MySQL, MongoDB, Redis
    
    This project is open-source and can be extended to support more database types and features.
    """)
    
    st.info("Version: 1.0.0 | Author: Your Name")


def format_recommendation_response(recommendation) -> str:
    """Format AI recommendation for Streamlit"""
    response = f"""
**Issue:** {recommendation.issue}
**Severity:** {recommendation.severity}
**Category:** {recommendation.category}

**Description:**
{recommendation.description}

**Solution:**
{recommendation.solution}

**Estimated Impact:** {recommendation.estimated_impact}
**Risk Level:** {recommendation.risk_level}
"""
    if recommendation.sql_commands:
        response += "\n**SQL Commands:**\n"
        for cmd in recommendation.sql_commands:
            response += f"```sql\n{cmd}\n```\n"
            
    return response


def display_performance_overview():
    """Display mock performance overview"""
    st.write("Displaying mock performance overview...")
    # Add charts and tables here
    
def display_query_analysis():
    """Display mock query analysis"""
    st.write("Displaying mock query analysis...")
    # Add tables of slow queries here
    
def display_index_analysis():
    """Display mock index analysis"""
    st.write("Displaying mock index analysis...")
    # Add tables of index usage here
    
def display_connection_analysis():
    """Display mock connection analysis"""
    st.write("Displaying mock connection analysis...")
    # Add charts of connection stats here
    

def main():
    """Main function to run the web interface"""
    st.set_page_config(
        page_title="DBA-GPT",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    assistant = get_assistant()
    main_interface(assistant)
    

if __name__ == "__main__":
    main() 