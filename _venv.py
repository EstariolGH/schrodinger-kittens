"""
Чтобы `python cats.py` и `python save_key.py` работали без активации окружения.

Если рядом со скриптом есть папка .venv (её создаёт install.bat), а скрипт
запущен «чужим» Python, — перезапускаем его через Python из .venv.
Если .venv нет и библиотеки не установлены — объясняем, что делать.
"""

import subprocess
import sys
from pathlib import Path


def ensure_project_venv() -> None:
    here = Path(__file__).resolve().parent
    venv = here / ".venv"
    for cand in (venv / "Scripts" / "python.exe", venv / "bin" / "python"):
        if cand.exists():
            if Path(sys.prefix).resolve() != venv.resolve():
                sys.exit(subprocess.call([str(cand), *sys.argv]))
            return


def missing_libs_exit(err: ImportError) -> None:
    sys.exit(
        f"Не найдена библиотека: {err.name}.\n"
        "Сначала установите всё нужное: дважды щёлкните install.bat\n"
        "(или см. README, шаг 4)."
    )
