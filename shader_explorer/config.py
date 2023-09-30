import shutil
import os


class _FoundExec(object):
    """Simple wrapper around resolved executables."""

    def __init__(self, exec_name, env_override):
        """Initializer.

        Args:
            exec_path (str): Resolved path.
            env_override (str): Envvar to override.
        """
        self.found = False
        self.name = exec_name
        self.exec_name = exec_name
        self.exec_path = None
        self.env_override = env_override

        found_env = os.getenv(env_override)
        if found_env:
            env_name = "${0}".format(env_override)
            if os.path.isfile(found_env):
                self.name = "{0} [{1}]".format(self.exec_name, env_name)
                self.exec_path = found_env
                self.found = True
            else:
                self._update(env_name, found_env)
        self._update(None, None)

    def __repr__(self):
        return "{0} ({1})".format(self.name, self.exec_path or "not found")

    def _update(self, resolver_name, paths):
        """If not found, try to rsolve it withn another directory..

        Args:
            resolver_name (str): Method used for resolving
            paths (str or None): Paths to resolve against.
        """
        if not self.found:
            found = shutil.which(self.exec_name, path=paths)
            if found:
                if resolver_name:
                    self.name = "{0} [{1}]".format(
                        self.exec_name, resolver_name
                    )
                self.exec_path = found
                self.found = True


def _find_executable(exec_name, env_override):
    """Find an executables path.

    Args:
        exec_name (str): Exec name.
        env_override (str): Envvar to override.

    Returns:
        _FoundExec: Wrapper around the exec.
    """
    # Check for an env override, but make sure
    # it actually exists, before commiting to using it
    found = _FoundExec(exec_name, env_override)
    return found


def _use_tool_for_missing_tools(parent_tool, recursive, *tools):
    """Use a tools path to find other tools.

    Args:
        parent_tool (_FoundExec): Parent tool.
        recursive (bool): Recursively search.
        *tools (_FoundExec): Tools that may need finding.
    """
    if not parent_tool.found:
        return
    if all(tool.found for tool in tools):
        return
    parent_tool_root_dir = os.path.abspath(
        os.path.join(parent_tool.exec_path, "..")
    )
    search_dirs = [parent_tool_root_dir]
    if recursive:
        for root, subdirs, _ in os.walk(parent_tool_root_dir):
            for subdir in subdirs:
                search_dirs.append(os.path.join(root, subdir))
    search_dirs = os.pathsep.join(search_dirs)

    update_name = parent_tool.exec_name.upper()
    for tool in tools:
        tool._update(update_name, search_dirs)


GLSLC_EXEC = _find_executable("glslc", "GLSLC_PATH")
SPIRV_DIS_EXEC = _find_executable("spirv-dis", "SPIRV_DIS_PATH")
SPIRV_CROSS_EXEC = _find_executable("spirv-cross", "SPIRV_CROSS_PATH")
DXC_EXEC = _find_executable("dxc", "DXC_PATH")
RGA_EXEC = _find_executable("rga", "RGA_PATH")
NAGA_EXEC = _find_executable("naga", "NAGA_PATH")
TINT_EXEC = _find_executable("tint", "TINT_PATH")
DOT_EXEC = _find_executable("dot", "DOT_PATH")

_use_tool_for_missing_tools(
    RGA_EXEC,
    True,
    DXC_EXEC,
    SPIRV_DIS_EXEC,
    SPIRV_CROSS_EXEC,
)

_use_tool_for_missing_tools(
    GLSLC_EXEC,
    False,
    SPIRV_DIS_EXEC,
    DXC_EXEC,
)


SUPPORT_GLSL_TO_SPIRV = GLSLC_EXEC.found
SUPPORT_HLSL_TO_SPIRV = DXC_EXEC.found
SUPPORT_WGSL_TO_SPIRV = NAGA_EXEC.found or TINT_EXEC.found

SUPPORT_SPIRV_TO_GLSL = SPIRV_CROSS_EXEC.found
SUPPORT_SPIRV_TO_HLSL = SPIRV_CROSS_EXEC.found
SUPPORT_SPIRV_TO_WGSL = NAGA_EXEC.found or TINT_EXEC.found

SUPPORT_VIEW_SPIRV = SPIRV_DIS_EXEC.found
SUPPORT_AMD_ASM = RGA_EXEC.found
