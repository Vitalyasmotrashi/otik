import math
import sys
from collections import Counter

def analyze_file(filename):
    with open(filename, "rb") as f:
        data = f.read()

    n = len(data)  # длина в байтах
    if n == 0:
        print("Файл пустой.")
        return

    # количества вхождений каждого байта 
    counts = Counter(data)

    # вероятности и количества информации 
    probs = {b: counts[b] / n for b in counts}
    infos = {b: -math.log2(probs[b]) for b in counts}

    # cуммарное количество информации 
    total_info_bits = sum(counts[b] * infos[b] for b in counts)
    total_info_bytes = total_info_bits / 8

    # oценки сжатия 
    L_bits = n * 8
    L_bytes = n
    E = math.ceil(total_info_bytes)  # минимальный размер сжатого текста
    G64 = E + 256 * 8                # с таблицей из 256 64-битных частот
    G8 = E + 256 * 1                 # с таблицей из 256 8-битных частот

    print(f"\nАнализ файла: {filename}")
    print(f"Длина файла: n = {n} байт ({L_bits} бит)")
    print(f"Суммарная информация IΣ(Q) = {total_info_bits:.2f} бит ({total_info_bytes:.2f} байт)")
    print(f"Минимальная длина без учёта контекста: E = {E} байт")
    print(f"Длина архива с таблицей G64 = {G64} байт")
    print(f"Длина архива с таблицей G8  = {G8} байт\n")

    print(f"{'Байт':>6} {'ASCII':>6} {'count':>10} {'p(j)':>10} {'I(j), бит':>12}")
    print("-" * 50)

    for b, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        pj = probs[b]
        ij = infos[b]
        ascii_repr = chr(b) if 32 <= b <= 126 else "."
        print(f"{b:6} {ascii_repr:>6} {cnt:10} {pj:10.5f} {ij:12.5f}")

    fract_part = total_info_bits - int(total_info_bits)
    print("\nДробная часть IΣ(Q):", format(fract_part, ".5e"))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python lab2_1.py <имя_файла>")
    else:
        analyze_file(sys.argv[1])
