"""Fuzz scenario modules.

Each module exposes ``run(base_url: str) -> list[dict]`` returning check
records built via tests.security.common.check. The registry of scenarios
lives in tests/security/fuzz/runner.py (mirrors tests/chaos/runner.py).
"""
