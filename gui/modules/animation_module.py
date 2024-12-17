import imgui, importlib, inspect, logging, math, time, uuid
from typing import Optional, Type
from deprecated import deprecated

from gui.components import c
from gui.global_app_state import g
from gui.modules import BaseModule


class AnimationModule(BaseModule):
    _Ease: Optional[Type["Ease"]] = None

    @classmethod
    def m_init(cls):
        cls._Ease = Ease


class Ease:
    """
    Warning: 未经验证的方法，由ChatGpt自动生成，使用时请注意
    """
    @staticmethod
    def Linear(t):
        return t

    @staticmethod
    def QuadraticIn(t):
        return t * t

    @staticmethod
    def QuadraticOut(t):
        return 1 - Ease.QuadraticIn(1 - t)

    @staticmethod
    def QuadraticInOut(t):
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * Ease.QuadraticIn(1 - t)

    @staticmethod
    def CubicIn(t):
        return t * t * t

    @staticmethod
    def CubicOut(t):
        return 1 - Ease.CubicIn(1 - t)

    @staticmethod
    def CubicInOut(t):
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - 4 * Ease.CubicIn(1 - t)

    @staticmethod
    def SineIn(t):
        return 0.5 - 0.5 * math.cos(t * math.pi)

    @staticmethod
    def SineOut(t):
        return 1 - Ease.SineIn(1 - t)

    @staticmethod
    def SineInOut(t):
        return 0.5 - 0.5 * math.cos(t * math.pi)

    @staticmethod
    def ExponentialIn(t):
        return 2 ** (10 * (t - 1))

    @staticmethod
    def ExponentialOut(t):
        return 1 - Ease.ExponentialIn(1 - t)

    @staticmethod
    def ExponentialInOut(t):
        if t < 0.5:
            return 0.5 * 2 ** (10 * (2 * t - 1))
        else:
            return 1 - 0.5 * 2 ** (-10 * (2 * t - 1))


class Tween:
    """Node Editor Tween"""
    __all_tweens: dict[str:"Tween"] = {}

    @staticmethod
    def start_animation(name, start, end, duration, function, delay=0.0, *args, **kwargs):

        """
        start a float animation. If the name already exists, the animation will be reset
        :param name: animation name
        :param start: start value, float
        :param end: end value, float
        :param duration: duration time in second
        :param function: callable function witch take one float variable
        :param delay: delay time in second
        :return: None
        Example:
        Tween.start_animation(
            'my_fade_animation',start=0.0, end=1.0,duration=1.0, function=set_alpha
        )
        def set_alpha(alpha):
            my_obj.alpha = alpha
        then call:
        step_animation('my_fade_animation')
        """
        if name in Tween.__all_tweens:
            tween = Tween.__all_tweens[name]
            tween.reset()
            return
        tween: 'Tween' = Tween(name, start, end, duration, function, delay, *args, **kwargs)
        Tween.__all_tweens[name] = tween

    @staticmethod
    def step_animation(name):
        if name not in Tween.__all_tweens:
            return
        tween: 'Tween' = Tween.__all_tweens[name]
        tween.step()

    @staticmethod
    def reset_animation(name):
        if name not in Tween.__all_tweens:
            return
        tween: 'Tween' = Tween.__all_tweens[name]
        tween.reset()

    @staticmethod
    def stop_animation(name):
        if name in Tween.__all_tweens:
            Tween.__all_tweens.pop(name)

    @staticmethod
    def is_animation_running(name):
        if name not in Tween.__all_tweens:
            return False
        tween: 'Tween' = Tween.__all_tweens[name]
        curr_time = time.time()
        if curr_time < tween.start_time:
            return False
        return True

    def __init__(self, name, start, end, duration, function, delay=0.0, ease=Ease.Linear):
        self.name = name
        self.start = start
        self.end = end
        self.duration = duration
        self.start_time = time.time() + delay
        self.function = function
        self.delay = delay
        self.ease = ease

    def get_value(self):
        curr_time = time.time()
        if curr_time < self.start_time:
            return self.start
        if curr_time >= self.start_time + self.duration:
            return self.end
        t = (curr_time - self.start_time) / self.duration
        t = self.ease(t)

        value = t * (self.end - self.start) + self.start
        return value

    def step(self):
        curr_time = time.time()
        if curr_time < self.start_time:
            return
        if curr_time > self.start_time + self.duration:
            self.function(self.get_value())
            Tween.stop_animation(self.name)
            return
        self.function(self.get_value())

    def reset(self):
        self.start_time = time.time() + self.delay


__runtime__ = True
if not __runtime__:
    # for type hint
    from gui.contents import pages

    raise Exception("this code will never be reached")


class AnimatedPageGroup:
    def __init__(self, vertical=True):

        self.first_shown = True
        self.curr_page_key: Optional[str] = None
        self.last_page_key: Optional[str] = None
        self.pages: dict[str:pages.BasePage] = {}
        self.page_levels: dict[str: int] = {}
        self.page_pos_from: dict[str: int] = {}
        self.page_pos_to: dict[str:int] = {}
        self.curr_page_pos: dict[str: int] = {}
        self.curr_page_alpha: dict[str: float] = {}
        self.vertical = vertical
        self.level_stack = {}
        self.name = str(uuid.uuid4())

    @deprecated(reason="This function is deprecated. Please use add_page_obj instead.")
    def add_page(self, page_obj):
        self.add_page_obj(page_obj)

    def add_page_obj(self, page_obj):
        page_obj.set_parent_page_group(self)

        page_key = page_obj.page_name
        page_level = page_obj.page_level
        page_pos_from = page_obj.page_pos_from
        page_pos_to = page_obj.page_pos_to

        is_first = len(self.pages) == 0
        self.pages[page_key] = page_obj
        self.page_levels[page_key] = page_level
        self.page_pos_from[page_key] = page_pos_from
        self.page_pos_to[page_key] = page_pos_to

        if is_first:
            self.curr_page_key = page_key
            self.last_page_key = page_key
            self.curr_page_pos[page_key] = page_pos_to
            self.curr_page_alpha[page_key] = 1.0
            self.level_stack[page_level] = page_key
        else:
            self.curr_page_pos[page_key] = page_pos_from
            self.curr_page_alpha[page_key] = 0.0

    def page_wrapper(self, key, page):
        Tween.step_animation(f'{key}_fade_in')
        Tween.step_animation(f'{key}_fade_out')
        Tween.step_animation(f'{key}_fade_alpha_in')
        Tween.step_animation(f'{key}_fade_alpha_out')
        if self.curr_page_alpha[key] == 0:
            return
        self.push_alpha(self.curr_page_alpha[key])
        if self.vertical:
            imgui.set_cursor_pos_y(self.curr_page_pos[key])
        else:
            imgui.set_cursor_pos_x(self.curr_page_pos[key])
        imgui.push_id(str(key))
        page.__call__()
        imgui.pop_id()
        self.pop_alpha()

    def show(self):
        imgui.push_style_color(imgui.COLOR_CHILD_BACKGROUND, 0, 0, 0, 0.0)
        c.begin_child(f"child_{self.name}", imgui.get_content_region_available_width(), border=False)
        imgui.pop_style_color()
        if self.first_shown:
            # pos = imgui.get_cursor_pos_y() if self.vertical else imgui.get_cursor_pos_x()
            # for key in self.page_pos_to.keys():
            #     self.page_pos_to[key] = pos
            self.curr_page_pos[self.curr_page_key] = self.page_pos_to[self.curr_page_key]
            self.first_shown = False
        for key, page in self.pages.items():
            self.page_wrapper(key, page)
        imgui.end_child()

    def switch_page(self, target_page):
        if target_page == self.curr_page_key:
            return
        self.last_page_key = self.curr_page_key
        self.curr_page_key = target_page
        duration = 0.3
        ease = Ease.CubicOut
        target_page_from = self.page_pos_from[target_page]
        target_page_to = self.page_pos_to[target_page]
        last_page_from = self.page_pos_from[self.last_page_key]
        last_page_to = self.page_pos_to[self.last_page_key]
        if self.page_levels[target_page] >= self.page_levels[self.last_page_key]:
            # 新页面的级别比原来页面的小， 或page级别相同
            last_page_from *= -1
            self.level_stack[self.page_levels[target_page]] = target_page

        else:
            # 新页面的级别比原来页面的大
            target_page_from *= -1
            # pop levels
            levels_to_pop = [level for level in self.level_stack.keys() if level > self.page_levels[target_page]]
            for key in levels_to_pop:
                self.level_stack.pop(key)
            self.level_stack[self.page_levels[target_page]] = target_page

        Tween.start_animation(f'{target_page}_fade_in',
                              target_page_from,
                              target_page_to,
                              duration,
                              lambda x: self.fade_func(target_page, x),
                              ease=ease)
        Tween.start_animation(f'{self.last_page_key}_fade_out',
                              last_page_to,
                              last_page_from,
                              duration,
                              lambda x: self.fade_func(self.last_page_key, x),
                              ease=ease)
        Tween.start_animation(f'{target_page}_fade_alpha_in',
                              0.0,
                              1.0,
                              duration,
                              lambda x: self.alpha_fade_func(target_page, x),
                              ease=ease)
        Tween.start_animation(f'{self.last_page_key}_fade_alpha_out',
                              1.0,
                              0.0,
                              duration,
                              lambda x: self.alpha_fade_func(self.last_page_key, x),
                              ease=ease)

    def switch_page_obj(self, page_obj):
        self.switch_page(page_obj.page_name)

    def fade_func(self, page, pos):
        self.curr_page_pos[page] = pos

    def alpha_fade_func(self, page, alpha):
        self.curr_page_alpha[page] = alpha

    def set_alpha(self, color, alpha):
        return color[0], color[1], color[2], color[3] * alpha

    def push_alpha(self, alpha):
        for color in range(0, imgui.COLOR_COUNT):
            imgui.push_style_color(color, *self.set_alpha(g.mImguiStyle.colors[color], alpha))

    def pop_alpha(self):
        imgui.pop_style_color(imgui.COLOR_COUNT)

    def get_level_stack(self):
        return str(self.level_stack)

    def show_level_guide(self):
        page_clicked = None
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (0, 0))
        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 0)
        imgui.push_style_color(imgui.COLOR_BUTTON, 0, 0, 0, 0)
        length = len(self.level_stack)
        for level, page in self.level_stack.items():
            if level != 0:
                imgui.same_line()
            if level < length - 1:
                text = f'{page} >'
            else:
                text = page
            if imgui.button(text):
                page_clicked = page
        imgui.pop_style_var(2)
        imgui.pop_style_color()
        imgui.same_line()
        imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + imgui.get_content_region_available_width() - imgui.get_frame_height_with_spacing())
        if c.icon_button('more-2-fill'):
            imgui.open_popup('pages settings')
        if imgui.begin_popup('pages settings'):
            if (self.curr_page_key is not None) and (self.pages[self.curr_page_key].cell_module is not None):

                clicked, _ = imgui.menu_item("Expand All")
                if clicked:
                    self.pages[self.curr_page_key].cell_module.expand_all()
                clicked, _ = imgui.menu_item("Collapse All")
                if clicked:
                    self.pages[self.curr_page_key].cell_module.collapse_all()
                imgui.separator()
            clicked, _ = imgui.menu_item('Reload All Pages')
            if clicked:
                self.reload_all_pages(preserve_data=False)
            clicked, _ = imgui.menu_item('Reload All Pages (Preserve Data)')
            if clicked:
                self.reload_all_pages(preserve_data=True)
            imgui.end_popup()
        imgui.separator()
        if page_clicked:
            self.switch_page(page_clicked)

    def reload_all_pages(self, preserve_data=False):
        from gui.contents import pages
        logging.info(f'[{self.__class__.__name__}] reloading all pages')
        org_curr_page = self.curr_page_key
        preserved_data = {}
        if preserve_data:
            preserved_data = pages.cache_data()
        pages.reload_pages()
        importlib.reload(pages)
        if preserve_data:
            pages.restore_data(preserved_data)

        caller_frame = inspect.currentframe().f_back.f_back
        caller_class = caller_frame.f_locals.get('cls', None)
        base_class_name = caller_class.__base__.__name__
        logging.info(f'[{self.__class__.__name__}] base class name: {base_class_name}')
        if base_class_name == 'BaseContent':
            caller_class.c_init()  # 如果继承自BaseContent，则可以运行c_init()方法
            if 'page_group' in dir(caller_class):  # 如果其含有page_group变量
                page_group = getattr(caller_class, 'page_group')
                if page_group is not None:
                    # page_group.switch_page(org_curr_page)
                    pass
