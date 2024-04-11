from gui import global_var as g
from gui.modules.base_module import BaseModule


class ProgramModule(BaseModule):
    cached_programs = {}

    @classmethod
    def m_init(cls):
        super().m_init()

    @classmethod
    def load_program(cls, program_path, force_load=False):
        if not force_load and program_path in cls.cached_programs:
            return cls.cached_programs[program_path]
        prog = g.mWindowEvent.load_program(program_path)
        cls.cached_programs[program_path] = prog
        return prog
