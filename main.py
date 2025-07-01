#!/usr/bin/env python3
"""
DBA-GPT: Generative AI Agent for Proactive Database Administration
Main entry point for the DBA-GPT system
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.ai.dba_assistant import DBAAssistant
from core.monitoring.monitor import DatabaseMonitor
from core.web.api import start_api_server
from core.web.interface import start_web_interface
from core.utils.logger import setup_logger
from core.utils.cli import CLIInterface

logger = setup_logger(__name__)


class DBAGPT:
    """Main DBA-GPT system class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize DBA-GPT system"""
        self.config = Config(config_path)
        self.assistant = DBAAssistant(self.config)
        self.monitor = DatabaseMonitor(self.config)
        self.cli = CLIInterface(self.assistant)
        
    async def start_monitoring(self):
        """Start proactive database monitoring"""
        logger.info("Starting DBA-GPT monitoring system...")
        await self.monitor.start()
        
    async def start_api(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server"""
        logger.info(f"Starting DBA-GPT API server on {host}:{port}")
        await start_api_server(self.assistant, host, port)
        
    def start_web_interface(self, port: int = 8501):
        """Start the web interface"""
        logger.info(f"Starting DBA-GPT web interface on port {port}")
        # We need to run streamlit from the command line
        # This function will now be a placeholder
        pass
        
    async def start_cli(self):
        """Start the command-line interface"""
        logger.info("Starting DBA-GPT CLI interface")
        await self.cli.run()


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DBA-GPT: AI-Powered Database Administration")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--mode", "-m", choices=["cli", "api", "web", "monitor", "all"], 
                       default="cli", help="Run mode")
    parser.add_argument("--host", default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--web-port", type=int, default=8501, help="Web interface port")
    
    args = parser.parse_args()
    
    try:
        # Initialize DBA-GPT
        dbagpt = DBAGPT(args.config)
        
        if args.mode == "cli":
            await dbagpt.start_cli()
        elif args.mode == "api":
            await dbagpt.start_api(args.host, args.port)
        elif args.mode == "web":
            # We need to construct and run the streamlit command
            logger.info("Starting web interface via Streamlit...")
            script_path = Path(__file__).parent / "core" / "web" / "interface.py"
            cmd = [
                sys.executable, "-m", "streamlit", "run", str(script_path),
                "--server.port", str(args.web_port),
                "--",
                "--config", str(dbagpt.config.config_path)
            ]
            subprocess.Popen(cmd)
            # Keep the main process alive
            await asyncio.Event().wait()
        elif args.mode == "monitor":
            await dbagpt.start_monitoring()
        elif args.mode == "all":
            # Start all services
            tasks = [
                dbagpt.start_monitoring(),
                dbagpt.start_api(args.host, args.port)
            ]
            await asyncio.gather(*tasks)
            
    except KeyboardInterrupt:
        logger.info("DBA-GPT shutdown requested")
    except Exception as e:
        logger.error(f"Error starting DBA-GPT: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # On Windows, the default event loop (ProactorEventLoop) can have issues
    # with some libraries. However, the Selector loop we tried earlier caused
    # input blocking. We'll remove the explicit policy setting and let Python
    # use its default, which is generally more compatible for modern apps.
    if os.name == 'nt' and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main()) 