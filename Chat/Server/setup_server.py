import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [],
    "include_files": ['gui_add_user_server.ui', 'gui_main_server.ui'],
}
setup(
    name="GAM_server_client",
    version="0.1.1",
    description="Тестовый проект",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('server.py',
                            target_name='server.exe',
                            )]
)
