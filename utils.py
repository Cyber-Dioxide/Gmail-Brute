#!/usr/bin/env python3
"""
SMTP Tester Pro - Utility Tools
================================
Additional utilities for SMTP analysis and email validation.
"""

import socket
import ssl
import re
import dns.resolver
import smtplib
import asyncio
import threading
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    console = Console()
except ImportError:
    import sys
    print("Installing rich...")
    import os
    os.system("pip install rich")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    console = Console()


# ============== SMTP BANNER GRABBER ==============

@dataclass
class SMTPBannerInfo:
    """SMTP banner information"""
    host: str
    port: int
    banner: str
    server_type: str
    supports_tls: bool
    supports_starttls: bool
    auth_methods: List[str]
    response_time: float
    error: Optional[str] = None


class SMTPBannerGrabber:
    """Grab and analyze SMTP server banners"""

    COMMON_PORTS = [25, 587, 465, 2525, 2526]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def grab_banner(self, host: str, port: int = 25) -> SMTPBannerInfo:
        """Grab SMTP banner from server"""
        start_time = datetime.now()

        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # Connect
            sock.connect((host, port))

            # Receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()

            # Check for STARTTLS support
            supports_starttls = False
            supports_tls = port == 465
            auth_methods = []

            try:
                # Send EHLO
                sock.send(b"EHLO localhost\r\n")
                ehlo_response = sock.recv(2048).decode('utf-8', errors='ignore')

                # Parse capabilities
                for line in ehlo_response.split('\n'):
                    line = line.strip().upper()
                    if 'STARTTLS' in line:
                        supports_starttls = True
                    if 'AUTH' in line:
                        # Extract auth methods
                        auth_match = re.search(r'AUTH\s+(.+)', line)
                        if auth_match:
                            auth_methods = auth_match.group(1).split()
            except:
                pass

            sock.close()

            response_time = (datetime.now() - start_time).total_seconds()

            # Detect server type
            server_type = self._detect_server_type(banner)

            return SMTPBannerInfo(
                host=host,
                port=port,
                banner=banner,
                server_type=server_type,
                supports_tls=supports_tls,
                supports_starttls=supports_starttls,
                auth_methods=auth_methods,
                response_time=response_time
            )

        except socket.timeout:
            return SMTPBannerInfo(
                host=host, port=port, banner="",
                server_type="Unknown", supports_tls=False,
                supports_starttls=False, auth_methods=[],
                response_time=self.timeout, error="Connection timeout"
            )
        except socket.error as e:
            return SMTPBannerInfo(
                host=host, port=port, banner="",
                server_type="Unknown", supports_tls=False,
                supports_starttls=False, auth_methods=[],
                response_time=0, error=str(e)
            )

    def _detect_server_type(self, banner: str) -> str:
        """Detect SMTP server type from banner"""
        banner_lower = banner.lower()

        server_signatures = {
            'postfix': ['postfix', 'esmtp'],
            'exim': ['exim', 'esmtp'],
            'sendmail': ['sendmail', 'esmtp'],
            'microsoft exchange': ['microsoft', 'exchange', 'outlook'],
            'dovecot': ['dovecot'],
            'courier': ['courier', 'esmtp'],
            'qmail': ['qmail'],
            'zimbra': ['zimbra'],
            'gmail': ['gmail', 'google'],
            'yahoo': ['yahoo'],
            'outlook': ['outlook', 'hotmail'],
            'hmailserver': ['hmailserver'],
            'mailenable': ['mailenable'],
            'merak': ['merak'],
            'smartermail': ['smartermail'],
        }

        for server, signatures in server_signatures.items():
            for sig in signatures:
                if sig in banner_lower:
                    return server.title()

        return "Unknown"

    def scan_ports(self, host: str, ports: Optional[List[int]] = None) -> List[SMTPBannerInfo]:
        """Scan multiple ports for SMTP service"""
        ports = ports or self.COMMON_PORTS
        results = []

        for port in ports:
            info = self.grab_banner(host, port)
            if not info.error:
                results.append(info)

        return results


# ============== MX RECORD LOOKUP ==============

@dataclass
class MXRecord:
    """MX record information"""
    domain: str
    preference: int
    exchange: str
    ip_addresses: List[str]


class MXLookup:
    """DNS MX record lookup"""

    def __init__(self, nameservers: Optional[List[str]] = None):
        self.resolver = dns.resolver.Resolver()
        if nameservers:
            self.resolver.nameservers = nameservers

    def lookup(self, domain: str) -> List[MXRecord]:
        """Lookup MX records for a domain"""
        try:
            answers = self.resolver.resolve(domain, 'MX')
            records = []

            for rdata in answers:
                exchange = str(rdata.exchange).rstrip('.')
                preference = rdata.preference

                # Get A records for the exchange
                ip_addresses = self._get_a_records(exchange)

                records.append(MXRecord(
                    domain=domain,
                    preference=preference,
                    exchange=exchange,
                    ip_addresses=ip_addresses
                ))

            # Sort by preference
            records.sort(key=lambda x: x.preference)
            return records

        except dns.resolver.NoAnswer:
            return []
        except dns.resolver.NXDOMAIN:
            return []
        except Exception:
            return []

    def _get_a_records(self, hostname: str) -> List[str]:
        """Get A records for a hostname"""
        try:
            answers = self.resolver.resolve(hostname, 'A')
            return [str(rdata) for rdata in answers]
        except:
            return []

    def get_smtp_servers(self, domain: str) -> List[str]:
        """Get list of SMTP servers for a domain"""
        records = self.lookup(domain)
        return [r.exchange for r in records]


# ============== EMAIL VALIDATOR ==============

@dataclass
class EmailValidationResult:
    """Email validation result"""
    email: str
    is_valid_format: bool
    domain: str
    has_mx_records: bool
    mx_servers: List[str]
    is_disposable: bool
    is_catch_all: Optional[bool]
    mailbox_exists: Optional[bool]
    error: Optional[str] = None


class EmailValidator:
    """Comprehensive email validation"""

    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.com', 'throwaway.email', 'fakeinbox.com',
        'getairmail.com', 'mailnesia.com', 'tempail.com',
        'mohmal.com', 'yopmail.com', 'dispostable.com',
        'maildrop.cc', 'getnada.com', 'temp-mail.org'
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.mx_lookup = MXLookup()

    def validate_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def is_disposable(self, domain: str) -> bool:
        """Check if domain is disposable email provider"""
        return domain.lower() in self.DISPOSABLE_DOMAINS

    def verify_mailbox(self, email: str, mx_server: str) -> Tuple[bool, Optional[str]]:
        """Verify if mailbox exists via SMTP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((mx_server, 25))

            # Read banner
            sock.recv(1024)

            # Send EHLO
            sock.send(b"EHLO localhost\r\n")
            sock.recv(1024)

            # Send MAIL FROM
            sock.send(b"MAIL FROM:<test@example.com>\r\n")
            sock.recv(1024)

            # Send RCPT TO
            sock.send(f"RCPT TO:<{email}>\r\n".encode())
            response = sock.recv(1024).decode()

            sock.send(b"QUIT\r\n")
            sock.close()

            # Parse response
            if response.startswith('250'):
                return True, None
            elif response.startswith('550'):
                return False, "Mailbox does not exist"
            else:
                return None, response.strip()

        except Exception as e:
            return None, str(e)

    def check_catch_all(self, domain: str, mx_server: str) -> bool:
        """Check if domain has catch-all enabled"""
        random_email = f"nonexistent{datetime.now().timestamp()}@{domain}"
        exists, _ = self.verify_mailbox(random_email, mx_server)
        return exists == True

    def validate(self, email: str, verify_mailbox: bool = False) -> EmailValidationResult:
        """Comprehensive email validation"""
        # Format validation
        is_valid_format = self.validate_format(email)

        if not is_valid_format:
            return EmailValidationResult(
                email=email,
                is_valid_format=False,
                domain="",
                has_mx_records=False,
                mx_servers=[],
                is_disposable=False,
                is_catch_all=None,
                mailbox_exists=None,
                error="Invalid email format"
            )

        # Extract domain
        domain = email.split('@')[1].lower()

        # Check MX records
        mx_servers = self.mx_lookup.get_smtp_servers(domain)
        has_mx = len(mx_servers) > 0

        # Check if disposable
        is_disposable = self.is_disposable(domain)

        result = EmailValidationResult(
            email=email,
            is_valid_format=True,
            domain=domain,
            has_mx_records=has_mx,
            mx_servers=mx_servers,
            is_disposable=is_disposable,
            is_catch_all=None,
            mailbox_exists=None
        )

        # Verify mailbox if requested
        if verify_mailbox and mx_servers:
            exists, error = self.verify_mailbox(email, mx_servers[0])
            result.mailbox_exists = exists
            result.error = error

            # Check catch-all
            if exists:
                result.is_catch_all = self.check_catch_all(domain, mx_servers[0])

        return result


# ============== SMTP SERVER SCANNER ==============

@dataclass
class SMTPScanResult:
    """SMTP server scan result"""
    host: str
    port: int
    is_open: bool
    banner: Optional[str] = None
    supports_ssl: bool = False
    supports_starttls: bool = False
    auth_methods: List[str] = None
    response_time: float = 0.0


class SMTPScanner:
    """Scan hosts for SMTP services"""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.banner_grabber = SMTPBannerGrabber(timeout)

    def scan_host(self, host: str, port: int = 25) -> SMTPScanResult:
        """Scan single host for SMTP service"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            start_time = datetime.now()
            result = sock.connect_ex((host, port))
            response_time = (datetime.now() - start_time).total_seconds()

            if result == 0:
                # Port is open, grab banner
                banner_info = self.banner_grabber.grab_banner(host, port)
                sock.close()

                return SMTPScanResult(
                    host=host,
                    port=port,
                    is_open=True,
                    banner=banner_info.banner,
                    supports_ssl=port == 465,
                    supports_starttls=banner_info.supports_starttls,
                    auth_methods=banner_info.auth_methods,
                    response_time=response_time
                )
            else:
                sock.close()
                return SMTPScanResult(
                    host=host,
                    port=port,
                    is_open=False,
                    response_time=response_time
                )

        except Exception as e:
            return SMTPScanResult(
                host=host,
                port=port,
                is_open=False,
                response_time=0
            )

    def scan_hosts(self, hosts: List[str], port: int = 25) -> List[SMTPScanResult]:
        """Scan multiple hosts"""
        results = []
        for host in hosts:
            result = self.scan_host(host, port)
            results.append(result)
        return results

    def scan_port_range(self, host: str, ports: List[int]) -> List[SMTPScanResult]:
        """Scan multiple ports on a host"""
        results = []
        for port in ports:
            result = self.scan_host(host, port)
            results.append(result)
        return results


# ============== CLI INTERFACE ==============

def show_banner_grab(host: str, port: int = 25):
    """Display SMTP banner information"""
    console.print(f"\n[bold cyan]Grabbing SMTP banner for {host}:{port}[/bold cyan]\n")

    grabber = SMTPBannerGrabber()
    info = grabber.grab_banner(host, port)

    table = Table(title="SMTP Server Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Host", info.host)
    table.add_row("Port", str(info.port))
    table.add_row("Server Type", info.server_type)
    table.add_row("Supports SSL", "Yes" if info.supports_tls else "No")
    table.add_row("Supports STARTTLS", "Yes" if info.supports_starttls else "No")
    table.add_row("Auth Methods", ", ".join(info.auth_methods) if info.auth_methods else "Unknown")
    table.add_row("Response Time", f"{info.response_time:.2f}s")

    console.print(table)

    if info.banner:
        console.print(f"\n[bold]Banner:[/bold]")
        console.print(Panel(info.banner, border_style="blue"))

    if info.error:
        console.print(f"\n[red]Error: {info.error}[/red]")


def show_mx_lookup(domain: str):
    """Display MX records for a domain"""
    console.print(f"\n[bold cyan]Looking up MX records for {domain}[/bold cyan]\n")

    lookup = MXLookup()
    records = lookup.lookup(domain)

    if not records:
        console.print(f"[red]No MX records found for {domain}[/red]")
        return

    table = Table(title=f"MX Records for {domain}")
    table.add_column("Preference", style="yellow")
    table.add_column("Exchange", style="cyan")
    table.add_column("IP Addresses", style="green")

    for record in records:
        table.add_row(
            str(record.preference),
            record.exchange,
            ", ".join(record.ip_addresses) if record.ip_addresses else "N/A"
        )

    console.print(table)


def show_email_validation(email: str, verify_mailbox: bool = False):
    """Display email validation result"""
    console.print(f"\n[bold cyan]Validating email: {email}[/bold cyan]\n")

    validator = EmailValidator()
    result = validator.validate(email, verify_mailbox=verify_mailbox)

    table = Table(title="Email Validation Result")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    table.add_row("Valid Format", "✓" if result.is_valid_format else "✗")
    table.add_row("Domain", result.domain)
    table.add_row("Has MX Records", "✓" if result.has_mx_records else "✗")
    table.add_row("MX Servers", ", ".join(result.mx_servers[:3]) if result.mx_servers else "None")
    table.add_row("Disposable", "Yes" if result.is_disposable else "No")

    if verify_mailbox:
        if result.mailbox_exists is True:
            table.add_row("Mailbox Exists", "[green]✓[/green]")
        elif result.mailbox_exists is False:
            table.add_row("Mailbox Exists", "[red]✗[/red]")
        else:
            table.add_row("Mailbox Exists", "[yellow]Unknown[/yellow]")

        if result.is_catch_all is not None:
            table.add_row("Catch-All", "Yes" if result.is_catch_all else "No")

    console.print(table)

    if result.error:
        console.print(f"\n[yellow]Note: {result.error}[/yellow]")


def main():
    """Main entry point for utilities"""
    import argparse

    parser = argparse.ArgumentParser(
        description="SMTP Tester Pro - Utility Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Banner grab command
    banner_parser = subparsers.add_parser("banner", help="Grab SMTP banner")
    banner_parser.add_argument("host", help="SMTP server host")
    banner_parser.add_argument("-p", "--port", type=int, default=25, help="Port number")

    # MX lookup command
    mx_parser = subparsers.add_parser("mx", help="Lookup MX records")
    mx_parser.add_argument("domain", help="Domain to lookup")

    # Email validation command
    email_parser = subparsers.add_parser("validate", help="Validate email address")
    email_parser.add_argument("email", help="Email address to validate")
    email_parser.add_argument("--verify", action="store_true", help="Verify mailbox exists")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for SMTP servers")
    scan_parser.add_argument("host", help="Host to scan")
    scan_parser.add_argument("-p", "--ports", type=int, nargs="+",
                            default=[25, 587, 465, 2525],
                            help="Ports to scan")

    args = parser.parse_args()

    if args.command == "banner":
        show_banner_grab(args.host, args.port)
    elif args.command == "mx":
        show_mx_lookup(args.domain)
    elif args.command == "validate":
        show_email_validation(args.email, args.verify)
    elif args.command == "scan":
        console.print(f"\n[bold cyan]Scanning {args.host} for SMTP services[/bold cyan]\n")
        scanner = SMTPScanner()
        results = scanner.scan_port_range(args.host, args.ports)

        table = Table(title="Scan Results")
        table.add_column("Port", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("SSL", style="yellow")
        table.add_column("STARTTLS", style="yellow")
        table.add_column("Banner", style="dim")

        for result in results:
            status = "[green]Open[/green]" if result.is_open else "[red]Closed[/red]"
            ssl_status = "✓" if result.supports_ssl else "✗"
            starttls_status = "✓" if result.supports_starttls else "✗"
            banner = (result.banner[:40] + "...") if result.banner and len(result.banner) > 40 else (result.banner or "N/A")

            table.add_row(
                str(result.port),
                status,
                ssl_status,
                starttls_status,
                banner
            )

        console.print(table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
