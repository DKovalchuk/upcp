"""Chaos engine — Docker-based fault injection for UPCP test environment.

Provides controlled fault injection: container kill/stop/pause,
network latency, resource stress. All operations are reversible.

Requires: docker Python SDK (pip install docker)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger("chaos.engine")

# process-wide JWT cache for authenticated integrity probes
_AUTH_CACHE: dict[str, str] | None = None

try:
    import docker
except ImportError:
    docker = None  # type: ignore[assignment]
    logger.warning("docker SDK not installed — ChaosEngine will not be available")


class FaultType(Enum):
    KILL = "kill"
    STOP = "stop"
    PAUSE = "pause"
    NETWORK_LATENCY = "network_latency"
    NETWORK_LOSS = "network_loss"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"


@dataclass
class ContainerInfo:
    name: str
    id: str
    status: str
    health: str | None = None


@dataclass
class ResourceSnapshot:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_limit_mb: float = 0.0
    net_rx_bytes: int = 0
    net_tx_bytes: int = 0
    pids: int = 0
    timestamp: float = field(default_factory=time.time)


class ChaosEngine:
    """Docker-based chaos engine for fault injection and recovery."""

    def __init__(self, compose_project: str = "upcp-test"):
        if docker is None:
            raise RuntimeError(
                "docker SDK is required for ChaosEngine. Install with: pip install docker"
            )
        self.client = docker.from_env()
        self.compose_project = compose_project
        self._containers: dict[str, docker.models.containers.Container] = {}

    def find_container(self, service_name: str) -> docker.models.containers.Container:
        """Find a container by service name within the compose project."""
        if service_name in self._containers:
            container = self._containers[service_name]
            container.reload()
            return container

        label = f"com.docker.compose.project={self.compose_project}"
        label_service = f"com.docker.compose.service={service_name}"

        containers = self.client.containers.list(
            all=True,
            filters={"label": [label, label_service]},
        )
        if not containers:
            raise ValueError(
                f"Container not found: service={service_name}, project={self.compose_project}"
            )

        container = containers[0]
        self._containers[service_name] = container
        return container

    def get_auth_headers(self) -> dict[str, str]:
        """Cached JWT headers for authenticated data checks (TASK-0141).

        Integrity probes hit GET /api/v1/projects, which requires a bearer
        token — bare requests got 401 and failed every data check.
        """
        global _AUTH_CACHE
        if _AUTH_CACHE is None:
            email = os.getenv("PERF_EMAIL", "admin@example.com")
            password = os.getenv("PERF_PASSWORD", "TestAdmin123!")
            base = os.getenv("CHAOS_BASE_URL", "http://localhost:38082")
            try:
                resp = httpx.post(
                    f"{base}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                token = resp.json().get("access_token")
                if resp.status_code == 200 and token:
                    _AUTH_CACHE = {"Authorization": f"Bearer {token}"}
                else:
                    logger.warning("integrity login failed: HTTP %s", resp.status_code)
            except Exception as e:
                logger.warning("integrity login error: %s", e)
            if _AUTH_CACHE is None:
                _AUTH_CACHE = {}
        return _AUTH_CACHE

    def get_status(self, service_name: str) -> ContainerInfo:
        """Get container status and health."""
        container = self.find_container(service_name)
        container.reload()

        health = None
        if container.attrs.get("State", {}).get("Health"):
            health = container.attrs["State"]["Health"]["Status"]

        return ContainerInfo(
            name=service_name,
            id=container.short_id,
            status=container.status,
            health=health,
        )

    def get_resources(self, service_name: str) -> ResourceSnapshot:
        """Capture resource usage snapshot."""
        container = self.find_container(service_name)
        try:
            stats = container.stats(stream=False)
        except Exception:
            return ResourceSnapshot()

        # CPU
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"]["online_cpus"]
        cpu_percent = (cpu_delta / system_delta * num_cpus * 100) if system_delta > 0 else 0

        # Memory
        mem_usage = stats["memory_stats"].get("usage", 0)
        mem_limit = stats["memory_stats"].get("limit", 0)

        # Network
        networks = stats.get("networks", {})
        net_rx = sum(v.get("rx_bytes", 0) for v in networks.values())
        net_tx = sum(v.get("tx_bytes", 0) for v in networks.values())

        return ResourceSnapshot(
            cpu_percent=round(cpu_percent, 2),
            memory_mb=round(mem_usage / 1024 / 1024, 2),
            memory_limit_mb=round(mem_limit / 1024 / 1024, 2),
            net_rx_bytes=net_rx,
            net_tx_bytes=net_tx,
            pids=stats.get("pids_stats", {}).get("current", 0),
        )

    # ── Fault Injection ───────────────────────────────────────

    def kill(self, service_name: str) -> float:
        """Kill container (SIGKILL). Returns time taken in seconds."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.kill()
        elapsed = time.monotonic() - start
        logger.info("Killed %s in %.3fs", service_name, elapsed)
        return elapsed

    def stop(self, service_name: str, timeout: int = 10) -> float:
        """Stop container gracefully. Returns time taken."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.stop(timeout=timeout)
        elapsed = time.monotonic() - start
        logger.info("Stopped %s in %.3fs", service_name, elapsed)
        return elapsed

    def start(self, service_name: str) -> float:
        """Start a stopped container. Returns time taken."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.start()
        elapsed = time.monotonic() - start
        logger.info("Started %s in %.3fs", service_name, elapsed)
        return elapsed

    def restart(self, service_name: str, timeout: int = 10) -> float:
        """Restart container. Returns time taken."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.restart(timeout=timeout)
        elapsed = time.monotonic() - start
        logger.info("Restarted %s in %.3fs", service_name, elapsed)
        return elapsed

    def pause(self, service_name: str) -> float:
        """Pause container (freeze processes). Returns time taken."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.pause()
        elapsed = time.monotonic() - start
        logger.info("Paused %s in %.3fs", service_name, elapsed)
        return elapsed

    def unpause(self, service_name: str) -> float:
        """Unpause container. Returns time taken."""
        container = self.find_container(service_name)
        start = time.monotonic()
        container.unpause()
        elapsed = time.monotonic() - start
        logger.info("Unpaused %s in %.3fs", service_name, elapsed)
        return elapsed

    # ── Health Monitoring ─────────────────────────────────────

    def wait_for_healthy(
        self, service_name: str, timeout: int = 60, interval: float = 1.0
    ) -> float:
        """Wait for container to become healthy. Returns time waited."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            info = self.get_status(service_name)
            if info.health == "healthy" or (info.status == "running" and info.health is None):
                elapsed = time.monotonic() - start
                logger.info("%s healthy after %.1fs", service_name, elapsed)
                return elapsed
            time.sleep(interval)
        raise TimeoutError(f"{service_name} not healthy after {timeout}s")

    def wait_for_unhealthy(
        self, service_name: str, timeout: int = 30, interval: float = 0.5
    ) -> float:
        """Wait for container to become unhealthy or stop. Returns time waited."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            info = self.get_status(service_name)
            if info.status in ("exited", "dead", "restarting"):
                elapsed = time.monotonic() - start
                logger.info("%s down after %.1fs", service_name, elapsed)
                return elapsed
            if info.health == "unhealthy":
                elapsed = time.monotonic() - start
                logger.info("%s unhealthy after %.1fs", service_name, elapsed)
                return elapsed
            time.sleep(interval)
        raise TimeoutError(f"{service_name} still running after {timeout}s")

    # ── HTTP Probing ──────────────────────────────────────────

    def probe_http(self, url: str, timeout: float = 5.0, retries: int = 1) -> dict[str, object]:
        """Probe an HTTP endpoint. Returns status, latency, error."""
        for attempt in range(retries):
            try:
                start = time.monotonic()
                resp = httpx.get(url, timeout=timeout)
                latency = time.monotonic() - start
                return {
                    "status_code": resp.status_code,
                    "latency_ms": round(latency * 1000, 2),
                    "success": resp.status_code < 500,
                    "attempt": attempt + 1,
                }
            except Exception as e:
                if attempt == retries - 1:
                    return {
                        "status_code": 0,
                        "latency_ms": 0,
                        "success": False,
                        "error": str(e),
                        "attempt": attempt + 1,
                    }
                time.sleep(0.5)
        return {"status_code": 0, "success": False, "attempt": retries}
