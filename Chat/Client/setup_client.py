import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ['gui'],
    "include_files": ['gui/'],
}
setup(
    name="GAM_chat_client",
    version="0.1.1",
    description="Тестовый проект",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('client.py',
                            target_name='client.exe',
                            )]
)
