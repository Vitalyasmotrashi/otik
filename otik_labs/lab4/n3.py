#!/usr/bin/env python3
"""
Л4.№3 — Универсальный декодер

Проверяет сигнатуру, версию и код алгоритма, затем вызывает соответствующий декодер:
- алг. 0: декодер из Л3.№3 (без сжатия)
- алг. 1: декодер Хаффмана из Л4.№1
- алг. 2: декодер Шеннона-Фано из Л4.№6

CLI:
  decode <archive> <output>
"""
from __future__ import annotations
import struct
import sys
import os
import importlib.util

SIGNATURE = b"SOBSTV"

def read_header(archive_path):
    """Прочитать заголовок и определить алгоритм."""
    with open(archive_path, "rb") as f:
        header = f.read(16)
        if len(header) < 16:
            raise ValueError("archive too short")
        
        sig = header[:6]
        ver = struct.unpack("<H", header[6:8])[0]
        
        # проверяем формат: если байт 8 - это часть uint64 длины (алгоритм 0),
        # или это байт алгоритма (новые форматы)
        # для старого формата: байты 8-15 это uint64 длина
        # для нового: байт 8 - алгоритм, байты 9-15 (7 байт) - длина
        
        # пробуем определить по размеру файла
        file_size = os.path.getsize(archive_path)
        
        # если читаем как старый формат (алг=0)
        n_old = struct.unpack("<Q", header[8:16])[0]
        if file_size == 16 + n_old:
            # это старый формат без поля алгоритма
            return sig, ver, 0
        
        # иначе это новый формат с полем алгоритма
        alg = header[8]
        
        return sig, ver, alg

def decode(archive_path: str, output_path: str):
    """Универсальный декодер."""
    sig, ver, alg = read_header(archive_path)
    
    # проверяем сигнатуру
    if sig != SIGNATURE:
        raise ValueError(f"bad signature: expected {SIGNATURE}, got {sig}")
    
    # проверяем версию
    if ver != 0:
        raise ValueError(f"unsupported version: {ver}")
    
    # выбираем декодер по алгоритму
    if alg == 0:
        # без сжатия - декодер из Л3
        lab3_path = os.path.join(os.path.dirname(__file__), "..", "lab3", "n1.py")
        spec = importlib.util.spec_from_file_location("lab3_n1", lab3_path)
        lab3_n1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab3_n1)
        lab3_n1.decode(archive_path, output_path)
        print(f"Decoded with algorithm 0 (no compression)")
    elif alg == 1:
        # Хаффман
        lab4_n1_path = os.path.join(os.path.dirname(__file__), "n1.py")
        spec = importlib.util.spec_from_file_location("lab4_n1", lab4_n1_path)
        lab4_n1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab4_n1)
        lab4_n1.decode(archive_path, output_path)
        print(f"Decoded with algorithm 1 (Huffman)")
    elif alg == 2:
        # Шеннон-Фано
        lab4_n6_path = os.path.join(os.path.dirname(__file__), "n6.py")
        spec = importlib.util.spec_from_file_location("lab4_n6", lab4_n6_path)
        lab4_n6 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab4_n6)
        lab4_n6.decode(archive_path, output_path)
        print(f"Decoded with algorithm 2 (Shannon-Fano)")
    else:
        raise ValueError(f"unknown algorithm: {alg}")

def main(argv):
    if len(argv) < 3:
        print("usage: n3.py decode <archive> <output>", file=sys.stderr)
        return 2
    
    cmd = argv[0]
    if cmd != "decode":
        print("usage: n3.py decode <archive> <output>", file=sys.stderr)
        return 2
    
    try:
        decode(argv[1], argv[2])
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
