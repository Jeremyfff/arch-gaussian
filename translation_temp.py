from gui.modules.language_module import LanguageSet

_l: LanguageSet = LanguageSet()
_l.register_translation(english="Folder Settings", chinese="文件夹设置")
_l.register_translation(english="Scroll Settings", chinese="滚动设置")
_l.register_translation(english="3D View Settings", chinese="3D视图设置")
_l.register_translation(english="Advanced Settings", chinese="高级设置")

_l.register_translation(english="Project Repository Folder", chinese="项目仓库文件夹")
_l.register_translation(english="Colmap Executable", chinese="Colmap可执行文件路径")
_l.register_translation(english="Invalid Colmap Executable Path", chinese="非法的Colmap可执行文件路径")
_l.register_translation(english="Auto Search Colmap Executable", chinese="自动搜索Colmap可执行文件路径")

_l.register_translation(english="Move Scroll Speed", chinese="移动物体速度")
_l.register_translation(english="Scale Scroll Speed", chinese="缩放物体速度")
_l.register_translation(english="Rotate Scroll Speed", chinese="旋转物体速度")

_l.register_translation(english="Need Restart", chinese="需要重启")
_l.register_translation(english="Grid Fading Dist", chinese="坐标格网消失距离")
_l.register_translation(english="Sets the gradient disappearance distance of the 3D view grid. Beyond this distance, the coordinate grid will not be visible.", chinese="设置三维视图格网的渐变消失距离。超过该距离，坐标格网将不可见。")
_l.register_translation(english="Sets the z-offset distance of the grid. The purpose of this option is to allow this option to be kept very small.", chinese="设置格网的z轴偏移距离。该选项的目的是允许请将该选项保持在一个很小的数值。")
