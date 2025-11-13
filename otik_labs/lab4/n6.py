#!/usr/bin/env python3
"""
Л4.№6 — Кодек Шеннона-Фано (+3 балла)

Использует тот же формат, что и Хаффман, но алгоритм = 2.

Формат архива:
  Заголовок (16 байт):
    0..5  : сигнатура b"SOBSTV" (6 байт)
    6-7   : версия формата uint16 = 0
    8     : код алгоритма uint8 = 2 (Шеннон-Фано)
    9..15 : исходная длина n (uint64) - 7 байт
  
  Таблица частот (256 байт):
    256 значений uint8 - нормализованные частоты 0..255
  
  Сжатые данные (побитово упакованные коды Шеннона-Фано)

CLI:
  encode <input> <archive>
  decode <archive> <output>
"""
from __future__ import annotations
import os
import struct
import sys
from typing import List, Tuple

SIGNATURE = b"SOBSTV"
VERSION = 0
ALGORITHM = 2  # Шеннон-Фано

HEADER_FMT = "<6sHBxxxxxxx"
HEADER_SIZE = 16

def shannon_fano(symbols_freqs: List[Tuple[int, int]], prefix="") -> dict:
    """Рекурсивное построение кодов Шеннона-Фано.
    
    symbols_freqs: список кортежей (symbol, freq)
    """
    if len(symbols_freqs) == 0:
        return {}
    
    if len(symbols_freqs) == 1:
        symbol, _ = symbols_freqs[0]
        return {symbol: prefix if prefix else "0"}
    
    # сортируем по убыванию частот, при равенстве - по возрастанию символа
    sorted_sf = sorted(symbols_freqs, key=lambda x: (-x[1], x[0]))
    
    # делим на две части с примерно равными суммами частот
    total = sum(f for _, f in sorted_sf)
    cumsum = 0
    split_idx = 0
    
    for i, (_, freq) in enumerate(sorted_sf):
        cumsum += freq
        if cumsum >= total / 2:
            split_idx = i + 1
            break
    
    if split_idx == 0:
        split_idx = 1
    
    left = sorted_sf[:split_idx]
    right = sorted_sf[split_idx:]
    
    codes = {}
    codes.update(shannon_fano(left, prefix + "0"))
    codes.update(shannon_fano(right, prefix + "1"))
    
    return codes

def build_shannon_fano_codes(freqs):
    """Построить коды Шеннона-Фано из частот."""
    symbols_freqs = [(i, freqs[i]) for i in range(256) if freqs[i] > 0]
    
    if len(symbols_freqs) == 0:
        return {}
    
    return shannon_fano(symbols_freqs)

def normalize_freqs(counts, n):
    """Нормализовать частоты к диапазону 0..255."""
    if n == 0:
        return [0] * 256
    
    freqs = [0] * 256
    for i in range(256):
        if counts[i] > 0:
            freqs[i] = max(1, int(counts[i] * 255 / n))
    
    return freqs

def encode(input_path: str, archive_path: str):
    """Сжать файл методом Шеннона-Фано."""
    with open(input_path, "rb") as f:
        data = f.read()
    
    n = len(data)
    
    # подсчитываем частоты
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    
    # нормализуем
    freqs = normalize_freqs(counts, n)
    
    # строим коды Шеннона-Фано
    codes = build_shannon_fano_codes(freqs)
    
    # кодируем
    bits = []
    for byte in data:
        if byte in codes:
            bits.extend([int(b) for b in codes[byte]])
    
    # упаковываем в байты
    compressed = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        byte_val = 0
        for j, bit in enumerate(byte_bits):
            byte_val |= (bit << (7 - j))
        compressed.append(byte_val)
    
    # записываем архив
    with open(archive_path, "wb") as f:
        # заголовок
        header = struct.pack(HEADER_FMT, SIGNATURE, VERSION, ALGORITHM)
        header = header[:9] + struct.pack("<Q", n)[:7]
        f.write(header)
        
        # таблица частот
        f.write(bytes(freqs))
        
        # сжатые данные
        f.write(compressed)

def build_decode_tree(codes):
    """Построить дерево декодирования из словаря кодов."""
    tree = {}
    for symbol, code in codes.items():
        node = tree
        for bit in code[:-1]:
            if bit not in node:
                node[bit] = {}
            node = node[bit]
        node[code[-1]] = symbol
    return tree

def decode(archive_path: str, output_path: str):
    """Распаковать файл методом Шеннона-Фано."""
    with open(archive_path, "rb") as f:
        # читаем заголовок
        header = f.read(HEADER_SIZE)
        if len(header) != HEADER_SIZE:
            raise ValueError("short header")
        
        sig = header[:6]
        ver = struct.unpack("<H", header[6:8])[0]
        alg = header[8]
        
        if sig != SIGNATURE:
            raise ValueError("bad signature")
        if ver != VERSION:
            raise ValueError(f"unsupported version: {ver}")
        if alg != ALGORITHM:
            raise ValueError(f"wrong algorithm: {alg}")
        
        # читаем длину
        n_bytes = header[9:16] + b'\x00'
        n = struct.unpack("<Q", n_bytes)[0]
        
        # читаем таблицу частот
        freqs_raw = f.read(256)
        if len(freqs_raw) != 256:
            raise ValueError("short freqs table")
        freqs = list(freqs_raw)
        
        # строим коды
        codes = build_shannon_fano_codes(freqs)
        
        # строим дерево декодирования
        decode_tree = build_decode_tree(codes)
        
        # читаем сжатые данные
        compressed = f.read()
    
    # декодируем
    decoded = bytearray()
    node = decode_tree
    
    for byte in compressed:
        for i in range(8):
            if len(decoded) >= n:
                break
            
            bit = str((byte >> (7 - i)) & 1)
            
            if bit in node:
                val = node[bit]
                if isinstance(val, int):
                    decoded.append(val)
                    node = decode_tree
                else:
                    node = val
            else:
                # ошибка декодирования - сбрасываем
                node = decode_tree
        
        if len(decoded) >= n:
            break
    
    # записываем результат
    with open(output_path, "wb") as f:
        f.write(decoded[:n])

def main(argv):
    if len(argv) < 3:
        print("usage: n6.py encode <input> <archive> | n6.py decode <archive> <output>", file=sys.stderr)
        return 2
    
    cmd = argv[0]
    try:
        if cmd == "encode":
            encode(argv[1], argv[2])
            return 0
        elif cmd == "decode":
            decode(argv[1], argv[2])
            return 0
        else:
            return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
