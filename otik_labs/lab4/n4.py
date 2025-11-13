#!/usr/bin/env python3
"""
Л4.№4 — Интеллектуальный кодер

Анализирует эффективность сжатия и выбирает:
- алгоритм 1 (Хаффман), если сжатие выгодно
- алгоритм 0 (без сжатия), если ncompr >= n

Флаг --force-algorithm позволяет принудительно использовать заданный алгоритм.

CLI:
  encode <input> <archive> [--force-algorithm=N]
  decode <archive> <output>
"""
from __future__ import annotations
import os
import struct
import sys
import importlib.util

SIGNATURE = b"SOBSTV"
VERSION = 0

# динамический импорт модулей
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base_dir = os.path.dirname(__file__)
huffman_codec = load_module("huffman_codec", os.path.join(base_dir, "n1.py"))


def estimate_huffman_size(input_path):
    """Оценить размер архива Хаффмана без реального сжатия."""
    with open(input_path, "rb") as f:
        data = f.read()
    
    n = len(data)
    if n == 0:
        return 0
    
    # подсчитываем частоты
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    
    # строим дерево и коды
    freqs = huffman_codec.normalize_freqs(counts, n)
    tree = huffman_codec.build_huffman_tree(freqs)
    if tree is None:
        return 16 + 256  # заголовок + таблица
    
    codes = huffman_codec.build_codes(tree)
    
    # считаем длину сжатых данных в битах
    total_bits = 0
    for byte in data:
        if byte in codes:
            total_bits += len(codes[byte])
    
    compressed_bytes = (total_bits + 7) // 8
    
    # общий размер: заголовок + таблица + сжатые данные
    total_size = 16 + 256 + compressed_bytes
    
    return total_size

def encode(input_path: str, archive_path: str, force_algorithm=None):
    """Интеллектуальное сжатие."""
    n = os.stat(input_path).st_size
    
    if force_algorithm is not None:
        # принудительное использование алгоритма
        if force_algorithm == 0:
            print(f"Forced algorithm 0 (no compression)")
            lab3_n1 = load_module("lab3_n1", os.path.join(base_dir, "..", "lab3", "n1.py"))
            lab3_n1.encode(input_path, archive_path)
        elif force_algorithm == 1:
            print(f"Forced algorithm 1 (Huffman)")
            huffman_codec.encode(input_path, archive_path)
        else:
            raise ValueError(f"unknown algorithm: {force_algorithm}")
        return
    
    # оцениваем размер с Хаффманом
    huffman_size = estimate_huffman_size(input_path)
    raw_size = 16 + n  # заголовок + данные без сжатия
    
    print(f"Input size: {n} bytes")
    print(f"Estimated Huffman archive: {huffman_size} bytes")
    print(f"Raw archive: {raw_size} bytes")
    
    if huffman_size < raw_size:
        print(f"Using algorithm 1 (Huffman) - saves {raw_size - huffman_size} bytes")
        huffman_codec.encode(input_path, archive_path)
    else:
        print(f"Using algorithm 0 (no compression) - Huffman would increase size by {huffman_size - raw_size} bytes")
        lab3_n1 = load_module("lab3_n1", os.path.join(base_dir, "..", "lab3", "n1.py"))
        lab3_n1.encode(input_path, archive_path)

def decode(archive_path: str, output_path: str):
    """Декодирование - используем универсальный декодер."""
    n3 = load_module("universal_decoder", os.path.join(base_dir, "n3.py"))
    n3.decode(archive_path, output_path)

def main(argv):
    if len(argv) < 3:
        print("usage: n4.py encode <input> <archive> [--force-algorithm=N] | n4.py decode <archive> <output>", file=sys.stderr)
        return 2
    
    cmd = argv[0]
    
    try:
        if cmd == "encode":
            force_alg = None
            for arg in argv[3:]:
                if arg.startswith("--force-algorithm="):
                    force_alg = int(arg.split("=")[1])
            
            encode(argv[1], argv[2], force_alg)
            return 0
        elif cmd == "decode":
            decode(argv[1], argv[2])
            return 0
        else:
            print("unknown command", file=sys.stderr)
            return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
