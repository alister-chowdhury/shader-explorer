import subprocess
import uuid
import os
import shutil

from ..config import RGA_EXEC, DOT_EXEC

# TODO FIGURE OUT AN ALTERNATIVE TO DOT


class RGACompileInfo(object):
    __slots__ = ("asic", "online", "cs", "vs", "gs", "fs", "output_dir")

    def __init__(self):
        self.asic = None
        self.online = False
        self.cs = None
        self.vs = None
        self.gs = None
        self.fs = None
        self.output_dir = None


class RGACompiledShader(object):
    def __init__(
        self,
        analysis=None,
        isa=None,
        parsed_isa=None,
        cfg=None,
        cfg_svg=None,
        cfg_png=None,
    ):
        self.analysis = analysis
        self.isa = isa
        self.parsed_isa = parsed_isa
        self.cfg = cfg
        self._cfg_svg_dirty = bool(cfg_svg)
        self._cfg_png_dirty = bool(cfg_png)
        self.cfg_svg = cfg_svg
        self.cfg_png = cfg_png

    def ensure_cfg_svg_rendered(self):
        if self._cfg_svg_dirty:
            subprocess.Popen((
                DOT_EXEC.exec_path,
                "-Nfontname=sans",
                "-Tsvg",
                self.cfg,
                "-o",
                self.cfg_svg,
            )).wait()
            self._cfg_svg_dirty = False

    def ensure_cfg_png_rendered(self):
        if self._cfg_png_dirty:
            subprocess.Popen((
                DOT_EXEC.exec_path,
                "-Nfontname=sans",
                "-Tpng",
                self.cfg,
                "-o",
                self.cfg_png,
            )).wait()
            self._cfg_png_dirty = False


def rga_compile(info):
    """Compute shaders using RGA.

    Args:
        info (RGACompileInfo): Description of what to compile.

    Returns:
        dict: Resulting mapping.

        {
            "stdout": ...,
            "shaders":
            {
                type: RGACompiledShader
            }
        }
    """

    if not RGA_EXEC.exec_path:
        raise ValueError("RGA is not supported!")
    if not info.asic:
        raise ValueError("No asic provided!")
    if not (info.cs or info.vs or info.gs or info.fs):
        raise ValueError("No shaders provided!")
    if info.cs and (info.vs or info.gs or info.fs):
        raise ValueError("Cannot mix compute and graphics pipelines")
    if not info.output_dir:
        raise ValueError("No output dir provided!")
    scratch_dir = os.path.join(
        info.output_dir, "TMP_{0}".format(str(uuid.uuid4()))
    )

    try:
        analysis_dir = os.path.join(scratch_dir, "a")
        isa_dir = os.path.join(scratch_dir, "isa")
        cfg_dir = os.path.join(scratch_dir, "cfg")

        os.makedirs(analysis_dir)
        os.makedirs(isa_dir)
        os.makedirs(cfg_dir)

        command = [
            RGA_EXEC.exec_path,
            "-s",
            "vulkan" if info.online else "vk-spv-offline",
            "-c",
            info.asic,
            "--isa",
            os.path.join(isa_dir, "isa.amdisa"),
            "--parse-isa",
            "--cfg",
            os.path.join(cfg_dir, "cfg.dot"),
            "-a",
            os.path.join(analysis_dir, "a.csv"),
        ]

        for shader_type, shader in (
            ("--comp", info.cs),
            ("--vert", info.vs),
            ("--geom", info.gs),
            ("--frag", info.fs),
        ):
            if shader:
                command.extend((shader_type, shader))
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        generate_mapping = lambda shader_type: {
            "analysis": (
                os.path.join(
                    analysis_dir,
                    "{0}_a_{1}.csv".format(info.asic, shader_type),
                ),
                os.path.join(
                    info.output_dir, "{0}_analysis.csv".format(shader_type)
                ),
            ),
            "isa": (
                os.path.join(
                    isa_dir,
                    "{0}_isa_{1}.amdisa".format(info.asic, shader_type),
                ),
                os.path.join(
                    info.output_dir, "{0}_isa.amdisa".format(shader_type)
                ),
            ),
            "parsed_isa": (
                os.path.join(
                    isa_dir, "{0}_isa_{1}.csv".format(info.asic, shader_type)
                ),
                os.path.join(
                    info.output_dir, "{0}_parsedisa.csv".format(shader_type)
                ),
            ),
            "cfg": (
                os.path.join(
                    cfg_dir, "{0}_cfg_{1}.dot".format(info.asic, shader_type)
                ),
                os.path.join(
                    info.output_dir, "{0}_cfg.dot".format(shader_type)
                ),
            ),
        }

        expected_mappings = {}

        for shader_type, shader in (
            ("comp", info.cs),
            ("vert", info.vs),
            ("geom", info.gs),
            ("frag", info.fs),
        ):
            if shader:
                expected_mappings[shader_type] = generate_mapping(shader_type)
        proc.wait()

        # rga doesn't gracefully return a bad error code
        # or even write to stderr, so if we want to detect
        # sometihng went wrong we need to do a bit of forensics.
        # However, we can bubble this up to the user, who will
        # probably realise something went wrong when the only
        # thing they can see is the output log
        stdout = proc.stdout.read()
        if not isinstance(stdout, str):
            stdout = stdout.decode("utf8")
        result = {"stdout": stdout, "shaders": {}}

        for shader_type, mapping in expected_mappings.items():
            output_mapping = {}

            for key, src_dst in mapping.items():
                src, dst = src_dst
                if not os.path.isfile(src):
                    dst = None
                else:
                    shutil.copyfile(src, dst)
                output_mapping[key] = dst
            if DOT_EXEC.found:
                cfg_png = None
                cfg_svg = None
                cfg_dot = output_mapping["cfg"]
                if cfg_dot:
                    cfg_png = os.path.join(
                        info.output_dir, "{0}_cfg.png".format(shader_type)
                    )
                    cfg_svg = os.path.join(
                        info.output_dir, "{0}_cfg.svg".format(shader_type)
                    )
                output_mapping["cfg_svg"] = cfg_svg
                output_mapping["cfg_png"] = cfg_png
            result["shaders"][shader_type] = RGACompiledShader(
                **output_mapping
            )
        return result
    finally:
        shutil.rmtree(scratch_dir)
