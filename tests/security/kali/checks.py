#!/usr/bin/env python3
"""Per-tool parsers for the Kali pentest agent (TASK-0142 / SPEC-0024 Phase 4).

Runs inside the kali container (python3 stdlib only). Each parse_* function
turns one tool's raw output into checks for schema "upcp-security-result/v1"
(structural helpers mirrored from tests/security/common.py, which is host-only
and not mounted into the container). CLI entrypoint: format_result.py, which
also owns the header audit and token redaction.

Severity contract (kali exit: high/critical => findings):
    sqlmap injectable -> critical, risky exposed service -> high,
    nikto advisory -> medium, missing security header -> low,
    server banner / scan-budget notes -> info.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Services that must never be exposed on the app host (fail = high).
RISKY_PORTS = {
    21: "ftp",
    23: "telnet",
    25: "smtp",
    69: "tftp",
    110: "pop3",
    139: "netbios-ssn",
    143: "imap",
    445: "microsoft-ds",
    512: "rexec",
    513: "rlogin",
    514: "rsh",
    1433: "ms-sql-s",
    1521: "oracle",
    2049: "nfs",
    2375: "docker",
    3389: "ms-wbt-server",
    5432: "postgres",
    5900: "vnc",
    6379: "redis",
    9200: "elasticsearch",
    11211: "memcached",
}

# nikto "+" lines that are scan metadata, not advisories.
NIKTO_META = re.compile(
    r"^\+\s*(End|Server|Target|Host IP|No CGI|Retrieved|Allowed HTTP|"
    r"Non-Html|The anti-clickjacking|Cookie|Java|Server may leak)",
    re.I,
)


def check(name, category, ok, expected="", actual="", detail="", severity=""):
    return {
        "name": name,
        "category": category,
        "status": "pass" if ok else "fail",
        "expected": expected,
        "actual": actual,
        "detail": detail,
        "severity": severity,
    }


def tail(path: Path, limit: int = 500) -> str:
    return path.read_text(errors="replace")[-limit:] if path.is_file() else ""


def parse_nmap(raw: Path, rc: int) -> list[dict]:
    if rc == 124:
        return [
            check(
                "nmap: scan completed",
                "port-scan",
                False,
                expected="nmap within 150s",
                actual="timeout",
                detail="nmap cut at time budget — results incomplete",
                severity="info",
            )
        ]
    if rc != 0 or not (raw / "nmap.xml").is_file():
        return [
            check(
                "nmap: scan completed",
                "port-scan",
                False,
                expected="nmap exits 0 with XML output",
                actual=f"rc={rc}",
                detail=tail(raw / "nmap.log"),
                severity="medium",
            )
        ]
    checks = [
        check(
            "nmap: service scan completed",
            "port-scan",
            True,
            actual="rc=0",
            detail="-Pn -sT -sV --top-ports 100 (connect scan: non-root)",
        )
    ]
    try:
        root = ET.parse(raw / "nmap.xml").getroot()
    except ET.ParseError as exc:
        return checks + [
            check("nmap: XML parseable", "port-scan", False, actual=str(exc), severity="medium")
        ]
    open_ports = 0
    for port in root.iter("port"):
        state = port.find("state")
        if state is None or state.get("state") != "open":
            continue
        open_ports += 1
        portid = int(port.get("portid", 0))
        svc_el = port.find("service")
        desc = ""
        if svc_el is not None:
            desc = " ".join(
                filter(None, (svc_el.get("name"), svc_el.get("product"), svc_el.get("version")))
            )
        if portid in RISKY_PORTS:
            checks.append(
                check(
                    f"nmap: risky service {RISKY_PORTS[portid]} exposed",
                    "port-scan",
                    False,
                    expected="only application ports reachable",
                    actual=f"{portid}/tcp open ({desc})",
                    detail=f"port {portid} commonly associated with "
                    f"{RISKY_PORTS[portid]} — verify exposure is intended",
                    severity="high",
                )
            )
        else:
            checks.append(
                check(
                    f"nmap: {portid}/tcp open ({desc or 'unknown'})",
                    "port-scan",
                    True,
                    actual="open",
                    detail="expected service on test stack",
                )
            )
    if open_ports == 0:
        checks.append(
            check(
                "nmap: open ports found",
                "port-scan",
                False,
                expected="application port reachable",
                actual="none",
                detail="no open ports — target down or filtered",
                severity="high",
            )
        )
    return checks


def parse_nikto(raw: Path, rc: int, max_seconds: int) -> list[dict]:
    if rc == 124:
        return [
            check(
                "nikto: scan completed",
                "web-scan",
                False,
                expected=f"nikto within {max_seconds}s",
                actual="timeout",
                detail="nikto cut at time budget",
                severity="info",
            )
        ]
    if rc not in (0, 1) or not (raw / "nikto.txt").is_file():
        return [
            check(
                "nikto: scan completed",
                "web-scan",
                False,
                expected="nikto exits 0 with output",
                actual=f"rc={rc}",
                detail=tail(raw / "nikto.log"),
                severity="medium",
            )
        ]
    lines = (raw / "nikto.txt").read_text(errors="replace").splitlines()
    findings = [
        re.sub(r"\s+", " ", ln.strip())[:160]
        for ln in lines
        if ln.strip().startswith("+") and not NIKTO_META.match(ln.strip())
    ][:20]
    if not findings:
        return [
            check(
                "nikto: no vulnerabilities reported",
                "web-scan",
                True,
                actual="0 advisories",
                detail=f"tuned scan (budget {max_seconds}s) found no advisories",
            )
        ]
    return [
        check(
            f"nikto: {f}",
            "web-scan",
            False,
            expected="clean nikto output",
            actual=f,
            detail=f,
            severity="medium",
        )
        for f in findings
    ]


def parse_sqlmap(raw: Path, rc: int, max_seconds: int) -> list[dict]:
    text = tail(raw / "sqlmap.log", limit=100_000)
    if rc == 124:
        return [
            check(
                "sqlmap: smoke completed within budget",
                "injection",
                False,
                expected=f"sqlmap within {max_seconds}s",
                actual="timeout",
                detail="sqlmap hard-cut by timeout before a verdict — "
                "inconclusive, scope reduced per task policy",
                severity="info",
            )
        ]
    if not text.strip():
        return [
            check(
                "sqlmap: smoke ran",
                "injection",
                False,
                expected="sqlmap output",
                actual=f"rc={rc}",
                detail="no sqlmap output captured",
                severity="medium",
            )
        ]
    if re.search(r"is vulnerable", text, re.I):
        param = re.search(r"Parameter: ([^\s(]+)", text)
        return [
            check(
                f"sqlmap: injection in {param.group(1) if param else 'param'}",
                "injection",
                False,
                expected="no injectable parameters",
                actual="VULNERABLE",
                detail="sqlmap reported an injectable parameter (--level 1 --risk 1 smoke)",
                severity="critical",
            )
        ]
    if re.search(
        r"do not appear to be injectable|does not seem to be injectable|"
        r"not injectable",
        text,
        re.I,
    ):
        return [
            check(
                "sqlmap: representative param not injectable",
                "injection",
                True,
                actual="not injectable",
                detail="--batch --crawl=0 --level=1 --risk=1 smoke on "
                "/api/v1/search?q= (authenticated when login OK)",
            )
        ]
    return [
        check(
            "sqlmap: smoke verdict",
            "injection",
            False,
            expected="a clear injectable/not-injectable verdict",
            actual=f"rc={rc}",
            detail=re.sub(r"\s+", " ", text)[-400:],
            severity="low",
        )
    ]
