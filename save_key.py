"""
Один раз сохраняет ваш API-ключ IBM Quantum на компьютере.

Запуск:
  python save_key.py                 ключ возьмётся из apikey.json рядом со скриптом,
                                     а если файла нет — скрипт попросит вставить ключ
  python save_key.py --file путь\\к\\apikey.json

Ключ сохраняется в служебный файл Qiskit в вашей домашней папке
(Windows: C:\\Users\\<вы>\\.qiskit\\qiskit-ibm.json). После этого cats.py
находит его сам, и ключ больше нигде в коде не нужен.
"""

import argparse
import json
import sys
from getpass import getpass
from pathlib import Path

from _venv import ensure_project_venv, missing_libs_exit

ensure_project_venv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_key_from_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for field in ("apikey", "apiKey", "api_key", "token"):
        if data.get(field):
            return data[field].strip()
    sys.exit(f"В файле {path} не нашлось поля 'apikey'. Проверьте, что это файл ключа IBM.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Сохранить API-ключ IBM Quantum")
    ap.add_argument("--file", default="apikey.json", help="файл с ключом (по умолчанию apikey.json)")
    args = ap.parse_args()

    key_file = Path(args.file)
    if key_file.exists():
        key = read_key_from_json(key_file)
        print(f"Ключ взят из файла {key_file}.")
    else:
        print("Файл apikey.json не найден — вставьте ключ вручную.")
        print("(Ctrl+V или правая кнопка мыши. Символы при вводе не отображаются — так и задумано.)")
        key = getpass("API-ключ: ").strip()

    if len(key) < 20:
        sys.exit("Похоже, это не ключ: он слишком короткий. Скопируйте его ещё раз целиком.")

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as e:
        missing_libs_exit(e)

    QiskitRuntimeService.save_account(
        token=key,
        plans_preference=["open"],   # бесплатный план Open
        set_as_default=True,
        overwrite=True,              # можно запускать повторно, если ключ поменялся
    )
    print("Ключ сохранён. Проверяю подключение к IBM...")

    try:
        service = QiskitRuntimeService()
        names = sorted(b.name for b in service.backends(simulator=False, operational=True))
    except Exception as e:  # noqa: BLE001 — показываем новичку понятную ошибку
        sys.exit(f"Ключ сохранён, но подключиться не удалось:\n  {e}\n"
                 "Проверьте интернет и что ключ скопирован целиком (см. README → «Если что-то пошло не так»).")

    print("Готово! Вам доступны квантовые процессоры:")
    for n in names:
        print("  •", n)
    print("\nТеперь можно запускать:  python cats.py --backend ibm")
    if key_file.exists():
        print(f"\nВажно: файл {key_file} больше не нужен. Удалите его или уберите туда, где его никто не увидит.")


if __name__ == "__main__":
    main()
