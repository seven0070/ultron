"""
Build #010 — Environment validator.

Detects Python, OS, CPU, RAM, disk, GPU, CUDA and reports readiness.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field

import psutil

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class EnvironmentReport:
    python_version: str
    python_ok: bool
    os_name: str
    os_release: str
    cpu: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    ram_total_gb: float
    ram_available_gb: float
    disk_free_gb: float
    gpu_detected: bool
    gpu_name: str
    cuda_available: bool
    cuda_version: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return asdict(self)


class EnvironmentManager:
    """Detects and validates the runtime environment for Monad."""

    MIN_PYTHON = (3, 12)
    MIN_RAM_GB = 8.0
    MIN_DISK_FREE_GB = 10.0

    def report(self) -> EnvironmentReport:
        py = sys.version_info
        py_str = f"{py.major}.{py.minor}.{py.micro}"
        py_ok = (py.major, py.minor) >= self.MIN_PYTHON

        mem = psutil.virtual_memory()
        disk = shutil.disk_usage(".")

        gpu_name, cuda_avail, cuda_ver = self._detect_gpu()

        report = EnvironmentReport(
            python_version=py_str,
            python_ok=py_ok,
            os_name=platform.system(),
            os_release=platform.release(),
            cpu=platform.processor() or "Unknown",
            cpu_cores_physical=psutil.cpu_count(logical=False) or 0,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 0,
            ram_total_gb=round(mem.total / (1024**3), 2),
            ram_available_gb=round(mem.available / (1024**3), 2),
            disk_free_gb=round(disk.free / (1024**3), 2),
            gpu_detected=bool(gpu_name),
            gpu_name=gpu_name or "None",
            cuda_available=cuda_avail,
            cuda_version=cuda_ver,
        )

        # Validation
        if not py_ok:
            report.errors.append(
                f"Python {self.MIN_PYTHON[0]}.{self.MIN_PYTHON[1]}+ required "
                f"(found {py_str})"
            )
        if report.ram_total_gb < self.MIN_RAM_GB:
            report.warnings.append(
                f"RAM {report.ram_total_gb} GB is below recommended {self.MIN_RAM_GB} GB"
            )
        if report.disk_free_gb < self.MIN_DISK_FREE_GB:
            report.warnings.append(
                f"Only {report.disk_free_gb} GB free — recommend ≥ {self.MIN_DISK_FREE_GB} GB"
            )
        if not report.gpu_detected:
            report.warnings.append("No GPU detected — CPU inference will be slow")
        elif not report.cuda_available:
            report.warnings.append("GPU found but CUDA runtime not available")

        return report

    # -- internal -------------------------------------------------------------

    def _detect_gpu(self) -> tuple[str, bool, str]:
        """Return (gpu_name, cuda_available, cuda_version)."""
        gpu_name = ""
        cuda_avail = False
        cuda_ver = "N/A"

        # Try nvidia-smi (fast, no python deps)
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                out = subprocess.run(
                    [nvidia_smi, "--query-gpu=name,driver_version",
                     "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5,
                )
                if out.returncode == 0 and out.stdout.strip():
                    gpu_name = out.stdout.strip().split("\n")[0].split(",")[0].strip()
                    cuda_avail = True

                # Get CUDA runtime version
                out2 = subprocess.run(
                    [nvidia_smi], capture_output=True, text=True, timeout=5,
                )
                if "CUDA Version:" in out2.stdout:
                    cuda_ver = out2.stdout.split("CUDA Version:")[1].split()[0].strip()
            except Exception as e:
                log.debug("nvidia-smi probe failed: {}", e)

        return gpu_name, cuda_avail, cuda_ver
