#!/usr/bin/env python3
"""
Л4.№1 — Кодек Хаффмана с форматом OTIK

Использует сигнатуру и структуру из Л3.№1, но с алгоритмом = 1 (Хаффман).

Формат архива:
  Заголовок (16 байт):
    0..5  : сигнатура b"SOBSTV" (6 байт)
    6-7   : версия формата uint16 = 0
    8     : код алгоритма uint8 = 1 (Хаффман)
    9..15 : исходная длина n (uint64) - 7 байт
  
  Таблица частот (256 байт):
    256 значений uint8 - нормализованные частоты 0..255
  
  Сжатые данные (побитово упакованные коды Хаффмана)

CLI:
  encode <input> <archive>
  decode <archive> <output>
"""
from __future__ import annotations
import os
import struct
import sys
from typing import BinaryIO
import heapq

SIGNATURE = b"SOBSTV"
VERSION = 0
ALGORITHM = 1  # Хаффман

HEADER_FMT = "<6sHBxxxxxxx"  # sig(6), ver(2), alg(1), padding(7)
HEADER_SIZE = 16

class HuffNode:
    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
        # при равных частотах: листья раньше узлов, потом по символу
        if self.freq != other.freq:
            return self.freq < other.freq
        if self.symbol is None and other.symbol is None:
            return False
        if self.symbol is None:
            return False
        if other.symbol is None:
            return True
        return self.symbol < other.symbol

def build_huffman_tree(freqs):
    """Построить дерево Хаффмана. freqs - список из 256 частот."""
    heap = []
    for i in range(256):
        if freqs[i] > 0:
            heapq.heappush(heap, HuffNode(symbol=i, freq=freqs[i]))
    
    if len(heap) == 0:
        return None
    if len(heap) == 1:
        node = heapq.heappop(heap)
        return HuffNode(freq=node.freq, left=node, right=None)
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = HuffNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, parent)
    
    return heap[0]

def build_codes(node, prefix="", codes=None):
    """Построить таблицу кодов из дерева."""
    if codes is None:
        codes = {}
    if node is None:
        return codes
    if node.symbol is not None:
        codes[node.symbol] = prefix if prefix else "0"
    else:
        build_codes(node.left, prefix + "0", codes)
        if node.right:
            build_codes(node.right, prefix + "1", codes)
    return codes

def normalize_freqs(counts, n):
    """Нормализовать частоты к диапазону 0..255 (uint8)."""
    if n == 0:
        return [0] * 256
    
    # нормализуем так, чтобы ненулевые частоты не стали нулями
    freqs = [0] * 256
    for i in range(256):
        if counts[i] > 0:
            freqs[i] = max(1, int(counts[i] * 255 / n))
    
    return freqs

def encode(input_path: str, archive_path: str):
    """Сжать файл методом Хаффмана."""
    # читаем входной файл
    with open(input_path, "rb") as f:
        data = f.read()
    
    n = len(data)
    
    # подсчитываем частоты байтов
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    
    # нормализуем к uint8
    freqs = normalize_freqs(counts, n)
    
    # строим дерево и коды
    tree = build_huffman_tree(freqs)
    if tree is None:
        codes = {}
    else:
        codes = build_codes(tree)
    
    # кодируем данные
    bits = []
    for byte in data:
        if byte in codes:
            bits.extend([int(b) for b in codes[byte]])
    
    # упаковываем биты в байты
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
        # добавляем длину исходного файла (7 байт)
        header = header[:9] + struct.pack("<Q", n)[:7]
        f.write(header)
        
        # таблица частот
        f.write(bytes(freqs))
        
        # сжатые данные
        f.write(compressed)

def decode(archive_path: str, output_path: str):
    """Распаковать файл методом Хаффмана."""
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
        
        # читаем длину (7 байт)
        n_bytes = header[9:16] + b'\x00'
        n = struct.unpack("<Q", n_bytes)[0]
        
        # читаем таблицу частот
        freqs_raw = f.read(256)
        if len(freqs_raw) != 256:
            raise ValueError("short freqs table")
        freqs = list(freqs_raw)
        
        # строим дерево
        tree = build_huffman_tree(freqs)
        if tree is None and n > 0:
            raise ValueError("no tree for non-empty file")
        
        # читаем сжатые данные
        compressed = f.read()
    
    # декодируем
    decoded = bytearray()
    node = tree
    bits_processed = 0
    
    for byte in compressed:
        for i in range(8):
            if len(decoded) >= n:
                break
            
            bit = (byte >> (7 - i)) & 1
            bits_processed += 1
            
            if node.symbol is not None:
                decoded.append(node.symbol)
                node = tree
                if len(decoded) >= n:
                    break
            
            if bit == 0:
                node = node.left
            else:
                node = node.right if node.right else node.left
            
            if node.symbol is not None:
                decoded.append(node.symbol)
                node = tree
        
        if len(decoded) >= n:
            break
    
    # записываем результат
    with open(output_path, "wb") as f:
        f.write(decoded[:n])

def main(argv):
    if len(argv) < 3:
        print("usage: n1.py encode <input> <archive> | n1.py decode <archive> <output>", file=sys.stderr)
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
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
