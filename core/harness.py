"""
Harness - The Core Agent Logic

The Harness acts as an extension of the Fulcrum's (human's) intelligence.
It loads context on instantiation, executes tasks with LLM assistance,
validates outputs against constraints, and logs Shadow Mode drafts for learning.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Load environment variables
load_dotenv()

# Rich console for pretty output
console = Console()


class HarnessValidationError(Exception):
    """Raised when output validation fails."""
    pass


class Harness:
    """
    The Harness Agent - An extension of human intelligence.
    
    This class represents the core Harness logic that:
    1. Loads identity, directives, and knowledge on instantiation
    2. Combines context with tasks for LLM execution
    3. Validates outputs against prime directive constraints
    4. Logs all actions in Shadow Mode for the learning loop
    
    Attributes:
        context_path (Path): Path to the context directory
        logs_path (Path): Path to the logs directory
        identity (str): Contents of identity.md
        prime_directive (str): Contents of prime_directive.md
        knowledge_base (str): Contents of knowledge_base.md
        mode (str): Operating mode - 'shadow' or 'production'
    """
    
    def __init__(
        self,
        context_path: str = "context",
        logs_path: str = "logs",
        mode: str = "shadow"
    ):
        """
        Initialize the Harness by loading all context files.
        
        Args:
            context_path: Path to the directory containing context files
            logs_path: Path to the directory for storing logs
            mode: Operating mode - 'shadow' (default) or 'production'
        """
        self.context_path = Path(context_path)
        self.logs_path = Path(logs_path)
        self.mode = mode
        
        # Ensure logs directory exists
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Load context files immediately
        self._load_context()
        
        console.print(Panel(
            f"[bold green]Harness Initialized[/bold green]\n"
            f"Mode: [cyan]{self.mode.upper()}[/cyan]\n"
            f"Context loaded from: [dim]{self.context_path}[/dim]",
            title="🔧 Harness System",
            border_style="green"
        ))
    
    def _load_context(self) -> None:
        """Load all context files into memory."""
        self.identity = self._read_file(self.context_path / "identity.md")
        self.prime_directive = self._read_file(self.context_path / "prime_directive.md")
        self.knowledge_base = self._read_file(self.context_path / "knowledge_base.md")
        
        console.print("[dim]✓ Loaded identity.md[/dim]")
        console.print("[dim]✓ Loaded prime_directive.md[/dim]")
        console.print("[dim]✓ Loaded knowledge_base.md[/dim]")
    
    def _read_file(self, path: Path) -> str:
        """Read a file and return its contents."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {path} not found[/yellow]")
            return ""
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt from identity and prime directive."""
        return f"""You are an AI assistant operating as part of the Harness system.
You represent the Fulcrum (the human principal) and must act according to their identity and directives.

=== IDENTITY ===
{self.identity}

=== PRIME DIRECTIVE ===
{self.prime_directive}

=== OPERATIONAL RULES ===
1. You are in {self.mode.upper()} MODE
2. All outputs must be validated against the Prime Directive
3. Never fabricate facts or citations
4. Maintain transparency in your reasoning
5. When uncertain, acknowledge it explicitly
"""
    
    def _call_llm(self, messages: list[dict]) -> str:
        """
        Call the LLM API (OpenAI or Anthropic).
        
        This is a stub implementation. Replace with actual API calls.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            The LLM's response as a string
        """
        # Check for API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if openai_key:
            return self._call_openai(messages, openai_key)
        elif anthropic_key:
            return self._call_anthropic(messages, anthropic_key)
        else:
            # Stub response when no API key is configured
            console.print("[yellow]No API key configured. Returning stub response.[/yellow]")
            return self._stub_response(messages)
    
    def _call_openai(self, messages: list[dict], api_key: str) -> str:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]OpenAI API error: {e}[/red]")
            return self._stub_response(messages)
    
    def _call_anthropic(self, messages: list[dict], api_key: str) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # Extract system message
            system_msg = next(
                (m["content"] for m in messages if m["role"] == "system"),
                ""
            )
            user_messages = [m for m in messages if m["role"] != "system"]
            
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=2000,
                system=system_msg,
                messages=user_messages
            )
            return response.content[0].text
        except Exception as e:
            console.print(f"[red]Anthropic API error: {e}[/red]")
            return self._stub_response(messages)
    
    def _stub_response(self, messages: list[dict]) -> str:
        """Generate a stub response for testing without API keys."""
        user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "No user message found"
        )
        return f"""[STUB RESPONSE - No API Key Configured]

Task received: {user_msg[:200]}...

This is a placeholder response. To enable actual LLM calls:
1. Copy .env.example to .env
2. Add your OPENAI_API_KEY or ANTHROPIC_API_KEY
3. Restart the Harness

Operating in {self.mode.upper()} mode.
All outputs are being logged for review.
"""
    
    def run_task(
        self,
        task: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a task using the Harness system.
        
        This method:
        1. Combines the task with identity and prime directive
        2. Sends the combined prompt to the LLM
        3. Validates the output
        4. Logs the result (Shadow Mode) or returns it (Production)
        
        Args:
            task: The task description or prompt
            context: Additional context dict (e.g., case details)
            
        Returns:
            Dict containing the task result and metadata
        """
        console.print(Panel(
            f"[bold]Task:[/bold] {task[:100]}{'...' if len(task) > 100 else ''}",
            title="📋 Running Task",
            border_style="blue"
        ))
        
        # Build the context string
        context_str = ""
        if context:
            context_str = f"\n=== ADDITIONAL CONTEXT ===\n{json.dumps(context, indent=2)}"
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": f"{task}{context_str}"}
        ]
        
        # Call the LLM
        output = self._call_llm(messages)
        
        # Validate the output
        validation_result = self.validate_output(output)
        
        # Build result object
        result = {
            "task": task,
            "context": context,
            "output": output,
            "validation": validation_result,
            "mode": self.mode,
            "timestamp": datetime.now().isoformat(),
            "status": "SHADOW" if self.mode == "shadow" else "PENDING_REVIEW"
        }
        
        # In Shadow Mode, always log instead of returning directly
        if self.mode == "shadow":
            self.log_shadow_mode(task, result)
            console.print("[cyan]Output logged to Shadow Mode (not executed)[/cyan]")
        
        return result
    
    def validate_output(self, output: str) -> dict[str, Any]:
        """
        Validate the output against Prime Directive constraints.
        
        This method checks:
        1. No fabrication indicators
        2. Appropriate disclaimers present
        3. No unauthorized action language
        4. Confidence indicators
        
        Args:
            output: The LLM output to validate
            
        Returns:
            Dict with validation results and any warnings/errors
        """
        validation = {
            "passed": True,
            "checks": [],
            "warnings": [],
            "errors": []
        }
        
        # Check 1: No fabrication indicators
        fabrication_phrases = [
            "I believe the case was",
            "As far as I know",
            "I think the statute says",
        ]
        for phrase in fabrication_phrases:
            if phrase.lower() in output.lower():
                validation["warnings"].append(
                    f"Potential fabrication indicator: '{phrase}'"
                )
        validation["checks"].append("fabrication_check")
        
        # Check 2: No unauthorized action language
        action_phrases = [
            "I have sent",
            "I have filed",
            "I have submitted",
            "I have committed",
        ]
        for phrase in action_phrases:
            if phrase.lower() in output.lower():
                validation["errors"].append(
                    f"Unauthorized action language detected: '{phrase}'"
                )
                validation["passed"] = False
        validation["checks"].append("action_check")
        
        # Check 3: Uncertainty acknowledgment
        uncertainty_phrases = [
            "I'm not certain",
            "This requires verification",
            "Please confirm",
            "Subject to review",
        ]
        has_uncertainty = any(
            phrase.lower() in output.lower()
            for phrase in uncertainty_phrases
        )
        if not has_uncertainty and len(output) > 500:
            validation["warnings"].append(
                "Long output without uncertainty acknowledgment"
            )
        validation["checks"].append("uncertainty_check")
        
        # Check 4: HALT_HARNESS emergency stop
        if "HALT_HARNESS" in output:
            validation["errors"].append("Emergency stop triggered")
            validation["passed"] = False
        validation["checks"].append("emergency_stop_check")
        
        # Display validation results
        self._display_validation(validation)
        
        return validation
    
    def _display_validation(self, validation: dict) -> None:
        """Display validation results using Rich."""
        table = Table(title="Validation Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        
        for check in validation["checks"]:
            status = "✓ Passed"
            if any(check in str(e) for e in validation["errors"]):
                status = "[red]✗ Failed[/red]"
            elif any(check in str(w) for w in validation["warnings"]):
                status = "[yellow]⚠ Warning[/yellow]"
            table.add_row(check, status)
        
        console.print(table)
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                console.print(f"[yellow]⚠ {warning}[/yellow]")
        
        if validation["errors"]:
            for error in validation["errors"]:
                console.print(f"[red]✗ {error}[/red]")
    
    def log_shadow_mode(
        self,
        task: str,
        output: dict[str, Any]
    ) -> Path:
        """
        Log the task and output to Shadow Mode storage.
        
        This implements the Learning Loop - all outputs are saved
        for later review, learning, and trust calibration.
        
        Args:
            task: The original task
            output: The complete result dict
            
        Returns:
            Path to the created log file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_slug = "".join(c if c.isalnum() else "_" for c in task[:30])
        filename = f"shadow_{timestamp}_{task_slug}.json"
        
        log_path = self.logs_path / filename
        
        # Build log entry
        log_entry = {
            "id": f"shadow_{timestamp}",
            "timestamp": datetime.now().isoformat(),
            "mode": "shadow",
            "task": task,
            "result": output,
            "review_status": "PENDING",
            "reviewed_by": None,
            "review_notes": None
        }
        
        # Write to file
        log_path.write_text(
            json.dumps(log_entry, indent=2, default=str),
            encoding="utf-8"
        )
        
        console.print(f"[dim]📝 Logged to: {log_path}[/dim]")
        
        return log_path
    
    def get_shadow_logs(self, limit: int = 10) -> list[dict]:
        """
        Retrieve recent Shadow Mode logs for review.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries, most recent first
        """
        log_files = sorted(
            self.logs_path.glob("shadow_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        logs = []
        for log_file in log_files:
            try:
                logs.append(json.loads(log_file.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                console.print(f"[yellow]Warning: Could not parse {log_file}[/yellow]")
        
        return logs
    
    def approve_shadow_log(
        self,
        log_id: str,
        reviewed_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Approve a Shadow Mode log entry.
        
        Args:
            log_id: The ID of the log to approve
            reviewed_by: Name/ID of the reviewer
            notes: Optional review notes
            
        Returns:
            True if approval was successful
        """
        for log_file in self.logs_path.glob("shadow_*.json"):
            try:
                log_data = json.loads(log_file.read_text(encoding="utf-8"))
                if log_data.get("id") == log_id:
                    log_data["review_status"] = "APPROVED"
                    log_data["reviewed_by"] = reviewed_by
                    log_data["review_notes"] = notes
                    log_data["reviewed_at"] = datetime.now().isoformat()
                    
                    log_file.write_text(
                        json.dumps(log_data, indent=2, default=str),
                        encoding="utf-8"
                    )
                    
                    console.print(f"[green]✓ Log {log_id} approved[/green]")
                    return True
            except json.JSONDecodeError:
                continue
        
        console.print(f"[red]Log {log_id} not found[/red]")
        return False


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    console.print(Panel(
        "[bold]Harness System - Interactive Mode[/bold]\n"
        "Type a task and press Enter. Type 'quit' to exit.",
        title="🔧 Harness CLI",
        border_style="cyan"
    ))
    
    harness = Harness()
    
    while True:
        try:
            task = console.input("\n[bold cyan]Task>[/bold cyan] ")
            if task.lower() in ("quit", "exit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break
            
            result = harness.run_task(task)
            console.print(Panel(
                result["output"],
                title="📤 Output",
                border_style="green" if result["validation"]["passed"] else "red"
            ))
            
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye![/dim]")
            break
