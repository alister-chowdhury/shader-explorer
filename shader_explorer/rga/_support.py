import re
import subprocess

from ..config import RGA_EXEC
from ..util import future_init


_ASIC_EXTRACTION_RE = re.compile(
    # --> gfx900 (Vega)
    r"^^(?P<asic>[A-Za-z0-9_][A-Za-z0-9_ ]+)"
    # gfx900 (Vega) <---
    r"(?P<family>[^\n]+)\n"
    # AMD Radeon Instinct MI25x2 MxGPU
    # Instinct MI25x2
    # Radeon (TM) PRO WX 8200
    # Radeon (TM) Pro WX 9100
    # Radeon Instinct MI25
    # Radeon Instinct MI25 MxGPU
    # Radeon Instinct MI25x2
    # Radeon Pro SSG
    # Radeon Pro V340
    # Radeon Pro V340 MxGPU
    # Radeon Pro Vega 56
    # Radeon RX Vega
    # Radeon Vega Frontier Edition
    # Radeon(TM) Pro V320
    r"(?P<gpu_types>(?:[ \t]+[^\n]+\n?)+)",
    flags = re.MULTILINE
)


@future_init
def get_rga_asic_support():
    """Get RGA asic support..

    Returns:
        list[dict]: Asic support mapping
    """
    if not RGA_EXEC.exec_path:
        yield
        yield []
        return

    # It can take a bit of time for these (mainly online)
    # to return back with a good result.
    # Rather than blocking everything, we call them as background
    # processes, letting other parts of the pipeline carry on,
    # and actually waiting when really required.
    vk_online_proc = subprocess.Popen(
        (
            RGA_EXEC.exec_path,
            "-s",
            "vulkan",
            "--list-asics"
        ),
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    vk_offline_proc = subprocess.Popen(
        (
            RGA_EXEC.exec_path,
            "-s",
            "vk-spv-offline",
            "--list-asics"
        ),
        stdout = subprocess.PIPE
    )

    # Setup done
    yield

    result = []

    vk_offline_proc.wait()
    vk_offline = vk_offline_proc.stdout.read()
    if not isinstance(vk_offline, str):
        vk_offline = vk_offline.decode("utf8")

    for match in _ASIC_EXTRACTION_RE.finditer(vk_offline):
        asic = match.group("asic").strip()
        family = match.group("family").strip()
        gpu_types = match.group("gpu_types")
        gpu_types = [
            gpu_type.strip()
            for gpu_type in gpu_types.strip().split("\n")
        ]

        result.append({
            "name": "{0}".format(asic),
            "asic": asic,
            "family": family,
            "gpu_types": gpu_types,
            "online": False
        })

    vk_online_proc.wait()
    vk_online = vk_online_proc.stdout.read()

    if not isinstance(vk_online, str):
        vk_online = vk_online.decode("utf8")

    # Not a great way to check if we have valid online entries,
    # we can call vulkan_backend directly, but that seems a bit
    # unsupported.
    if any(hint in vk_online.lower() for hint in ("failed to locate", "falling back")):
        vk_online = ""

    for match in _ASIC_EXTRACTION_RE.finditer(vk_online):
        asic = match.group("asic").strip()
        family = match.group("family").strip()
        gpu_types = match.group("gpu_types")
        gpu_types = [
            gpu_type.strip()
            for gpu_type in gpu_types.strip().split("\n")
        ]

        result.append({
            "name": "{0} [online]".format(asic),
            "asic": asic,
            "family": family,
            "gpu_types": gpu_types,
            "online": True
        })

    yield result

