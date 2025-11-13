import math
import sys
from collections import Counter

def analyze_unicode_file(filename):
    # UTF-8 
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    n = len(text)
    if n == 0:
        print("Файл пустой.")
        return

    # количества вхождений 
    counts = Counter(text)

    # вероятности и количество информации 
    probs = {ch: counts[ch] / n for ch in counts}
    infos = {ch: -math.log2(probs[ch]) for ch in counts}

    total_info_bits = sum(counts[ch] * infos[ch] for ch in counts)
    total_info_bytes = total_info_bits / 8

    A1 = len(counts)

    # минимальный размер архива (без таблицы) 
    E = math.ceil(total_info_bytes)

    # длины таблиц 
    # длина алфавита в битах (64-битное число)
    L_A1_bits = 64

    # массив пар (символ, частота)
    # символ может занимать 1–4 байта в UTF-8 (8–32 бита)
    # для оценки возьмем 32 бита на символ + 64 бита на частоту
    G_table_bits = A1 * (32 + 64)
    G_table_bytes = G_table_bits / 8

    # общая длина архива 
    G_total = E + math.ceil(L_A1_bits / 8 + G_table_bytes)

    print(f"\nАнализ Unicode-файла: {filename}")
    print(f"Количество символов: n = {n}")
    print(f"Размер алфавита |A1| = {A1}")
    print(f"Суммарная информация IΣ(Q) = {total_info_bits:.2f} бит ({total_info_bytes:.2f} байт)")
    print(f"Минимальная длина без контекста: E = {E} байт")
    print(f"Оценочная длина архива G = {G_total} байт (включая таблицу частот)\n")

    print(f"{'Символ':>8} {'count':>10} {'p(j)':>10} {'I(j), бит':>12}")
    print("-" * 50)

    for ch, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        pj = probs[ch]
        ij = infos[ch]
        ch_disp = ch if ch.isprintable() else f"\\u{ord(ch):04x}"
        print(f"{ch_disp:>8} {cnt:10} {pj:10.5f} {ij:12.5f}")

    fract_part = total_info_bits - int(total_info_bits)
    print("\nДробная часть IΣ(Q):", format(fract_part, ".5e"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python lab2_2.py <имя_файла>")
    else:
        analyze_unicode_file(sys.argv[1])
