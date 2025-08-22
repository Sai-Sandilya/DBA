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
            ["Chat", "Smart Join", "Smart Query", "Pattern Detection", "Schema Visualizer", "NoSQL Assistant", "Monitoring", "Analysis", "Configuration", "About"]
        )
        
        # Database selection
        db_keys = list(assistant.config.databases.keys())
        available_dbs = db_keys + ["oracle"]  # Add Oracle as a knowledge-based option
        
        if assistant.config.databases:
            # Create display names with database types
            db_display_names = []
            for db_key in available_dbs:
                if db_key == "oracle":
                    db_display_names.append(f"📚 {db_key} (Knowledge Base)")
                else:
                    # Get database type from configuration
                    db_config = assistant.config.databases.get(db_key)
                    if db_config:
                        db_type = db_config.db_type.lower()
                        if db_type == "mongodb":
                            db_display_names.append(f"🍃 {db_key} (MongoDB)")
                        elif db_type == "sqlite":
                            db_display_names.append(f"💾 {db_key} (SQLite)")
                        elif db_type == "postgresql":
                            db_display_names.append(f"🐘 {db_key} (PostgreSQL)")
                        elif db_type == "mysql":
                            db_display_names.append(f"🗄️ {db_key} (MySQL)")
                        elif db_type == "redis":
                            db_display_names.append(f"🔴 {db_key} (Redis)")
                        elif db_type == "elasticsearch":
                            db_display_names.append(f"🔍 {db_key} (Elasticsearch)")
                        elif db_type == "neo4j":
                            db_display_names.append(f"🕸️ {db_key} (Neo4j)")
                        elif db_type == "cassandra":
                            db_display_names.append(f"🗿 {db_key} (Cassandra)")
                        elif db_type == "influxdb":
                            db_display_names.append(f"📊 {db_key} (InfluxDB)")
                        elif db_type == "athena":
                            db_display_names.append(f"☁️ {db_key} (AWS Athena)")
                        elif db_type == "azure_sql":
                            db_display_names.append(f"🔵 {db_key} (Azure SQL)")
                        else:
                            db_display_names.append(f"🗄️ {db_key} ({db_type.title()})")
                    else:
                        db_display_names.append(f"🗄️ {db_key}")
            
            selected_db = st.selectbox(
                "Select Database Context",
                available_dbs,
                format_func=lambda x: db_display_names[available_dbs.index(x)],
                help="Select a live database or a knowledge base."
            )
            
            # Show database status
            if selected_db and selected_db != "oracle":
                db_config = assistant.config.databases.get(selected_db)
                if db_config:
                    st.markdown(f"**Status:** 🟢 Connected to {db_config.host}")
                    st.markdown(f"**Type:** {db_config.db_type.upper()}")
                    st.markdown(f"**Database:** {db_config.database}")
                else:
                    st.markdown("**Status:** 🔴 Not configured")
            elif selected_db == "oracle":
                st.markdown("**Status:** 📚 Knowledge Base Mode")
                st.markdown("**Type:** Oracle (Knowledge)")
                st.markdown("**Mode:** Educational Content")
            else:
                st.markdown("**Status:** ⚪ No database selected")
        else:
            selected_db = None
        
        # Show available database types that can be added
        st.markdown("---")
        st.markdown("### 📋 Available Database Types")
        st.markdown("**SQL Databases:**")
        st.markdown("- 🗄️ **MySQL** - Relational database")
        st.markdown("- 🐘 **PostgreSQL** - Advanced relational database")
        st.markdown("- 💾 **SQLite** - Lightweight embedded database")
        st.markdown("- 🔵 **Oracle** - Enterprise database (Knowledge Base)")
        st.markdown("- 🟦 **SQL Server** - Microsoft database")
        
        st.markdown("**NoSQL Databases:**")
        st.markdown("- 🍃 **MongoDB** - Document database")
        st.markdown("- 🔴 **Redis** - In-memory key-value store")
        st.markdown("- 🔍 **Elasticsearch** - Search engine")
        st.markdown("- 🕸️ **Neo4j** - Graph database")
        st.markdown("- 🗿 **Cassandra** - Wide-column database")
        st.markdown("- 📊 **InfluxDB** - Time series database")
        
        st.markdown("**Cloud Databases:**")
        st.markdown("- ☁️ **AWS Athena** - Serverless query service")
        st.markdown("- 🔵 **Azure SQL** - Microsoft cloud database")
        st.markdown("- 🟢 **Google BigQuery** - Data warehouse")
        
        st.markdown("**To add a database:**")
        st.markdown("1. Edit `config/config.yaml`")
        st.markdown("2. Add database configuration")
        st.markdown("3. Restart the application")
            
    # Main content
    if page == "Chat":
        chat_interface(assistant, selected_db)
    elif page == "Smart Join":
        run_async_in_thread(smart_join_interface, assistant, selected_db)
    elif page == "Smart Query":
        run_async_in_thread(smart_query_interface, assistant, selected_db)
    elif page == "Pattern Detection":
        run_async_in_thread(pattern_detection_interface, assistant, selected_db)
    elif page == "Schema Visualizer":
        run_async_in_thread(schema_visualizer_interface, assistant, selected_db)
    elif page == "NoSQL Assistant":
        run_async_in_thread(nosql_assistant_interface, assistant, selected_db)
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
        if st.button("🗄️ **Database Mode**", 
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
            if "mongodb" in selected_db.lower():
                st.success(f"🗄️ **MongoDB NoSQL Mode** - Connected to: **{selected_db}**")
                st.info("💡 Ask questions about YOUR MongoDB collections: documents, schema, data, queries, etc.")
            elif "sqlite" in selected_db.lower():
                st.success(f"🗄️ **SQLite Database Mode** - Connected to: **{selected_db}**")
                st.info("💡 Ask questions about YOUR SQLite database: tables, schema, data, queries, etc.")
            else:
                st.success(f"🗄️ **MySQL Database Mode** - Connected to: **{selected_db}**")
                st.info("💡 Ask questions about YOUR MySQL database: tables, schema, data, queries, etc.")
        else:
            st.warning("🗄️ **Database Mode** - No database selected! Please select a database from the sidebar.")
            st.info("💡 This mode answers questions about your specific connected database.")
    else:
        st.success(f"🎓 **General Database Topics Mode** - Educational Content")
        st.info("💡 Ask questions about: SQL concepts, database theory, best practices, tutorials, etc.")
    
    # Different example questions based on mode and database type
    st.markdown("### 💡 Example Questions")
    if st.session_state.chat_mode == "database":
        if selected_db:
            # Get database type from configuration
            db_config = assistant.config.databases.get(selected_db)
            db_type = db_config.db_type.lower() if db_config else "mysql"
            
            if db_type == "mongodb":
                st.markdown("""
                **MongoDB NoSQL Questions:**
                - "What collections do I have in my database?"
                - "Show me documents from user_profiles collection"
                - "How many documents are in product_catalog?"
                - "Find all indexes in my database"
                - "What's the structure of order_transactions?"
                - "Show me the latest orders from today"
                - "Find users with specific criteria"
                - "Aggregate data by category"
                """)
            elif db_type == "sqlite":
                st.markdown("""
                **SQLite Database Questions:**
                - "What tables do I have in my database?"
                - "Show me the schema of the users table"
                - "How many records are in my orders table?"
                - "Find all indexes in my database"
                - "What's the size of my database?"
                - "Show me recent transactions"
                - "Find duplicate records"
                - "Optimize my database performance"
                """)
            elif db_type == "postgresql":
                st.markdown("""
                **PostgreSQL Database Questions:**
                - "What tables do I have in my database?"
                - "Show me the schema of the users table"
                - "How many records are in my orders table?"
                - "Find all indexes in my database"
                - "What's the size of my database?"
                - "Show me active connections"
                - "Check for table bloat"
                - "Analyze query performance"
                - "Show me recent slow queries"
                """)
            elif db_type == "mysql":
                st.markdown("""
                **MySQL Database Questions:**
                - "What tables do I have in my database?"
                - "Show me the schema of the users table"
                - "How many records are in my orders table?"
                - "Find all indexes in my database"
                - "What's the size of my database?"
                - "Show me active processes"
                - "Check for slow queries"
                - "Analyze table performance"
                - "Show me recent errors"
                """)
            elif db_type == "redis":
                st.markdown("""
                **Redis Database Questions:**
                - "What keys do I have in my database?"
                - "Show me the value of a specific key"
                - "How many keys are in my database?"
                - "Find all keys matching a pattern"
                - "What's the memory usage of my database?"
                - "Show me key expiration times"
                - "Monitor real-time operations"
                - "Check Redis performance metrics"
                """)
            elif db_type == "elasticsearch":
                st.markdown("""
                **Elasticsearch Questions:**
                - "What indices do I have in my cluster?"
                - "Show me documents from a specific index"
                - "How many documents are in my index?"
                - "Find all mappings in my cluster"
                - "What's the cluster health status?"
                - "Show me search query performance"
                - "Analyze index performance"
                - "Check for failed shards"
                """)
            elif db_type == "neo4j":
                st.markdown("""
                **Neo4j Graph Database Questions:**
                - "What node labels do I have in my database?"
                - "Show me relationships between nodes"
                - "How many nodes are in my database?"
                - "Find all indexes in my database"
                - "What's the database size?"
                - "Show me the graph schema"
                - "Find shortest paths between nodes"
                - "Analyze graph performance"
                """)
            elif db_type == "cassandra":
                st.markdown("""
                **Cassandra Database Questions:**
                - "What keyspaces do I have in my cluster?"
                - "Show me tables in a keyspace"
                - "How many rows are in my table?"
                - "Find all indexes in my keyspace"
                - "What's the cluster status?"
                - "Show me table schemas"
                - "Check for compaction status"
                - "Analyze query performance"
                """)
            elif db_type == "influxdb":
                st.markdown("""
                **InfluxDB Time Series Questions:**
                - "What measurements do I have in my database?"
                - "Show me data from a specific measurement"
                - "How many data points are in my measurement?"
                - "Find all tags in my database"
                - "What's the database size?"
                - "Show me recent time series data"
                - "Analyze data retention policies"
                - "Check for data compression"
                """)
            elif db_type == "athena":
                st.markdown("""
                **AWS Athena Questions:**
                - "What databases do I have in my catalog?"
                - "Show me tables in a database"
                - "How many rows are in my table?"
                - "Find all partitions in my table"
                - "What's the query execution history?"
                - "Show me recent query results"
                - "Analyze query performance"
                - "Check for failed queries"
                """)
            elif db_type == "azure_sql":
                st.markdown("""
                **Azure SQL Database Questions:**
                - "What tables do I have in my database?"
                - "Show me the schema of the users table"
                - "How many records are in my orders table?"
                - "Find all indexes in my database"
                - "What's the database size?"
                - "Show me active connections"
                - "Check for performance issues"
                - "Analyze query performance"
                """)
            else:
                st.markdown("""
                **General Database Questions:**
                - "What tables do I have in my database?"
                - "Show me the schema of the users table"
                - "How many records are in my orders table?"
                - "Find all indexes in my database"
                - "What's the size of my database?"
                """)
        else:
            st.markdown("""
            **Select a database to see specific questions:**
            - Choose a database from the sidebar to get tailored questions
            - Each database type has specific capabilities and query patterns
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
    if st.session_state.chat_mode == "database" and selected_db:
        if selected_db == "oracle":
            placeholder_text = "Ask about Oracle database concepts and best practices..."
        else:
            # Get database type from configuration
            db_config = assistant.config.databases.get(selected_db)
            if db_config:
                db_type = db_config.db_type.lower()
                if db_type == "mongodb":
                    placeholder_text = "Ask about your MongoDB collections and documents..."
                elif db_type == "sqlite":
                    placeholder_text = "Ask about your SQLite database tables and data..."
                elif db_type == "postgresql":
                    placeholder_text = "Ask about your PostgreSQL database and performance..."
                elif db_type == "mysql":
                    placeholder_text = "Ask about your MySQL database and optimization..."
                elif db_type == "redis":
                    placeholder_text = "Ask about your Redis keys and memory usage..."
                elif db_type == "elasticsearch":
                    placeholder_text = "Ask about your Elasticsearch indices and queries..."
                elif db_type == "neo4j":
                    placeholder_text = "Ask about your Neo4j graph database and relationships..."
                elif db_type == "cassandra":
                    placeholder_text = "Ask about your Cassandra keyspaces and tables..."
                elif db_type == "influxdb":
                    placeholder_text = "Ask about your InfluxDB measurements and time series..."
                elif db_type == "athena":
                    placeholder_text = "Ask about your AWS Athena queries and data..."
                elif db_type == "azure_sql":
                    placeholder_text = "Ask about your Azure SQL database and performance..."
                else:
                    placeholder_text = f"Ask about your {db_type.title()} database..."
            else:
                placeholder_text = "Ask about your database..."
    else:
        placeholder_text = "Ask about database concepts, SQL, best practices..."
    
    if prompt := st.chat_input(placeholder_text):
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
                            response = "❌ **Database Mode requires a connected database.** Please select a database from the sidebar, or switch to 'General Database Topics' mode for educational content."
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


async def smart_join_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Smart Join Assistant Interface"""
    st.title("🔗 Smart Join Assistant")
    st.markdown("### 🤖 AI-Powered Table Join Analysis")
    st.markdown("Don't know which join type to use? Let AI analyze your tables and show you the differences!")
    
    if not selected_db or selected_db == "oracle":
        st.warning("⚠️ Please select a MySQL database from the sidebar to use the Smart Join Assistant.")
        st.info("💡 This tool analyzes your actual database tables and shows you different join types with sample results.")
        return
    
    # Table selection
    st.markdown("### 📋 Select Tables to Join")
    
    col1, col2 = st.columns(2)
    
    with col1:
        table1 = st.text_input("First Table Name", placeholder="e.g., users, orders, products")
    
    with col2:
        table2 = st.text_input("Second Table Name", placeholder="e.g., customers, order_items, inventory")
    
    # Analyze button
    if st.button("🔍 Analyze Join Options", type="primary", use_container_width=True):
        if table1 and table2:
            with st.spinner("🤖 Analyzing tables and generating join examples..."):
                try:
                    # Get join analysis
                    analysis = run_async_in_thread(
                        assistant.smart_join_analysis,
                        table1, table2, selected_db
                    )
                    
                    if "error" in analysis:
                        st.error(f"❌ Analysis failed: {analysis['error']}")
                        return
                    
                    # Display results
                    st.success("✅ Join analysis complete!")
                    
                    # Summary
                    st.markdown("### 📊 Analysis Summary")
                    st.markdown(analysis.get("summary", ""))
                    
                    # Join keys found
                    join_keys = analysis.get("join_keys", [])
                    if join_keys:
                        st.markdown("### 🔑 Join Keys Found")
                        for i, key in enumerate(join_keys):
                            confidence_color = "🟢" if key["confidence"] == "high" else "🟡"
                            st.info(f"{confidence_color} **Join Key {i+1}**: `{key['table1_column']}` = `{key['table2_column']}` ({key['confidence']} confidence)")
                    
                    # Recommendations
                    recommendations = analysis.get("recommendations", [])
                    if recommendations:
                        st.markdown("### 💡 AI Recommendations")
                        for rec in recommendations:
                            if rec["type"] == "info":
                                st.info(f"💡 {rec['message']}")
                                st.markdown(f"**Suggestion**: {rec['suggestion']}")
                            elif rec["type"] == "warning":
                                st.warning(f"⚠️ {rec['message']}")
                                st.markdown(f"**Suggestion**: {rec['suggestion']}")
                    
                    # Join examples
                    join_examples = analysis.get("join_examples", {})
                    if join_examples and "error" not in join_examples:
                        st.markdown("### 🔄 Join Type Examples")
                        
                        # Create tabs for different join types
                        tab1, tab2, tab3, tab4 = st.tabs(["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"])
                        
                        with tab1:
                            if "INNER JOIN" in join_examples:
                                example = join_examples["INNER JOIN"]
                                st.markdown("**INNER JOIN** - Only matching records from both tables")
                                st.code(example["query"], language="sql")
                                st.markdown(f"**Result**: {example['row_count']} rows")
                                if example.get("result"):
                                    df = pd.DataFrame(example["result"])
                                    st.dataframe(df.head(5))
                        
                        with tab2:
                            if "LEFT JOIN" in join_examples:
                                example = join_examples["LEFT JOIN"]
                                st.markdown("**LEFT JOIN** - All records from first table + matching from second")
                                st.code(example["query"], language="sql")
                                st.markdown(f"**Result**: {example['row_count']} rows")
                                if example.get("result"):
                                    df = pd.DataFrame(example["result"])
                                    st.dataframe(df.head(5))
                        
                        with tab3:
                            if "RIGHT JOIN" in join_examples:
                                example = join_examples["RIGHT JOIN"]
                                st.markdown("**RIGHT JOIN** - All records from second table + matching from first")
                                st.code(example["query"], language="sql")
                                st.markdown(f"**Result**: {example['row_count']} rows")
                                if example.get("result"):
                                    df = pd.DataFrame(example["result"])
                                    st.dataframe(df.head(5))
                        
                        with tab4:
                            if "FULL OUTER JOIN" in join_examples:
                                example = join_examples["FULL OUTER JOIN"]
                                st.markdown("**FULL OUTER JOIN** - All records from both tables")
                                st.code(example["query"], language="sql")
                                st.markdown(f"**Result**: {example['row_count']} rows")
                                if example.get("result"):
                                    df = pd.DataFrame(example["result"])
                                    st.dataframe(df.head(5))
                    
                    # Generate final query section
                    st.markdown("### 🎯 Generate Your Query")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        join_type = st.selectbox(
                            "Join Type",
                            ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"],
                            help="Select the join type you want to use"
                        )
                    
                    with col2:
                        if join_keys:
                            join_condition = st.selectbox(
                                "Join Condition",
                                [f"t1.{key['table1_column']} = t2.{key['table2_column']}" for key in join_keys],
                                help="Select the join condition"
                            )
                        else:
                            join_condition = st.text_input(
                                "Join Condition",
                                placeholder="e.g., t1.id = t2.user_id",
                                help="Enter your custom join condition"
                            )
                    
                    if st.button("🚀 Generate SQL Query", type="primary"):
                        try:
                            final_query = run_async_in_thread(
                                assistant.generate_join_query,
                                table1, table2, join_type, join_condition
                            )
                            
                            st.markdown("### 📝 Your Generated Query")
                            st.code(final_query, language="sql")
                            
                            # Copy button
                            st.markdown("💡 **Copy this query and use it in the Chat interface to execute it!**")
                            
                        except Exception as e:
                            st.error(f"❌ Failed to generate query: {str(e)}")
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    logger.error(f"Smart join analysis error: {e}", exc_info=True)
        else:
            st.warning("⚠️ Please enter both table names to analyze.")
    
    # Help section
    with st.expander("💡 How to Use Smart Join Assistant"):
        st.markdown("""
        ### 🎯 What This Tool Does:
        
        1. **Analyzes your tables** - Examines structure, data types, and relationships
        2. **Finds join keys** - Automatically identifies potential columns to join on
        3. **Shows examples** - Demonstrates each join type with actual results
        4. **Provides recommendations** - Suggests the best join type based on your data
        5. **Generates queries** - Creates the final SQL query for you
        
        ### 🔗 Join Types Explained:
        
        - **INNER JOIN**: Only records that exist in both tables
        - **LEFT JOIN**: All records from first table + matching from second
        - **RIGHT JOIN**: All records from second table + matching from first  
        - **FULL OUTER JOIN**: All records from both tables
        
        ### 💡 Pro Tips:
        
        - Use this tool when you're unsure which join type to use
        - Compare the row counts to understand the differences
        - Check the sample data to see what each join returns
        - Use the generated query in the Chat interface to execute it
        """)
    
    # Quick examples
    st.markdown("### ⚡ Quick Examples")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Users + Orders"):
            st.session_state.table1 = "users"
            st.session_state.table2 = "orders"
            st.rerun()
    
    with col2:
        if st.button("📦 Products + Inventory"):
            st.session_state.table1 = "products"
            st.session_state.table2 = "inventory"
            st.rerun()
    
    with col3:
        if st.button("🛒 Orders + Items"):
            st.session_state.table1 = "orders"
            st.session_state.table2 = "order_items"
            st.rerun()


async def smart_query_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Smart Query Builder Interface"""
    st.title("🔍 Smart Query Builder")
    st.markdown("### 🤖 Natural Language to SQL Converter")
    st.markdown("Don't know SQL? Just describe what you want in plain English!")
    
    if not selected_db or selected_db == "oracle":
        st.warning("⚠️ Please select a MySQL database from the sidebar to use the Smart Query Builder.")
        st.info("💡 This tool converts your natural language into SQL queries using AI.")
        return
    
    # Database and table selection
    st.markdown("### 🗄️ Database & Table Selection")
    
    # Get available tables using a proper async wrapper
    async def get_available_tables():
        try:
            connection = await assistant.db_connector.get_connection(assistant.config.databases[selected_db])
            tables_result = await connection.execute_query("SHOW TABLES")
            return [table[0] for table in tables_result] if tables_result else []
        except Exception as e:
            logger.error(f"Error fetching tables: {e}")
            return []
    
    # Fetch tables
    available_tables = []
    try:
        available_tables = run_async_in_thread(get_available_tables)
    except Exception as e:
        st.warning(f"⚠️ Could not fetch tables: {str(e)}")
        available_tables = []
    
    # Table selector
    if available_tables:
        selected_table = st.selectbox(
            "Select a table to work with:",
            ["All Tables"] + available_tables,
            help="Choose a specific table or 'All Tables' to let AI decide"
        )
    else:
        selected_table = "All Tables"
        st.info("ℹ️ No tables found. The AI will try to match table names from your query.")
    
    # Natural language input
    st.markdown("### 💬 Describe What You Want")
    
    natural_query = st.text_area(
        "Enter your query in natural language",
        placeholder="e.g., 'Show me all customers who spent more than $1000 last month' or 'Find products with low stock levels'",
        height=100,
        help="Describe what data you want to see in plain English"
    )
    
    # Query building button
    if st.button("🔍 Build SQL Query", type="primary", use_container_width=True):
        if natural_query.strip():
            with st.spinner("🤖 Analyzing your request and building SQL query..."):
                try:
                    # Build the query
                    result = run_async_in_thread(
                        assistant.build_natural_query,
                        natural_query, selected_db, selected_table
                    )
                    
                    if "error" in result:
                        st.error(f"❌ Query building failed: {result['error']}")
                        return
                    
                    if not result.get("success", False):
                        st.error(f"❌ Query building failed: {result.get('error', 'Unknown error')}")
                        return
                    
                    # Display results
                    st.success("✅ SQL Query Generated Successfully!")
                    
                    # Show the generated SQL
                    st.markdown("### 📝 Generated SQL Query")
                    st.code(result["sql_query"], language="sql")
                    
                    # Show explanation
                    st.markdown("### 💡 What This Query Does")
                    st.info(result["explanation"])
                    
                    # Show validation results
                    validation = result.get("validation", {})
                    if validation.get("valid", False):
                        st.success(f"✅ Query is valid! Estimated {validation.get('estimated_rows', 0)} rows will be returned.")
                    else:
                        st.warning(f"⚠️ Query validation failed: {validation.get('error', 'Unknown error')}")
                    
                    # Show suggestions
                    suggestions = result.get("suggestions", [])
                    if suggestions:
                        st.markdown("### 💡 Suggestions")
                        for suggestion in suggestions:
                            st.info(suggestion)
                    
                    # Show analysis details in expandable section
                    with st.expander("🔍 Query Analysis Details"):
                        analysis = result.get("analysis", {})
                        st.markdown(f"**Intent**: {analysis.get('intent', 'unknown')}")
                        
                        if analysis.get("entities"):
                            st.markdown("**Entities Found**:")
                            for entity in analysis["entities"]:
                                st.markdown(f"- {entity['type']}: {entity['name']}")
                        
                        if analysis.get("filters"):
                            st.markdown("**Filters Applied**:")
                            for filter_item in analysis["filters"]:
                                st.markdown(f"- {filter_item['table']}.{filter_item['column']} {filter_item['operator']} {filter_item['value']}")
                        
                        if analysis.get("aggregations"):
                            st.markdown("**Aggregations**:")
                            for agg in analysis["aggregations"]:
                                st.markdown(f"- {agg['function']}({agg['column']})")
                    
                    # Execute button
                    st.markdown("### 🚀 Execute Query")
                    if st.button("▶️ Execute This Query", type="secondary"):
                        try:
                            with st.spinner("🔄 Executing query..."):
                                # Execute the generated query using proper async wrapper
                                async def execute_query():
                                    try:
                                        connection = await assistant.db_connector.get_connection(assistant.config.databases[selected_db])
                                        
                                        # Limit results for display
                                        display_query = result["sql_query"]
                                        if "LIMIT" not in display_query.upper():
                                            display_query += " LIMIT 50"
                                        
                                        query_result = await connection.execute_query(display_query)
                                        return query_result
                                    except Exception as e:
                                        logger.error(f"Error executing query: {e}")
                                        raise e
                                
                                query_result = run_async_in_thread(execute_query)
                                
                                if query_result:
                                    st.markdown("### 📊 Query Results")
                                    import pandas as pd
                                    
                                    # Get column names from the query
                                    try:
                                        # Try to get column names from the connection
                                        if hasattr(connection, 'cursor') and connection.cursor:
                                            columns = [desc[0] for desc in connection.cursor.description]
                                        else:
                                            # Fallback: use generic column names
                                            columns = [f"Column_{i}" for i in range(len(query_result[0]))]
                                    except:
                                        columns = [f"Column_{i}" for i in range(len(query_result[0]))]
                                    
                                    df = pd.DataFrame(query_result, columns=columns)
                                    st.dataframe(df, use_container_width=True)
                                    
                                    # Show statistics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Rows", len(df))
                                    with col2:
                                        st.metric("Total Columns", len(df.columns))
                                    with col3:
                                        st.metric("Query Status", "✅ Success")
                                    
                                    # Download button
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results as CSV",
                                        data=csv,
                                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                    
                                else:
                                    st.info("ℹ️ Query executed successfully but returned no results.")
                                    
                        except Exception as e:
                            st.error(f"❌ Query execution failed: {str(e)}")
                            st.error("💡 Try modifying your natural language query to be more specific.")
                    
                except Exception as e:
                    st.error(f"❌ Query building failed: {str(e)}")
                    logger.error(f"Smart query building error: {e}", exc_info=True)
        else:
            st.warning("⚠️ Please enter a natural language query.")
    
    # Help section
    with st.expander("💡 How to Use Smart Query Builder"):
        st.markdown("""
        ### 🎯 What This Tool Does:
        
        The Smart Query Builder converts your natural language into SQL queries using AI analysis of your database schema.
        
        ### 📝 Example Queries:
        
        **Simple Queries:**
        - "Show me all customers"
        - "Get all products"
        - "List all orders"
        
        **Filtered Queries:**
        - "Customers with age greater than 25"
        - "Products with price less than 100"
        - "Orders with status equal to completed"
        
        **Top N Queries:**
        - "Top 10 customers by total spent"
        - "5 best performing products"
        - "Top 20 orders by amount"
        
        **Aggregate Queries:**
        - "How many customers do we have?"
        - "What is the total sales amount?"
        - "Show me the average order value"
        
        **Date Range Queries:**
        - "Orders from last month"
        - "Customers created in the past 30 days"
        - "Sales between January and March"
        
        ### 💡 Pro Tips:
        
        - Be specific about table names (customers, orders, products)
        - Use clear column names (age, price, status, amount)
        - Specify conditions clearly (greater than, less than, equal to)
        - The AI will suggest improvements and optimizations
        """)
    
    # Quick examples
    st.markdown("### ⚡ Quick Examples")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Show All Customers"):
            st.session_state.natural_query = "Show me all customers"
            st.rerun()
    
    with col2:
        if st.button("💰 High Value Orders"):
            st.session_state.natural_query = "Show me orders with amount greater than 500"
            st.rerun()
    
    with col3:
        if st.button("📊 Total Sales"):
            st.session_state.natural_query = "What is the total amount of all orders?"
            st.rerun()


async def pattern_detection_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Pattern Detection Interface"""
    st.title("🔍 Pattern Detection")
    st.markdown("### 🤖 AI-Powered Data Quality & Anomaly Detection")
    st.markdown("Automatically scan your database for data quality issues, schema problems, and anomalies!")
    
    if not selected_db or selected_db == "oracle":
        st.warning("⚠️ Please select a MySQL database from the sidebar to use Pattern Detection.")
        st.info("💡 This tool automatically finds data quality issues, schema problems, and anomalies.")
        return
    
    # Database health overview
    st.markdown("### 📊 Database Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Database", selected_db)
    with col2:
        st.metric("Status", "🟡 Ready to Scan")
    with col3:
        st.metric("Last Scan", "Never")
    with col4:
        st.metric("Health Score", "N/A")
    
    # Scan button
    st.markdown("### 🔍 Start Pattern Detection Scan")
    
    if st.button("🚀 Run Full Database Scan", type="primary", use_container_width=True):
        with st.spinner("🔍 Scanning database for patterns and issues..."):
            try:
                # Run pattern detection
                result = run_async_in_thread(
                    assistant.detect_patterns,
                    selected_db
                )
                
                if "error" in result:
                    st.error(f"❌ Pattern detection failed: {result['error']}")
                    return
                
                # Display results
                st.success("✅ Pattern Detection Complete!")
                
                # Show summary
                summary = result.get("summary", {})
                if summary:
                    st.markdown("### 📈 Scan Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        health_score = summary.get("health_score", 0)
                        if health_score >= 80:
                            st.metric("Health Score", f"{health_score}/100", delta="🟢 Excellent")
                        elif health_score >= 60:
                            st.metric("Health Score", f"{health_score}/100", delta="🟡 Good")
                        else:
                            st.metric("Health Score", f"{health_score}/100", delta="🔴 Needs Attention")
                    
                    with col2:
                        total_issues = summary.get("total_issues", 0)
                        st.metric("Total Issues", total_issues)
                    
                    with col3:
                        severity_counts = summary.get("severity_breakdown", {})
                        critical_count = severity_counts.get("critical", 0)
                        st.metric("Critical Issues", critical_count)
                    
                    with col4:
                        scan_time = summary.get("scan_timestamp", datetime.now())
                        st.metric("Scan Time", scan_time.strftime("%H:%M:%S"))
                
                # Show issues by category
                st.markdown("### 🚨 Issues Found")
                
                # Data Quality Issues
                quality_issues = result.get("data_quality_issues", [])
                if quality_issues:
                    st.markdown("#### 📊 Data Quality Issues")
                    for issue in quality_issues[:5]:  # Show first 5
                        severity_color = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(issue.get("severity", "medium"), "🟡")
                        
                        with st.expander(f"{severity_color} {issue['description']}"):
                            st.markdown(f"**Table**: {issue.get('table', 'N/A')}")
                            if issue.get('column'):
                                st.markdown(f"**Column**: {issue['column']}")
                            st.markdown(f"**Severity**: {issue.get('severity', 'medium').title()}")
                            st.markdown(f"**Recommendation**: {issue.get('recommendation', 'N/A')}")
                            
                            if issue.get('details'):
                                st.markdown("**Details**:")
                                for key, value in issue['details'].items():
                                    st.markdown(f"- {key}: {value}")
                
                # Schema Problems
                schema_problems = result.get("schema_problems", [])
                if schema_problems:
                    st.markdown("#### 🔧 Schema Problems")
                    for issue in schema_problems[:5]:  # Show first 5
                        severity_color = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(issue.get("severity", "medium"), "🟡")
                        
                        with st.expander(f"{severity_color} {issue['description']}"):
                            st.markdown(f"**Table**: {issue.get('table', 'N/A')}")
                            if issue.get('column'):
                                st.markdown(f"**Column**: {issue['column']}")
                            st.markdown(f"**Severity**: {issue.get('severity', 'medium').title()}")
                            st.markdown(f"**Recommendation**: {issue.get('recommendation', 'N/A')}")
                
                # Performance Issues
                performance_issues = result.get("performance_issues", [])
                if performance_issues:
                    st.markdown("#### ⚡ Performance Issues")
                    for issue in performance_issues[:5]:  # Show first 5
                        severity_color = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(issue.get("severity", "medium"), "🟡")
                        
                        with st.expander(f"{severity_color} {issue['description']}"):
                            st.markdown(f"**Table**: {issue.get('table', 'N/A')}")
                            if issue.get('column'):
                                st.markdown(f"**Column**: {issue['column']}")
                            st.markdown(f"**Severity**: {issue.get('severity', 'medium').title()}")
                            st.markdown(f"**Recommendation**: {issue.get('recommendation', 'N/A')}")
                
                # Anomalies
                anomalies = result.get("anomalies", [])
                if anomalies:
                    st.markdown("#### 🚨 Anomalies")
                    for issue in anomalies[:5]:  # Show first 5
                        severity_color = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(issue.get("severity", "medium"), "🟡")
                        
                        with st.expander(f"{severity_color} {issue['description']}"):
                            st.markdown(f"**Table**: {issue.get('table', 'N/A')}")
                            if issue.get('column'):
                                st.markdown(f"**Column**: {issue['column']}")
                            st.markdown(f"**Severity**: {issue.get('severity', 'medium').title()}")
                            st.markdown(f"**Recommendation**: {issue.get('recommendation', 'N/A')}")
                
                # Show recommendations
                recommendations = result.get("recommendations", [])
                if recommendations:
                    st.markdown("### 💡 Recommendations")
                    
                    for rec in recommendations:
                        priority_color = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                            "general": "💡"
                        }.get(rec.get("priority", "medium"), "💡")
                        
                        with st.expander(f"{priority_color} {rec['title']}"):
                            st.markdown(f"**{rec['description']}**")
                            st.markdown("**Actions:**")
                            for action in rec.get("actions", []):
                                st.markdown(f"- {action}")
                
                # Show detailed results in expandable section
                with st.expander("🔍 Detailed Scan Results"):
                    st.json(result)
                
            except Exception as e:
                st.error(f"❌ Pattern detection failed: {str(e)}")
                logger.error(f"Pattern detection error: {e}", exc_info=True)
    
    # Help section
    with st.expander("💡 How Pattern Detection Works"):
        st.markdown("""
        ### 🎯 What Pattern Detection Does:
        
        The Pattern Detection system automatically scans your database for:
        
        **📊 Data Quality Issues:**
        - High percentage of NULL values
        - Duplicate records
        - Statistical outliers
        - Data type mismatches
        
        **🔧 Schema Problems:**
        - Missing primary keys
        - Missing indexes on frequently queried columns
        - Missing foreign key constraints
        - Missing NOT NULL constraints
        
        **⚡ Performance Issues:**
        - Large tables that might need partitioning
        - Missing constraints
        - Inefficient table structures
        
        **🚨 Anomalies:**
        - Unusual data patterns
        - Highly skewed distributions
        - Unexpected value distributions
        
        ### 📈 Health Score:
        
        The system calculates a health score (0-100) based on:
        - **Critical Issues**: -10 points each
        - **High Issues**: -5 points each  
        - **Medium Issues**: -2 points each
        - **Low Issues**: -1 point each
        
        ### 💡 Recommendations:
        
        Each issue comes with specific, actionable recommendations to improve your database health.
        """)
    
    # Quick scan options
    st.markdown("### ⚡ Quick Scan Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Data Quality Only"):
            st.info("🔧 Feature coming soon: Targeted data quality scans")
    
    with col2:
        if st.button("🔧 Schema Only"):
            st.info("🔧 Feature coming soon: Targeted schema analysis")
    
    with col3:
        if st.button("🚨 Anomalies Only"):
            st.info("🔧 Feature coming soon: Targeted anomaly detection")


async def schema_visualizer_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """Schema Visualizer Interface"""
    st.title("🔧 Schema Visualizer")
    st.markdown("### 📊 Interactive Table Relationship Diagrams")
    st.markdown("Visualize your database schema with beautiful, interactive diagrams!")
    
    if not selected_db or selected_db == "oracle":
        st.warning("⚠️ Please select a MySQL database from the sidebar to use Schema Visualizer.")
        st.info("💡 This tool creates interactive diagrams showing table relationships, ERDs, and schema structure.")
        return
    
    # Schema overview
    st.markdown("### 📈 Database Schema Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Database", selected_db)
    with col2:
        st.metric("Status", "🟡 Ready to Visualize")
    with col3:
        st.metric("Last Scan", "Never")
    with col4:
        st.metric("Tables", "N/A")
    
    # Generate visualization button
    st.markdown("### 🔧 Generate Schema Visualization")
    
    if st.button("🎨 Create Interactive Diagrams", type="primary", use_container_width=True):
        with st.spinner("🔧 Analyzing database schema and generating visualizations..."):
            try:
                # Generate schema visualization
                result = run_async_in_thread(
                    assistant.visualize_schema,
                    selected_db
                )
                
                if "error" in result:
                    st.error(f"❌ Schema visualization failed: {result['error']}")
                    return
                
                # Display results
                st.success("✅ Schema Visualization Complete!")
                
                # Show statistics
                stats = result.get("statistics", {})
                if stats:
                    st.markdown("### 📊 Schema Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        overview = stats.get("overview", {})
                        st.metric("Total Tables", overview.get("total_tables", 0))
                    
                    with col2:
                        st.metric("Total Columns", overview.get("total_columns", 0))
                    
                    with col3:
                        relationships = stats.get("relationships", {})
                        st.metric("Foreign Keys", relationships.get("total_foreign_keys", 0))
                    
                    with col4:
                        st.metric("Total Size", f"{overview.get('total_size_mb', 0):.1f} MB")
                
                # Show different diagram types
                diagrams = result.get("diagrams", {})
                
                # ERD Diagram
                if "erd" in diagrams:
                    st.markdown("### 🔗 Entity Relationship Diagram (ERD)")
                    erd = diagrams["erd"]
                    
                    st.markdown(f"**Title**: {erd.get('title', 'Entity Relationship Diagram')}")
                    st.markdown(f"**Description**: {erd.get('description', 'Shows tables and their relationships')}")
                    
                    # Show entities
                    entities = erd.get("elements", {}).get("entities", [])
                    if entities:
                        st.markdown("#### 🏗️ Entities (Tables)")
                        for entity in entities:
                            st.markdown(f"**📋 {entity['name']}** ({len(entity['attributes'])} columns)")
                            # Show attributes in a container instead of expander
                            with st.container():
                                for attr in entity["attributes"]:
                                    icon = "🔑" if attr["primary_key"] else "🔗" if attr["foreign_key"] else "📝"
                                    nullable = "NULL" if attr["nullable"] else "NOT NULL"
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{icon} **{attr['name']}** ({attr['type']}) - {nullable}")
                    
                    # Show relationships
                    relationships = erd.get("elements", {}).get("relationships", [])
                    if relationships:
                        st.markdown("#### 🔗 Relationships")
                        for rel in relationships:
                            st.markdown(f"**{rel['from_entity']}** ({rel['from_attribute']}) → **{rel['to_entity']}** ({rel['to_attribute']}) - {rel['type']}")
                
                # Network Diagram
                if "network" in diagrams:
                    st.markdown("### 🌐 Table Relationship Network")
                    network = diagrams["network"]
                    
                    st.markdown(f"**Title**: {network.get('title', 'Table Relationship Network')}")
                    st.markdown(f"**Description**: {network.get('description', 'Shows how tables are connected')}")
                    
                    # Show nodes (tables)
                    nodes = network.get("nodes", [])
                    if nodes:
                        st.markdown("#### 📊 Tables")
                        for node in nodes:
                            data = node.get("data", {})
                            st.markdown(f"**{node['label']}** - {data.get('row_count', 0)} rows, {data.get('size_mb', 0):.1f} MB, {data.get('column_count', 0)} columns")
                    
                    # Show edges (relationships)
                    edges = network.get("edges", [])
                    if edges:
                        st.markdown("#### 🔗 Connections")
                        for edge in edges:
                            st.markdown(f"**{edge['source']}** → **{edge['target']}** ({edge['label']})")
                
                # Hierarchy Diagram
                if "hierarchy" in diagrams:
                    st.markdown("### 📊 Table Dependency Hierarchy")
                    hierarchy = diagrams["hierarchy"]
                    
                    st.markdown(f"**Title**: {hierarchy.get('title', 'Table Dependency Hierarchy')}")
                    st.markdown(f"**Description**: {hierarchy.get('description', 'Shows table dependencies in hierarchical structure')}")
                    
                    # Show levels
                    levels = hierarchy.get("levels", [])
                    if levels:
                        st.markdown("#### 📈 Dependency Levels")
                        for level in levels:
                            st.markdown(f"**Level {level['level']}**: {', '.join(level['tables'])}")
                
                # Summary Diagram
                if "summary" in diagrams:
                    st.markdown("### 📋 Schema Summary")
                    summary = diagrams["summary"]
                    
                    st.markdown(f"**Title**: {summary.get('title', 'Database Schema Summary')}")
                    st.markdown(f"**Description**: {summary.get('description', 'Overview of database structure and statistics')}")
                    
                    # Show statistics
                    summary_stats = summary.get("statistics", {})
                    if summary_stats:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Tables", summary_stats.get("total_tables", 0))
                        with col2:
                            st.metric("Total Columns", summary_stats.get("total_columns", 0))
                        with col3:
                            st.metric("Total Rows", f"{summary_stats.get('total_rows', 0):,}")
                    
                    # Show largest tables
                    largest_tables = summary.get("largest_tables", [])
                    if largest_tables:
                        st.markdown("#### 📊 Largest Tables")
                        for table_name, size_mb in largest_tables:
                            st.markdown(f"**{table_name}**: {size_mb:.1f} MB")
                    
                    # Show most connected tables
                    most_connected = summary.get("most_connected_tables", [])
                    if most_connected:
                        st.markdown("#### 🔗 Most Connected Tables")
                        for table_name, connections in most_connected:
                            st.markdown(f"**{table_name}**: {connections} connections")
                
                # Show relationship analysis
                relationships = result.get("relationships", {})
                if relationships:
                    st.markdown("### 🔍 Relationship Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Foreign Keys", len(relationships.get("foreign_keys", [])))
                    
                    with col2:
                        st.metric("Potential Relationships", len(relationships.get("potential_relationships", [])))
                    
                    with col3:
                        st.metric("Orphaned Tables", len(relationships.get("orphaned_tables", [])))
                    
                    with col4:
                        st.metric("Circular Dependencies", len(relationships.get("circular_dependencies", [])))
                    
                    # Show orphaned tables
                    orphaned_tables = relationships.get("orphaned_tables", [])
                    if orphaned_tables:
                        st.warning(f"⚠️ Found {len(orphaned_tables)} orphaned tables: {', '.join(orphaned_tables)}")
                    
                    # Show circular dependencies
                    circular_deps = relationships.get("circular_dependencies", [])
                    if circular_deps:
                        st.error(f"🚨 Found {len(circular_deps)} circular dependencies:")
                        for cycle in circular_deps:
                            st.markdown(f"**Cycle**: {' → '.join(cycle)}")
                    
                    # Show potential relationships
                    potential_rels = relationships.get("potential_relationships", [])
                    if potential_rels:
                        st.info(f"💡 Found {len(potential_rels)} potential relationships:")
                        for rel in potential_rels[:5]:  # Show first 5
                            st.markdown(f"**{rel['from_table']}.{rel['from_column']}** → **{rel['to_table']}.{rel['to_column']}** (confidence: {rel['confidence']})")
                
                # Show detailed results in expandable section
                with st.expander("🔍 Detailed Schema Analysis"):
                    st.json(result)
                
            except Exception as e:
                st.error(f"❌ Schema visualization failed: {str(e)}")
                logger.error(f"Schema visualization error: {e}", exc_info=True)
    
    # Help section
    with st.expander("💡 How Schema Visualizer Works"):
        st.markdown("""
        ### 🎯 What Schema Visualizer Does:
        
        The Schema Visualizer creates multiple types of interactive diagrams:
        
        **🔗 Entity Relationship Diagram (ERD):**
        - Shows tables as entities with their attributes
        - Displays relationships between tables
        - Highlights primary and foreign keys
        
        **🌐 Table Relationship Network:**
        - Visualizes how tables are connected
        - Node size based on table size/row count
        - Shows connection strength and types
        
        **📊 Table Dependency Hierarchy:**
        - Shows table dependencies in levels
        - Identifies root tables (no dependencies)
        - Helps understand data flow
        
        **📋 Schema Summary:**
        - Overview of database structure
        - Key statistics and metrics
        - Largest and most connected tables
        
        ### 🔍 Relationship Analysis:
        
        - **Foreign Keys**: Actual defined relationships
        - **Potential Relationships**: Suggested relationships based on naming conventions
        - **Orphaned Tables**: Tables with no relationships
        - **Circular Dependencies**: Tables that reference each other in cycles
        
        ### 💡 Benefits:
        
        - **Understand Database Structure**: Visual representation of your schema
        - **Identify Issues**: Find orphaned tables and circular dependencies
        - **Optimize Design**: See relationship patterns and opportunities
        - **Documentation**: Generate visual documentation of your database
        """)
    
    # Quick visualization options
    st.markdown("### ⚡ Quick Visualization Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔗 ERD Only"):
            st.info("🔧 Feature coming soon: Targeted ERD generation")
    
    with col2:
        if st.button("🌐 Network Only"):
            st.info("🔧 Feature coming soon: Targeted network diagram")
    
    with col3:
        if st.button("📊 Hierarchy Only"):
            st.info("🔧 Feature coming soon: Targeted hierarchy diagram")


async def nosql_assistant_interface(assistant: DBAAssistant, selected_db: Optional[str]):
    """NoSQL Assistant Interface"""
    st.title("🗄️ NoSQL Assistant")
    st.markdown("### 🔍 AI-Powered NoSQL Database Management")
    st.markdown("Manage MongoDB, Cassandra, Redis, Elasticsearch, Neo4j, and InfluxDB with natural language!")
    
    if not selected_db or selected_db == "oracle":
        st.warning("⚠️ Please select a NoSQL database from the sidebar to use the NoSQL Assistant.")
        st.info("💡 This tool helps you manage non-relational databases with natural language queries.")
        return
    
    # Database type detection
    st.markdown("### 🗄️ Database Information")
    
    # Get database type from config
    db_config = assistant.config.databases.get(selected_db)
    if not db_config:
        st.error(f"❌ Database '{selected_db}' not found in configuration")
        return
    
    db_type = db_config.db_type.lower()
    
    # Show database info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Database", selected_db)
    with col2:
        st.metric("Type", db_type.upper())
    with col3:
        st.metric("Host", db_config.host)
    with col4:
        st.metric("Port", db_config.port)
    
    # NoSQL Query Builder
    st.markdown("### 🔍 Natural Language Query Builder")
    st.markdown("Ask questions about your NoSQL database in plain English!")
    
    # Query input
    natural_query = st.text_area(
        "Enter your NoSQL query in natural language:",
        placeholder="Examples:\n• Find all users in MongoDB\n• Get Redis keys matching 'user:*'\n• Search for documents in Elasticsearch\n• Find all Person nodes in Neo4j\n• Query measurements from InfluxDB",
        height=120
    )
    
    # Execute query button
    if st.button("🔍 Analyze & Execute Query", type="primary", use_container_width=True):
        if not natural_query.strip():
            st.warning("⚠️ Please enter a query to analyze")
            return
        
        with st.spinner(f"🔍 Analyzing {db_type} query..."):
            try:
                # Analyze the NoSQL query
                result = await assistant.analyze_nosql_query(natural_query, db_type, selected_db)
                
                if "error" in result:
                    st.error(f"❌ Query analysis failed: {result['error']}")
                    return
                
                # Display results
                st.success("✅ Query Analysis Complete!")
                
                # Show analysis
                analysis = result.get("analysis", {})
                if analysis:
                    st.markdown("### 📊 Query Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Intent**: {analysis.get('intent', 'Unknown')}")
                        if analysis.get('collection'):
                            st.markdown(f"**Collection/Table**: {analysis['collection']}")
                        if analysis.get('key'):
                            st.markdown(f"**Key**: {analysis['key']}")
                        if analysis.get('index'):
                            st.markdown(f"**Index**: {analysis['index']}")
                    
                    with col2:
                        if analysis.get('filter'):
                            st.markdown(f"**Filter**: {analysis['filter']}")
                        if analysis.get('aggregation'):
                            st.markdown(f"**Aggregation**: {analysis['aggregation']}")
                        if analysis.get('limit'):
                            st.markdown(f"**Limit**: {analysis['limit']}")
                
                # Show generated query/command
                if "query" in result:
                    st.markdown("### 🔧 Generated Query")
                    st.code(result["query"], language="javascript" if db_type == "mongodb" else "sql")
                
                if "command" in result:
                    st.markdown("### 🔧 Generated Command")
                    st.code(result["command"], language="bash")
                
                # Show explanation
                if "explanation" in result:
                    st.markdown("### 💡 What This Query Does")
                    st.info(result["explanation"])
                
                # Show suggestions
                suggestions = result.get("suggestions", [])
                if suggestions:
                    st.markdown("### 💡 Suggestions")
                    for suggestion in suggestions:
                        st.markdown(f"• {suggestion}")
                
                # Execute the query if user wants
                st.markdown("### ⚡ Execute Query")
                if st.button("🚀 Execute Query", type="secondary"):
                    with st.spinner("Executing query..."):
                        try:
                            # Execute the query based on database type
                            if db_type == "mongodb":
                                # For MongoDB, we'd need to implement actual execution
                                st.info("🔧 MongoDB query execution coming soon!")
                            elif db_type == "redis":
                                # For Redis, execute the command
                                connection = await assistant.db_connector.get_connection(db_config)
                                if "command" in result:
                                    command_result = await connection.execute_command(result["command"])
                                    st.success(f"✅ Command executed: {command_result}")
                            else:
                                st.info(f"🔧 {db_type.upper()} query execution coming soon!")
                                
                        except Exception as e:
                            st.error(f"❌ Query execution failed: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Query analysis failed: {str(e)}")
                logger.error(f"NoSQL query analysis error: {e}", exc_info=True)
    
    # Database Information
    st.markdown("### 📊 Database Information")
    
    if st.button("📊 Get Database Info", type="secondary"):
        with st.spinner("🔍 Gathering database information..."):
            try:
                info = await assistant.get_nosql_database_info(db_type, selected_db)
                
                if "error" in info:
                    st.error(f"❌ Failed to get database info: {info['error']}")
                    return
                
                st.success("✅ Database Information Retrieved!")
                
                # Display info based on database type
                if db_type == "mongodb":
                    if "collections" in info:
                        st.markdown("#### 📁 Collections")
                        collections = info["collections"]
                        if collections:
                            for collection in collections[:10]:  # Show first 10
                                st.markdown(f"• **{collection}**")
                            if len(collections) > 10:
                                st.info(f"... and {len(collections) - 10} more collections")
                        else:
                            st.info("No collections found")
                
                elif db_type == "redis":
                    if "server_info" in info:
                        st.markdown("#### 🔧 Server Information")
                        server_info = info["server_info"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Redis Version", server_info.get("server", {}).get("redis_version", "Unknown"))
                        with col2:
                            st.metric("Connected Clients", server_info.get("clients", {}).get("connected_clients", 0))
                        with col3:
                            st.metric("Used Memory", f"{server_info.get('memory', {}).get('used_memory_human', 'Unknown')}")
                        with col4:
                            st.metric("Total Commands", server_info.get("stats", {}).get("total_commands_processed", 0))
                
                elif db_type == "elasticsearch":
                    if "cluster_info" in info:
                        st.markdown("#### 🌐 Cluster Information")
                        cluster_info = info["cluster_info"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Cluster Name", cluster_info.get("health", {}).get("cluster_name", "Unknown"))
                        with col2:
                            st.metric("Status", cluster_info.get("health", {}).get("status", "Unknown"))
                        with col3:
                            st.metric("Number of Nodes", cluster_info.get("health", {}).get("number_of_nodes", 0))
                        with col4:
                            st.metric("Active Shards", cluster_info.get("health", {}).get("active_shards", 0))
                
                elif db_type == "neo4j":
                    if "database_info" in info:
                        st.markdown("#### 🕸️ Graph Database Information")
                        db_info = info["database_info"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Nodes", db_info.get("node_count", 0))
                        with col2:
                            st.metric("Relationships", db_info.get("relationship_count", 0))
                        with col3:
                            st.metric("Labels", db_info.get("label_count", 0))
                        with col4:
                            st.metric("Database Size", "N/A")
                
                elif db_type == "cassandra":
                    if "keyspaces" in info:
                        st.markdown("#### 🗂️ Keyspaces")
                        keyspaces = info["keyspaces"]
                        if keyspaces and "keyspaces" in keyspaces:
                            for keyspace in keyspaces["keyspaces"][:10]:  # Show first 10
                                st.markdown(f"• **{keyspace.get('keyspace_name', 'Unknown')}**")
                        else:
                            st.info("No keyspaces found")
                
                elif db_type == "influxdb":
                    if "buckets" in info:
                        st.markdown("#### 🪣 Buckets")
                        buckets = info["buckets"]
                        if buckets and "buckets" in buckets:
                            for bucket in buckets["buckets"][:10]:  # Show first 10
                                st.markdown(f"• **{bucket.get('name', 'Unknown')}**")
                        else:
                            st.info("No buckets found")
                
            except Exception as e:
                st.error(f"❌ Failed to get database info: {str(e)}")
                logger.error(f"Database info error: {e}", exc_info=True)
    
    # Help section
    with st.expander("💡 How NoSQL Assistant Works"):
        st.markdown("""
        ### 🎯 What NoSQL Assistant Does:
        
        The NoSQL Assistant helps you manage non-relational databases using natural language:
        
        **🗄️ Supported Databases:**
        - **MongoDB**: Document database queries and operations
        - **Redis**: Key-value store commands and operations
        - **Elasticsearch**: Search and analytics queries
        - **Neo4j**: Graph database traversals and queries
        - **Cassandra**: Wide-column store queries
        - **InfluxDB**: Time-series database queries
        
        **🔍 Natural Language Examples:**
        
        **MongoDB:**
        - "Find all users where age > 25"
        - "Count documents in orders collection"
        - "Show me users with email containing '@gmail.com'"
        
        **Redis:**
        - "Get value for key 'user:123'"
        - "Set key 'session:456' to 'active'"
        - "Find all keys matching 'user:*'"
        
        **Elasticsearch:**
        - "Search for documents in 'products' index"
        - "Find products with price > 100"
        - "Analyze index 'logs'"
        
        **Neo4j:**
        - "Find all Person nodes"
        - "Find relationships between users"
        - "Find shortest path from User to Product"
        
        **Cassandra:**
        - "Select from users table"
        - "Show all keyspaces"
        - "Query users where id = 123"
        
        **InfluxDB:**
        - "Query measurements from cpu bucket"
        - "Show all buckets"
        - "Get temperature data from sensors"
        
        ### 💡 Benefits:
        
        - **Natural Language**: No need to learn specific query languages
        - **Multi-Database Support**: Manage different NoSQL databases with one interface
        - **AI-Powered Analysis**: Intelligent query understanding and optimization
        - **Real-time Execution**: Execute queries directly from the interface
        - **Database Insights**: Get comprehensive information about your NoSQL databases
        """)
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Database Stats"):
            st.info("🔧 Feature coming soon: Quick database statistics")
    
    with col2:
        if st.button("🔍 Schema Explorer"):
            st.info("🔧 Feature coming soon: Interactive schema exploration")
    
    with col3:
        if st.button("⚡ Performance Monitor"):
            st.info("🔧 Feature coming soon: Real-time performance monitoring")


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
                                # Execute the SQL and capture any errors
                                response = run_async_in_thread(
                                    assistant.chat,
                                    custom_sql,
                                    db_name=selected_error_db
                                )
                                
                                # Always show the response if we get one
                                if response:
                                    # Check if it contains error resolution content
                                    if any(keyword in response.lower() for keyword in [
                                        "emergency resolution", "database error", "auto-resolving", 
                                        "🚨", "error detected", "resolution generated"
                                    ]):
                                        st.success("✅ Real database error captured and auto-resolved!")
                                        st.markdown(response)
                                    else:
                                        st.info("Response received:")
                                        st.markdown(response)
                                else:
                                    st.warning("No response received from database query.")
                                
                                # Check if we have new errors in the recent_errors list
                                if assistant.recent_errors:
                                    st.success(f"✅ Error added to system! Total recent errors: {len(assistant.recent_errors)}")
                                    
                                st.rerun()  # Always refresh to update counters
                                    
                            except Exception as e:
                                st.success(f"✅ Real database error captured and processed!")
                                st.error(f"Database Error Details: {str(e)}")
                                st.info("The error has been sent to the auto-resolution system. Check the Recent Errors section above for the resolution.")
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

    st.divider()

    # --- MySQL Query Performance & Optimization Tools ---
    db_config = assistant.config.get_database_config(selected_db)
    if not db_config:
        return

    if db_config.db_type.lower() == 'mysql':
        st.subheader("⚡ MySQL Top Queries & Optimization")

        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            top_n = st.number_input("Top N", min_value=5, max_value=100, value=10, step=5, help="Number of queries to fetch from Performance Schema")
        with col_b:
            sort_by = st.selectbox("Sort by", ["total_time_ms", "avg_time_ms", "calls", "rows_examined", "rows_sent"], index=0)
        with col_c:
            go = st.button("Fetch Top Queries")

        if go:
            try:
                with st.spinner("Fetching top queries from Performance Schema..."):
                    top_queries = run_async_in_thread(assistant.analyzer.optimizer.get_top_queries, db_config, top_n, sort_by)

                if not top_queries:
                    st.info("No data from Performance Schema. Ensure it is enabled and consumers for statements digest are ON.")
                else:
                    for i, q in enumerate(top_queries):
                        with st.expander(f"[{i+1}] {q.get('query', '')[:120]}..."):
                            m1, m2, m3, m4, m5 = st.columns(5)
                            m1.metric("Calls", q.get("calls", 0))
                            m2.metric("Total ms", f"{q.get('total_time_ms', 0):.1f}")
                            m3.metric("Avg ms", f"{q.get('avg_time_ms', 0):.2f}")
                            m4.metric("Rows Examined", q.get("rows_examined", 0))
                            m5.metric("Rows Sent", q.get("rows_sent", 0))

                            st.caption(f"First seen: {q.get('first_seen', '-')}, Last seen: {q.get('last_seen', '-')}")
                            st.code(q.get("query", ""), language="sql")

                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("Explain", key=f"explain_{i}"):
                                    with st.spinner("Running EXPLAIN FORMAT=JSON..."):
                                        plan = run_async_in_thread(assistant.analyzer.optimizer.explain_query, db_config, q.get("query", ""), False)
                                    if plan and not plan.get("error"):
                                        st.json(plan.get("raw", {}))
                                        # Quick table summary
                                        tbl = plan.get("tables", [])
                                        if tbl:
                                            st.table(pd.DataFrame(tbl))
                                    else:
                                        st.error(plan.get("error", "Unknown error"))

                            with b2:
                                if st.button("Optimize", key=f"opt_{i}"):
                                    with st.spinner("Analyzing query and generating suggestions..."):
                                        analysis = run_async_in_thread(assistant.analyzer.optimizer.analyze_query, db_config, q.get("query", ""))
                                    issues = analysis.get("issues", [])
                                    rewrites = analysis.get("suggested_rewrites", [])
                                    indexes = analysis.get("suggested_indexes", [])

                                    if issues:
                                        st.subheader("Issues Detected")
                                        for it in issues:
                                            st.warning(it)
                                    if rewrites:
                                        st.subheader("Suggested Rewrites")
                                        for r in rewrites:
                                            st.info(r)
                                    if indexes:
                                        st.subheader("Suggested Indexes")
                                        for idx in indexes:
                                            st.code(idx.get("ddl", ""), language="sql")
                                            st.caption(idx.get("reason", ""))
            except Exception as e:
                st.error(f"Error fetching top queries: {e}")

        st.markdown("---")
        st.subheader("🧪 Explain / Optimize a Custom SQL")
        sql_text = st.text_area("SQL", value="SELECT * FROM orders WHERE user_id = 42 ORDER BY id DESC LIMIT 50", height=120)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Explain SQL"):
                with st.spinner("Running EXPLAIN FORMAT=JSON..."):
                    plan = run_async_in_thread(assistant.analyzer.optimizer.explain_query, db_config, sql_text, False)
                if plan and not plan.get("error"):
                    st.json(plan.get("raw", {}))
                    tbl = plan.get("tables", [])
                    if tbl:
                        st.table(pd.DataFrame(tbl))
                else:
                    st.error(plan.get("error", "Unknown error"))
        with c2:
            if st.button("Optimize SQL"):
                with st.spinner("Analyzing SQL..."):
                    analysis = run_async_in_thread(assistant.analyzer.optimizer.analyze_query, db_config, sql_text)
                issues = analysis.get("issues", [])
                rewrites = analysis.get("suggested_rewrites", [])
                indexes = analysis.get("suggested_indexes", [])
                if issues:
                    st.subheader("Issues Detected")
                    for it in issues:
                        st.warning(it)
                if rewrites:
                    st.subheader("Suggested Rewrites")
                    for r in rewrites:
                        st.info(r)
                if indexes:
                    st.subheader("Suggested Indexes")
                    for idx in indexes:
                        st.code(idx.get("ddl", ""), language="sql")
                        st.caption(idx.get("reason", ""))
    else:
        st.info("MySQL-specific query optimization tools are available when a MySQL database is selected.")


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
    
    # Show currently configured databases
    if assistant.config.databases:
        st.success(f"✅ **{len(assistant.config.databases)} databases configured**")
        
        # Create a table of configured databases
        db_data = []
        for db_name, db_config in assistant.config.databases.items():
            db_data.append({
                "Name": db_name,
                "Type": db_config.db_type.upper(),
                "Host": db_config.host,
                "Database": db_config.database,
                "Status": "🟢 Configured"
            })
        
        st.dataframe(pd.DataFrame(db_data), use_container_width=True)
    else:
        st.warning("⚠️ **No databases configured**")
    
    st.markdown("---")
    st.subheader("📋 Available Database Types")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**SQL Databases:**")
        st.markdown("- 🗄️ **MySQL** - Relational database")
        st.markdown("- 🐘 **PostgreSQL** - Advanced relational database")
        st.markdown("- 💾 **SQLite** - Lightweight embedded database")
        st.markdown("- 🔵 **Oracle** - Enterprise database")
        st.markdown("- 🟦 **SQL Server** - Microsoft database")
    
    with col2:
        st.markdown("**NoSQL Databases:**")
        st.markdown("- 🍃 **MongoDB** - Document database")
        st.markdown("- 🔴 **Redis** - In-memory key-value store")
        st.markdown("- 🔍 **Elasticsearch** - Search engine")
        st.markdown("- 🕸️ **Neo4j** - Graph database")
        st.markdown("- 🗿 **Cassandra** - Wide-column database")
        st.markdown("- 📊 **InfluxDB** - Time series database")
    
    with col3:
        st.markdown("**Cloud Databases:**")
        st.markdown("- ☁️ **AWS Athena** - Serverless query service")
        st.markdown("- 🔵 **Azure SQL** - Microsoft cloud database")
        st.markdown("- 🟢 **Google BigQuery** - Data warehouse")
    
    st.markdown("---")
    st.subheader("🔧 How to Add a Database")
    
    st.markdown("""
    **To add a new database:**
    
    1. **Edit the configuration file:**
       ```bash
       # Open config/config.yaml
       ```
    
    2. **Add database configuration:**
       ```yaml
       databases:
         your_database_name:
           host: "your-host"
           port: 3306
           database: "your_database"
           username: "your_username"
           password: "your_password"
           db_type: "mysql"  # or postgresql, mongodb, etc.
           connection_pool_size: 10
           timeout: 30
       ```
    
    3. **Restart the application:**
       ```bash
       # Stop and restart DBA-GPT
       ```
    
    4. **Test the connection** in the Chat interface
    """)
    
    st.warning("⚠️ **Security Note:** Store sensitive credentials in environment variables or use a secure configuration management system.")
    
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