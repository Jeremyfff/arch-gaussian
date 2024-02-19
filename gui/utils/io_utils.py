import pyglet
import win32ui
import tkinter as tk
from tkinter import filedialog


def open_file_dialog():
    dlg = win32ui.CreateFileDialog(1)  # 参数 1 表示打开文件对话框
    dlg.SetOFNInitialDir('C://')  # 设置打开文件对话框中的初始显示目录
    dlg.DoModal()
    filename = dlg.GetPathName()
    return filename


def open_folder_dialog():
    # 创建 Tkinter 根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口
    # 弹出文件夹选择框
    selected_folder = filedialog.askdirectory()
    return selected_folder


if __name__ == '__main__':
    # dlg = win32ui.CreateFileDialog(1)  # 参数 1 表示打开文件对话框
    # dlg.SetOFNInitialDir('C://')  # 设置打开文件对话框中的初始显示目录
    # dlg.DoModal()
    # filename = dlg.GetPathName()
    # print(filename)
    import win32gui
    from win32com.shell import shell, shellcon

    desktop_pidl = shell.SHGetFolderLocation(0, shellcon.CSIDL_DESKTOP, 0, 0)
    pidl, display_name, image_list = shell.SHBrowseForFolder(
        win32gui.GetDesktopWindow(),
        desktop_pidl,
        "Choose a folder",
        0,
        None,
        None
    )
    print
    shell.SHGetPathFromIDList(pidl)
