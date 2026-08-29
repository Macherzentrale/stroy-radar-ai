import os
import glob
import json
import csv

def run_audit():
    print("=" * 50)
    print("STROY-RADAR / AUDIT REPORT (STANDARD LIBS)")
    print("=" * 50)
    
    # 1. Списък с файлове
    files = os.listdir('.')
    print(f"\nОбщ брой файлове: {len(files)}")
    py_files = glob.glob("*.py")
    json_files = glob.glob("*.json")
    csv_files = glob.glob("*.csv")
    
    print(f"  • Python скриптове ({len(py_files)}): {py_files}")
    print(f"  • JSON фийдове ({len(json_files)}): {json_files}")
    print(f"  • CSV доклади ({len(csv_files)}): {csv_files}")
    
    # 2. Анализ на CSV файлове
    print("\nАНАЛИЗ НА CSV:")
    for c in csv_files:
        try:
            with open(c, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                header = reader[0] if reader else []
                rows_count = len(reader) - 1 if len(reader) > 1 else 0
                print(f"  [+] {c}: {rows_count} реда | Колони: {header}")
        except Exception as e:
            print(f"  [-] Грешка при {c}: {e}")

    # 3. Анализ на JSON файлове
    print("\nАНАЛИЗ НА JSON:")
    for j in json_files:
        try:
            with open(j, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data) if isinstance(data, list) else len(data.keys())
                print(f"  [+] {j}: {count} обекта")
        except Exception as e:
            print(f"  [-] Грешка при {j}: {e}")

    # 4. Преглед на функции в Python скриптовете
    print("\nФУНКЦИИ В PYTHON СКРИПТОВЕТЕ:")
    for p in py_files:
        if p == "audit_project.py":
            continue
        print(f"\n  --- Скрипт: {p} ---")
        try:
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("import ") or stripped.startswith("from "):
                        print(f"    {stripped}")
        except Exception as e:
            print(f"    Грешка: {e}")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    run_audit()
