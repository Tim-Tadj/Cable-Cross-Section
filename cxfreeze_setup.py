import sys
from cx_Freeze import Executable, setup

APP_NAME = "Cable Conduit Fill Simulator"
APP_VERSION = "0.1.0"
UPGRADE_CODE = "{AF5E0BF1-3F34-4C1D-9A89-8529F5CDFE69}"
TARGET_DIR = r"[LocalAppDataFolder]\CableConduitFillSimulator"
TARGET_EXE = "CableSimulation.exe"

includes = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "pygame",
    "pymunk",
    "main",
    "cable",
    "conduit",
    "config",
    "physics",
    "input_handler",
    "calculations",
]

build_exe_options = {
    "includes": includes,
    "include_msvcr": True,
    "zip_include_packages": [],
    "excludes": ["tkinter"],
}

shortcut_table = [
    (
        "DesktopShortcut",
        "DesktopFolder",
        APP_NAME,
        "TARGETDIR",
        f"[TARGETDIR]{TARGET_EXE}",
        None,
        APP_NAME,
        None,
        None,
        None,
        None,
        "TARGETDIR",
    ),
    (
        "StartMenuShortcut",
        "ProgramMenuFolder",
        APP_NAME,
        "TARGETDIR",
        f"[TARGETDIR]{TARGET_EXE}",
        None,
        APP_NAME,
        None,
        None,
        None,
        None,
        "TARGETDIR",
    ),
]

bdist_msi_options = {
    "upgrade_code": UPGRADE_CODE,
    "add_to_path": False,
    "all_users": False,
    "initial_target_dir": TARGET_DIR,
    "target_name": "CableConduitFillSimulator",
    "data": {"Shortcut": shortcut_table},
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        "cable_gui.py",
        base=base,
        target_name=TARGET_EXE,
    )
]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="Cable conduit fill simulation GUI and physics sandbox.",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
