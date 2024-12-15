# build_exe.py
import subprocess
import shutil
import os
import winshell
from win32com.client import Dispatch


def create_executable():
    # Run PyInstaller to create the executable file
    subprocess.call(['pyinstaller', '--onefile', '--windowed', 'main.py'])


def move_to_program_folder():
    program_folder = os.path.expanduser('~/MyPrograms/IgroMuha')
    if not os.path.exists(program_folder):
        os.makedirs(program_folder)

    exe_path = os.path.join('dist', 'main.exe')
    if os.path.exists(exe_path):
        new_exe_path = os.path.join(program_folder, 'IgroMuha 3.2.exe')
        shutil.move(exe_path, new_exe_path)
        print(f'Executable file moved to program folder: {new_exe_path}')
        return new_exe_path
    else:
        print(f'Executable file not found: {exe_path}')
        return None


def create_shortcut(exe_path):
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'IgroMuha.lnk')

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = exe_path
    shortcut.WorkingDirectory = os.path.dirname(exe_path)
    shortcut.IconLocation = exe_path
    shortcut.save()

    print(f'Shortcut created on desktop: {shortcut_path}')


if __name__ == "__main__":
    create_executable()
    exe_path = move_to_program_folder()
    if exe_path:
        create_shortcut(exe_path)