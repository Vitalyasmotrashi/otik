import sys
import math
from collections import Counter, defaultdict

def analyze_markov_file(filename):
    with open(filename, "rb") as f:
        data = f.read()

    n = len(data)
    if n < 2:
        print("Файл слишком короткий для анализа (нужно ≥2 байта).")
        return

    # --- Подсчёт пар символов (a_j a_k) ---
    pair_counts = Counter((data[i], data[i + 1]) for i in range(n - 1))

    # --- Подсчёт count(a_j *) ---
    first_counts = defaultdict(int)
    for (a, b), cnt in pair_counts.items():
        first_counts[a] += cnt

    # --- Условные вероятности p(a_k | a_j) ---
    conditional_probs = {
        (a, b): pair_counts[(a, b)] / first_counts[a]
        for (a, b) in pair_counts
    }

    # --- Количество информации (в битах) ---
    I_bits = sum(
        pair_counts[(a, b)] * (-math.log2(conditional_probs[(a, b)]))
        for (a, b) in pair_counts
    )

    I_bytes = I_bits / 8

    print(f"\nАнализ источника с памятью (Л2.№4)")
    print(f"Файл: {filename}")
    print(f"Количество байт в файле: n = {n}")
    print(f"Количество различных пар: {len(pair_counts)}")
    print(f"Количество различных символов: {len(set(data))}")
    print("-" * 60)
    print(f"Суммарное количество информации I_CM1(Q) = {I_bits:.2f} бит ({I_bytes:.2f} байт)")

    # --- Пример таблицы ---
    print("\nТаблица условных вероятностей (фрагмент):")
    print(f"{'a_j':>6} {'a_k':>6} {'count':>10} {'p(a_k|a_j)':>12}")
    print("-" * 40)

    for (a, b), cnt in sorted(pair_counts.items(), key=lambda x: -x[1])[:20]:
        p_cond = conditional_probs[(a, b)]
        a_disp = chr(a) if 32 <= a <= 126 else f"\\x{a:02X}"
        b_disp = chr(b) if 32 <= b <= 126 else f"\\x{b:02X}"
        print(f"{a_disp:>6} {b_disp:>6} {cnt:10} {p_cond:12.5f}")

    print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python lab2_4.py <имя_файла>")
    else:
        analyze_markov_file(sys.argv[1])
