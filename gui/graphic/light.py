# -*- coding: utf-8 -*-
# @Author  : Yiheng Feng
# @Time    : 12/11/2024 4:18 PM
# @Function:

class ILight:
    pass


class DirectionalLight(ILight):
    def __init__(self, direction=(0, 0, 1)):
        self.direction = direction
