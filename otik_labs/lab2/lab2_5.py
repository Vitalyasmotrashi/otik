import sys
import math
from collections import Counter, defaultdict

def analyze_markov_unicode(filename):
    # --- Чтение файла как текста в UTF-8 ---
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    n = len(text)
    if n < 2:
        print("Файл слишком короткий (меньше 2 символов).")
        return

    # --- Подсчёт пар символов ---
    pair_counts = Counter((text[i], text[i + 1]) for i in range(n - 1))

    # --- Подсчёт count(a_j *) ---
    first_counts = defaultdict(int)
    for (a, b), cnt in pair_counts.items():
        first_counts[a] += cnt

    # --- Условные вероятности ---
    conditional_probs = {
        (a, b): pair_counts[(a, b)] / first_counts[a]
        for (a, b) in pair_counts
    }

    # --- Суммарное количество информации ---
    I_bits = sum(
        pair_counts[(a, b)] * (-math.log2(conditional_probs[(a, b)]))
        for (a, b) in pair_counts
    )
    I_bytes = I_bits / 8

    print(f"\nАнализ Unicode-источника с памятью (Л2.№5)")
    print(f"Файл: {filename}")
    print(f"Количество символов: {n}")
    print(f"Количество различных пар: {len(pair_counts)}")
    print(f"Размер алфавита: {len(set(text))}")
    print("-" * 60)
    print(f"Суммарная информация I_CM1(Q) = {I_bits:.2f} бит ({I_bytes:.2f} байт)")

    print("\nФрагмент таблицы условных вероятностей:")
    print(f"{'a_j':>8} {'a_k':>8} {'count':>10} {'p(a_k|a_j)':>12}")
    print("-" * 50)

    for (a, b), cnt in sorted(pair_counts.items(), key=lambda x: -x[1])[:20]:
        p_cond = conditional_probs[(a, b)]
        a_disp = a if a.isprintable() else f"\\u{ord(a):04x}"
        b_disp = b if b.isprintable() else f"\\u{ord(b):04x}"
        print(f"{a_disp:>8} {b_disp:>8} {cnt:10} {p_cond:12.5f}")

    print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python lab2_5.py <имя_файла>")
    else:
        analyze_markov_unicode(sys.argv[1])
