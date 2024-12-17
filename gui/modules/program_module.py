# import logging
#
# import moderngl
# from moderngl_window.exceptions import ImproperlyConfigured
# from moderngl_window.loaders.base import BaseLoader
# from moderngl_window.meta import ProgramDescription
# from moderngl_window.opengl import program
#
# from gui.modules.base_module import BaseModule
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
#
# class Loader(BaseLoader):
#     kind = "single"
#
#     def load(self) -> moderngl.Program:
#         """Loads a shader program from a single glsl file.
#
#         Returns:
#             moderngl.Program: The Program instance
#         """
#         shaders = self.load_shader()
#         prog = shaders.create()
#
#         # Wrap the program if reloadable is set
#         if self.meta.reloadable:
#             # Disable reload flag so reloads will return Program instances
#             self.meta.reloadable = False
#             # Wrap it ..
#             prog = program.ReloadableProgram(self.meta, prog)
#
#         return prog
#
#     def load_shader(self) -> program.ProgramShaders:
#         self.meta.resolved_path, source = self._load_source(self.meta.path)
#         shaders = program.ProgramShaders.from_single(self.meta, source)
#         shaders.handle_includes(self._load_source)
#         return shaders
#
#     def _load_source(self, path):
#         """Finds and loads a single source file.
#
#         Args:
#             path: Path to resource
#         Returns:
#             Tuple[resolved_path, source]: The resolved path and the source
#         """
#         resolved_path = self.find_program(path)
#         if not resolved_path:
#             raise ImproperlyConfigured("Cannot find program '{}'".format(path))
#
#         logger.info(f"Loading: {path} (using custom loader)")
#
#         with open(str(resolved_path), "r") as fd:
#             return resolved_path, fd.read()
#
#
# class ProgramModule(BaseModule):
#     @classmethod
#     def m_init(cls):
#         super().m_init()
#         # use custom Loader to replace default Loaders
#         from moderngl_window.conf import settings
#         settings.PROGRAM_LOADERS.insert(0, "gui.modules.program_module.Loader")
#
#     @classmethod
#     def load_program(cls, program_path) -> moderngl.Program:
#         meta = ProgramDescription(
#             path=program_path,
#             vertex_shader=None,
#             geometry_shader=None,
#             fragment_shader=None,
#             tess_control_shader=None,
#             tess_evaluation_shader=None,
#             defines=None,
#             varyings=None,
#         )
#         loader = Loader(meta)
#         return loader.load()
#
#     @classmethod
#     def load_shader(cls, program_path) -> program.ProgramShaders:
#         meta = ProgramDescription(
#             path=program_path,
#             vertex_shader=None,
#             geometry_shader=None,
#             fragment_shader=None,
#             tess_control_shader=None,
#             tess_evaluation_shader=None,
#             defines=None,
#             varyings=None,
#         )
#         loader = Loader(meta)
#         return loader.load_shader()
