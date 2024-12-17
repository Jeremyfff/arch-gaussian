import logging
import os.path

import moderngl
from moderngl_window.exceptions import ImproperlyConfigured
from moderngl_window.loaders.base import BaseLoader
from moderngl_window.meta import ProgramDescription
from moderngl_window.opengl import program
from moderngl_window.opengl.program import ShaderSource, ShaderError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_meta(program_path) -> ProgramDescription:
    return ProgramDescription(
        path=program_path,
        vertex_shader=None,
        geometry_shader=None,
        fragment_shader=None,
        tess_control_shader=None,
        tess_evaluation_shader=None,
        defines=None,
        varyings=None,
    )


def load_program(program_path) -> moderngl.Program:
    meta = ProgramDescription(
        path=program_path,
        vertex_shader=None,
        geometry_shader=None,
        fragment_shader=None,
        tess_control_shader=None,
        tess_evaluation_shader=None,
        defines=None,
        varyings=None,
    )
    loader = Loader(meta)
    return loader.load()


def load_shader(program_path) -> program.ProgramShaders:
    meta = ProgramDescription(
        path=program_path,
        vertex_shader=None,
        geometry_shader=None,
        fragment_shader=None,
        tess_control_shader=None,
        tess_evaluation_shader=None,
        defines=None,
        varyings=None,
    )
    loader = Loader(meta)
    return loader.load_shader()


class Loader(BaseLoader):
    kind = "single"

    def load(self) -> moderngl.Program:
        """Loads a shader program from a single glsl file.

        Returns:
            moderngl.Program: The Program instance
        """
        shaders = self.load_shader()
        prog = shaders.create()

        # Wrap the program if reloadable is set
        if self.meta.reloadable:
            # Disable reload flag so reloads will return Program instances
            self.meta.reloadable = False
            # Wrap it ..
            prog = program.ReloadableProgram(self.meta, prog)

        return prog

    def load_shader(self) -> program.ProgramShaders:
        self.meta.resolved_path, source = self._load_source(self.meta.path)
        shaders = program.ProgramShaders.from_single(self.meta, source)

        # shaders.handle_includes(self._load_source)
        # we use overloaded shader handle includes function instead
        Loader._overloaded_shader_handle_includes(shaders, self._load_source, self.meta.path)

        return shaders

    def _load_source(self, path):
        """Finds and loads a single source file.

        Args:
            path: Path to resource
        Returns:
            Tuple[resolved_path, source]: The resolved path and the source
        """
        resolved_path = self.find_program(path)
        if not resolved_path:
            raise ImproperlyConfigured("Cannot find program '{}'".format(path))

        logger.info(f"Loading: {path} (using custom loader)")

        with open(str(resolved_path), "r") as fd:
            return resolved_path, fd.read()

    @staticmethod
    def _overloaded_shader_handle_includes(shader: program.ProgramShaders, load_source_func, root_path):
        """Resolves ``#include`` preprocessors

                Args:
                    load_source_func (func): A function for finding and loading a source
                """
        if shader.vertex_source:
            # shader.vertex_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.vertex_source, load_source_func, root_path)
        if shader.geometry_source:
            # shader.geometry_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.geometry_source, load_source_func, root_path)
        if shader.fragment_source:
            # shader.fragment_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.fragment_source, load_source_func, root_path)
        if shader.tess_control_source:
            # shader.tess_control_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.tess_control_source, load_source_func, root_path)
        if shader.tess_evaluation_source:
            # shader.tess_evaluation_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.tess_evaluation_source, load_source_func, root_path)
        if shader.compute_shader_source:
            # shader.compute_shader_source.handle_includes(load_source_func)
            Loader._overloaded_source_handle_includes(shader.compute_shader_source, load_source_func, root_path)

    @staticmethod
    def _overloaded_source_handle_includes(self: program.ShaderSource, load_source_func, root_path, depth=0, source_id=0):
        """Inject includes into the shader source.
        This happens recursively up to a max level in case the users has
        circular includes. We also build up a list of all the included
        sources in the root shader.

        Args:
            load_source_func (func): A function for finding and loading a source
            depth (int): The current include depth (increase by 1 for every call)
        """
        if depth > 100:
            raise ShaderError(
                "Reaching an include depth of 100. You probably have circular includes"
            )

        current_id = source_id
        while True:
            for nr, line in enumerate(self._lines):
                line = line.strip()
                if line.startswith("#include"):
                    include_path = line[9:]
                    include_path = include_path.strip()
                    if include_path.startswith('"') and include_path.endswith('"'):
                        include_path = include_path.strip('"')
                    elif include_path.startswith("'") and include_path.endswith("'"):
                        include_path = include_path.strip("'")
                    if include_path.startswith("./"):
                        include_path = include_path[2:]
                    dir_path = os.path.dirname(root_path)
                    path = os.path.join(dir_path, include_path)
                    try:
                        _, source = load_source_func(path)
                    except Exception as e:
                        logging.warning(f"failed to load shader at {path}")
                        path = include_path
                        logging.info(f"trying to reload shader from {path}")
                        _, source = load_source_func(path)

                    current_id += 1
                    source = ShaderSource(
                        None,
                        path,
                        source,
                        defines=self._defines,
                        id=current_id,
                        root=False,
                    )
                    Loader._overloaded_source_handle_includes(source, load_source_func, path, depth=depth + 1, source_id=current_id)
                    # source.handle_includes(
                    #     load_source_func, path, depth=depth + 1, source_id=current_id
                    # )
                    self._lines = self.lines[:nr] + source.lines + self.lines[nr + 1:]
                    self._source_list += source.source_list
                    current_id = self._source_list[-1].id
                    break
            else:
                break
