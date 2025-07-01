"""
Command-line interface for DBA-GPT
"""

import asyncio
import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markup import escape

from core.ai.dba_assistant import DBAAssistant
from core.utils.logger import setup_logger

logger = setup_logger(__name__)
console = Console()

async def ainput(prompt: str = "") -> str:
    """Async version of input()"""
    return await asyncio.to_thread(input, prompt)


class CLIInterface:
    """Command-line interface for DBA-GPT"""
    
    def __init__(self, assistant: DBAAssistant):
        """Initialize CLI interface"""
        self.assistant = assistant
        self.conversation_history = []
        
    async def run(self):
        """Run the CLI interface"""
        console.print(Panel.fit(
            "[bold blue]DBA-GPT[/bold blue] - AI-Powered Database Administration\n"
            "Type 'help' for commands, 'quit' to exit",
            border_style="blue"
        ))
        
        while True:
            try:
                # Get user input
                user_input = await ainput("\nDBA-GPT: ")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.lower() == 'status':
                    self._show_status()
                elif user_input.lower() == 'databases':
                    self._show_databases()
                elif user_input.lower() == 'tips':
                    await self._show_tips()
                elif user_input.lower().startswith('analyze'):
                    await self._analyze_database(user_input)
                elif user_input.lower().startswith('report'):
                    await self._generate_report(user_input)
                else:
                    # Treat as a question for the AI assistant
                    await self._handle_question(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                console.print(f"Error: {e}", style="bold red")
                
    def _show_help(self):
        """Show help information"""
        help_text = """
[bold]Available Commands:[/bold]

[green]help[/green] - Show this help message
[green]status[/green] - Show system status
[green]databases[/green] - List configured databases
[green]tips[/green] - Show DBA tips
[green]analyze <database>[/green] - Analyze specific database
[green]report <database>[/green] - Generate performance report
[green]quit[/green] - Exit DBA-GPT

[bold]Examples:[/bold]
• "My PostgreSQL database is running slow"
• "How do I optimize MySQL performance?"
• "What should I check for database security?"
• "analyze postgresql"
• "report mysql"
        """
        console.print(Panel(help_text, title="[bold blue]DBA-GPT Help[/bold blue]"))
        
    def _show_status(self):
        """Show system status"""
        try:
            # This would typically get status from the monitoring system
            status_table = Table(title="DBA-GPT System Status")
            status_table.add_column("Component", style="cyan")
            status_table.add_column("Status", style="green")
            status_table.add_column("Details", style="white")
            
            status_table.add_row("AI Assistant", "✅ Active", "Ready to answer questions")
            status_table.add_row("Database Monitoring", "✅ Active", "Monitoring configured databases")
            status_table.add_row("Auto-Remediation", "✅ Active", "Automatic issue resolution enabled")
            
            console.print(status_table)
            
        except Exception as e:
            console.print(f"Error getting status: {e}", style="bold red")
            
    def _show_databases(self):
        """Show configured databases"""
        try:
            db_table = Table(title="Configured Databases")
            db_table.add_column("Name", style="cyan")
            db_table.add_column("Type", style="green")
            db_table.add_column("Host", style="white")
            db_table.add_column("Database", style="white")
            
            for db_name, db_config in self.assistant.config.databases.items():
                db_table.add_row(
                    db_name,
                    db_config.db_type,
                    f"{db_config.host}:{db_config.port}",
                    db_config.database
                )
                
            console.print(db_table)
            
        except Exception as e:
            console.print(f"Error getting databases: {e}", style="bold red")
            
    async def _show_tips(self):
        """Show DBA tips"""
        try:
            tips = await self.assistant.get_quick_tips()
            
            tips_text = "\n".join([f"• {tip}" for tip in tips])
            console.print(Panel(tips_text, title="[bold blue]DBA Tips[/bold blue]"))
            
        except Exception as e:
            console.print(f"Error getting tips: {e}", style="bold red")
            
    async def _analyze_database(self, command: str):
        """Analyze a specific database"""
        try:
            parts = command.split()
            if len(parts) < 2:
                console.print("[red]Usage: analyze <database_name>[/red]")
                return
                
            db_name = parts[1]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing database...", total=None)
                
                # This would typically call the monitoring system
                console.print(f"[yellow]Analysis for {db_name} would be performed here[/yellow]")
                
        except Exception as e:
            console.print(f"Error analyzing database: {e}", style="bold red")
            
    async def _generate_report(self, command: str):
        """Generate a performance report"""
        try:
            parts = command.split()
            if len(parts) < 2:
                console.print("[red]Usage: report <database_name>[/red]")
                return
                
            db_name = parts[1]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating report...", total=None)
                
                # This would typically call the analyzer
                console.print(f"[yellow]Performance report for {db_name} would be generated here[/yellow]")
                
        except Exception as e:
            console.print(f"Error generating report: {e}", style="bold red")
            
    async def _handle_question(self, question: str):
        """Handle user questions with AI assistant"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Thinking...", total=None)
                
                # Get AI recommendation
                recommendation = await self.assistant.get_recommendation(question)
                
                # Display the response
                self._display_recommendation(recommendation)
                
                # Store in conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": question
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": recommendation.description
                })
                
        except Exception as e:
            console.print(f"Error processing question: {e}", style="bold red")
            
    def _display_recommendation(self, recommendation):
        """Display AI recommendation in a formatted way"""
        
        severity_color = self._get_severity_color(recommendation.severity)
        
        # Create a Rich Text object for the content
        text = Text()
        text.append("Issue: ", style="bold")
        text.append(escape(recommendation.issue) + "\n")
        text.append("Severity: ", style="bold")
        text.append(escape(recommendation.severity) + "\n", style=severity_color)
        text.append("Category: ", style="bold")
        text.append(escape(recommendation.category) + "\n\n")
        
        text.append("Description:\n", style="bold")
        text.append(escape(recommendation.description) + "\n\n")
        
        text.append("Solution:\n", style="bold")
        text.append(escape(recommendation.solution) + "\n\n")
        
        text.append("Estimated Impact: ", style="bold")
        text.append(escape(recommendation.estimated_impact) + "\n")
        text.append("Risk Level: ", style="bold")
        text.append(escape(recommendation.risk_level) + "\n")

        if recommendation.sql_commands:
            text.append("\nSQL Commands:\n", style="bold")
            for i, cmd in enumerate(recommendation.sql_commands, 1):
                text.append(f"{i}. ", style="bold")
                text.append(escape(cmd) + "\n")

        console.print(Panel(
            text,
            title="[bold blue]DBA-GPT Recommendation[/bold blue]",
            border_style=severity_color
        ))
        
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        colors = {
            "critical": "red",
            "high": "bright_yellow",
            "medium": "yellow",
            "low": "green"
        }
        return colors.get(severity.lower(), "white") 