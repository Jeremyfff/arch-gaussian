import logging
from enum import Enum
from typing import Optional

import imgui

from gui.components import c
from gui.global_app_state import g


class ProgressState(Enum):
    Prepare = 0
    Running = 1
    Complete = 2
    Error = 3
    NotFound = 4


_state2str: dict = {
    0: "Prepare",
    1: "Running",
    2: "Complete",
    3: "Error",
    4: "NotFound"
}

_ctx_dict: dict[str: "ProgressContex"] = {}
_active_ctx_dict: dict[str: "ProgressContex"] = {}


class ProgressContex:
    def __init__(self, ctx_name: str, display_name: str = None):
        self._ctx_name: str = ctx_name
        self._display_name: str = display_name if display_name is not None else ctx_name
        self._total: int = 0
        self._curr: int = 0
        self._state: ProgressState = ProgressState.Prepare
        self.push_state(ProgressState.Prepare)
        from gui.modules import EventModule
        self._event_module = EventModule
        self._event_module.on_progress_ctx_change()

    def __del__(self):
        if self.ctx_name in _active_ctx_dict:
            _active_ctx_dict.pop(self.ctx_name)
        if self.ctx_name in _ctx_dict:
            _ctx_dict.pop(self.ctx_name)
        self._event_module.on_progress_ctx_change()

    def new_progress(self, total=100) -> None:
        assert total > 0

        self._curr = 0
        self._total = total
        self.push_state(ProgressState.Running)
        self._event_module.on_progress_ctx_change()

    def update(self, n=1) -> None:
        self._curr += n
        if self._curr >= self._total:
            self.push_state(ProgressState.Complete)

    def set_curr(self, curr):
        self._curr = curr
        if self._curr >= self._total:
            self.push_state(ProgressState.Complete)

    def push_state(self, state: ProgressState) -> None:
        self._state = state
        # Complete
        if self._state == ProgressState.Complete:
            self._curr = self._total
            if self.ctx_name in _active_ctx_dict:
                _active_ctx_dict.pop(self.ctx_name)

        # Error or Not Found
        elif self._state == ProgressState.Error or self._state == ProgressState.NotFound:
            if self.ctx_name in _active_ctx_dict:
                _active_ctx_dict.pop(self.ctx_name)

        # Running
        elif self._state == ProgressState.Running:
            _active_ctx_dict[self.ctx_name] = self
            _ctx_dict[self.ctx_name] = self
        # Prepare
        elif self._state == ProgressState.Prepare:
            _active_ctx_dict[self.ctx_name] = self
            _ctx_dict[self.ctx_name] = self

    def draw_progress_bar(self, width=None, height=None, suffix="default"):
        if width is None:
            width = imgui.get_content_region_available_width()
        if height is None:
            height = 10 * g.global_scale
        c.progress_bar(f"{self._ctx_name}_{suffix}", width, height, progress=self.progress, state_value=self._state.value)

    def draw_text(self):
        c.gray_text(f"{self._display_name} {_state2str[self.state.value]} [{round(self.progress * 100)}%]")

    @property
    def ctx_name(self):
        return self._ctx_name

    @property
    def display_name(self):
        return self._display_name

    @property
    def progress(self) -> float:
        if self._total == 0:
            return -1
        else:
            return float(self._curr) / float(self._total)

    @property
    def state(self) -> ProgressState:
        return self._state


def p_create_contex(ctx_name, display_name=None) -> ProgressContex:
    if ctx_name in _ctx_dict:
        logging.warning(f"contex {ctx_name} already exist, use exist one")
        return _ctx_dict[ctx_name]

    ctx = ProgressContex(ctx_name, display_name)
    return ctx


def p_get_contex(ctx_name) -> Optional[ProgressContex]:
    if ctx_name not in _ctx_dict:
        # logging.error(f"{ctx_name} not found in _ctx_dict")
        return None
    return _ctx_dict[ctx_name]


def p_remove_contex(ctx_name) -> None:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    del ctx


def p_has_contex(ctx_name) -> bool:
    return ctx_name in _ctx_dict


def p_new_progress(ctx_name, total: int) -> None:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.new_progress(total)


def p_update(ctx_name, n=1) -> None:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.update(n)


def p_set_curr(ctx_name, curr) -> None:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.set_curr(curr)


def p_get_progress(ctx_name) -> float:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return 0
    return ctx.progress


def p_get_state(ctx_name) -> ProgressState:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return ProgressState.NotFound
    return ctx.state


def p_set_state(ctx_name, state: ProgressState) -> None:
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.push_state(state)


def p_draw_progress_bar(ctx_name, width=None, height=None, suffix="default"):
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.draw_progress_bar(width, height, suffix)


def p_draw_progress_text(ctx_name):
    ctx = p_get_contex(ctx_name)
    if not ctx:
        return
    ctx.draw_text()


def p_get_all_ctx() -> dict[str: ProgressContex]:
    return _ctx_dict


def p_get_all_active_ctx() -> dict[str: ProgressContex]:
    return _active_ctx_dict


def p_get_mean_progress() -> float:
    ctxs = p_get_all_active_ctx().values()
    c = 0
    s = 0.0
    for ctx in ctxs:
        ctx: ProgressContex = ctx
        s += ctx.progress
        c += 1
    if c == 0:
        return 0
    mean = s / c
    return mean


def p_get_num_active_progress() -> int:
    return len(p_get_all_active_ctx().values())
