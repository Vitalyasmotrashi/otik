#!/usr/bin/env python3
"""
Л4.№2 — Анализ эффективности кодов Хаффмана с разной разрядностью частот

Программа рассчитывает коды Хаффмана для разных разрядностей частот:
- 64 бит (ненормализованные)
- 32 бит (усечённые или нормализованные)
- 8 бит (нормализованные к 0..255)
- 4 бит (нормализованные к 0..15)

Для каждого варианта вычисляет:
- EB: длина сжатых данных в байтах
- GB: общая длина архива (EB + размер таблицы частот)

CLI:
  analyze <file> [--all-bits]  # анализ файла
  compare <file1> <file2> ...  # сравнение нескольких файлов
"""
from __future__ import annotations
import math
import sys
import heapq

class HuffNode:
    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right
    
    def __lt__(self, other):
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
    """Построить дерево Хаффмана."""
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
    """Построить таблицу кодов."""
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

def normalize_freqs(counts, n, max_val):
    """Нормализовать частоты к диапазону 0..max_val, сохраняя ненулевые."""
    if n == 0:
        return [0] * 256
    
    freqs = [0] * 256
    for i in range(256):
        if counts[i] > 0:
            freqs[i] = max(1, int(counts[i] * max_val / n))
    
    return freqs

def calc_compressed_size(data, freqs):
    """Рассчитать размер сжатых данных в битах для данных частот."""
    tree = build_huffman_tree(freqs)
    if tree is None:
        return 0
    
    codes = build_codes(tree)
    
    # подсчитываем реальные частоты в данных
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    
    # считаем общую длину в битах
    total_bits = 0
    for i in range(256):
        if counts[i] > 0 and i in codes:
            total_bits += counts[i] * len(codes[i])
    
    return total_bits

def analyze_file(filename, all_bits=False):
    """Анализировать файл для разных разрядностей."""
    with open(filename, "rb") as f:
        data = f.read()
    
    n = len(data)
    if n == 0:
        print(f"Файл {filename} пуст")
        return
    
    # подсчитываем частоты
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    
    print(f"\nАнализ файла: {filename}")
    print(f"Размер: {n} байт\n")
    
    results = {}
    
    # варианты разрядностей
    variants = [
        (64, (1 << 64) - 1, 8),
        (32, (1 << 32) - 1, 4),
        (8, 255, 1),
        (4, 15, 0.5),
    ]
    
    if all_bits:
        # бонус +2: перебор всех разрядностей от 1 до 64
        variants = [(b, (1 << b) - 1, b/8) for b in range(1, 65)]
    
    for bits, max_val, bytes_per_freq in variants:
        if bits in [64]:
            # ненормализованные частоты
            freqs = counts[:]
        else:
            # нормализованные
            freqs = normalize_freqs(counts, n, max_val)
        
        # размер сжатых данных в битах
        compressed_bits = calc_compressed_size(data, freqs)
        E = math.ceil(compressed_bits / 8)  # в байтах
        
        # размер таблицы частот
        freq_table_size = int(256 * bytes_per_freq)
        
        # общий размер архива
        G = E + freq_table_size
        
        results[bits] = {
            'E': E,
            'G': G,
            'freq_size': freq_table_size,
        }
        
        if bits in [64, 32, 8, 4] or all_bits:
            print(f"B = {bits:2d} бит:")
            print(f"  E{bits} = {E:10d} байт (сжатые данные)")
            print(f"  G{bits} = {G:10d} байт (архив с таблицей {freq_table_size} байт)")
            if not all_bits:
                print()
    
    # определяем оптимальную разрядность
    best_bits = min(results.keys(), key=lambda b: results[b]['G'])
    print(f"Оптимальная разрядность B* = {best_bits} бит (минимальный G = {results[best_bits]['G']} байт)")
    
    # рекомендация для фиксированной разрядности
    if not all_bits:
        print(f"\nРекомендуемая фиксированная разрядность B** = 8 бит")
        print(f"  - Удобна в чтении/записи (по 1 байту на частоту)")
        print(f"  - Таблица 256 байт (компактна)")
        print(f"  - G8 = {results[8]['G']} байт")
    
    return results

def compare_files(filenames):
    """Сравнить несколько файлов."""
    all_results = {}
    
    for filename in filenames:
        try:
            results = analyze_file(filename, all_bits=False)
            all_results[filename] = results
        except Exception as e:
            print(f"Ошибка при анализе {filename}: {e}")
    
    print("\n" + "="*80)
    print("СРАВНИТЕЛЬНАЯ ТАБЛИЦА")
    print("="*80)
    
    print(f"\n{'Файл':<30} {'E64':>10} {'E32':>10} {'E8':>10} {'E4':>10} {'B*':>5}")
    print("-"*80)
    for fname, results in all_results.items():
        e64 = results[64]['E']
        e32 = results[32]['E']
        e8 = results[8]['E']
        e4 = results[4]['E']
        best_b = min(results.keys(), key=lambda b: results[b]['G'])
        print(f"{fname:<30} {e64:10d} {e32:10d} {e8:10d} {e4:10d} {best_b:5d}")
    
    print(f"\n{'Файл':<30} {'G64':>10} {'G32':>10} {'G8':>10} {'G4':>10} {'B*':>5}")
    print("-"*80)
    for fname, results in all_results.items():
        g64 = results[64]['G']
        g32 = results[32]['G']
        g8 = results[8]['G']
        g4 = results[4]['G']
        best_b = min(results.keys(), key=lambda b: results[b]['G'])
        print(f"{fname:<30} {g64:10d} {g32:10d} {g8:10d} {g4:10d} {best_b:5d}")

def main(argv):
    if len(argv) == 0:
        print("usage: n2.py analyze <file> [--all-bits] | n2.py compare <file1> <file2> ...", file=sys.stderr)
        return 2
    
    cmd = argv[0]
    
    try:
        if cmd == "analyze":
            if len(argv) < 2:
                print("usage: n2.py analyze <file> [--all-bits]", file=sys.stderr)
                return 2
            all_bits = "--all-bits" in argv
            analyze_file(argv[1], all_bits)
            return 0
        elif cmd == "compare":
            if len(argv) < 2:
                print("usage: n2.py compare <file1> <file2> ...", file=sys.stderr)
                return 2
            compare_files(argv[1:])
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
