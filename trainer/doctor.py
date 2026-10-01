"""Non-mutating local environment checks."""

from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import asdict, dataclass

from trainer.config import ProjectPaths, huggingface_token_present


@dataclass(frozen=True)
class DoctorReport:
    architecture: str
    python_version: str
    python_supported: bool
    free_disk_gib: float
    hf_token_present: bool
    mlx_available: bool


def inspect(paths: ProjectPaths) -> DoctorReport:
    disk = shutil.disk_usage(paths.root)
    python_supported = sys.version_info[:2] == (3, 12)
    try:
        import mlx  # noqa: F401
        mlx_available = True
    except ImportError:
        mlx_available = False
    return DoctorReport(
        architecture=platform.machine(),
        python_version=platform.python_version(),
        python_supported=python_supported,
        free_disk_gib=round(disk.free / (1024 ** 3), 1),
        hf_token_present=huggingface_token_present(paths.root),
        mlx_available=mlx_available,
    )


def as_dict(report: DoctorReport) -> dict[str, object]:
    return asdict(report)
