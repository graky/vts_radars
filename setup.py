import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["qtpy", "json", "pyqtlet2", "shapely", "sklearn", "pandas", "fastdtw", "scipy", "numpy", "win32api", "win32com", "sqlalchemy"],
    "excludes": ["tkinter"],
    "include_files": [
        "ships_vts.db",
        # Укажите путь к необходимым DLL-файлам, если они известны
        "vcomp140.dll"
        # Добавьте другие необходимые файлы, например, иконки, дополнительные библиотеки и т.д.
    ],
}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ShipProject2",
    version="0.3",
    description="smth",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
