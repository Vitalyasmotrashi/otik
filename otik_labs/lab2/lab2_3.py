import sys
from collections import Counter

def guess_encoding(counts):
    """Определение кодировки по частотам байтов."""
    total = sum(counts.values())
    if total == 0:
        return "Не удалось определить (файл пуст)"

    # доли не-ASCII байтов
    non_ascii_ratio = sum(c for b, c in counts.items() if b > 127) / total

    # если почти все байты <128 — ASCII
    if non_ascii_ratio < 0.05:
        return "ASCII / не русскоязычный текст"

    # частоты характерных байтов
    freq = lambda b: counts.get(b, 0) / total

    # UTF-8
    if freq(0xD0) + freq(0xD1) > 0.15:
        return "UTF-8"

    # CP1251
    if max(freq(b) for b in range(0xE0, 0xF0)) > 0.03:
        return "Windows-1251 (CP1251)"

    # KOI8-R
    if max(freq(b) for b in range(0xC0, 0xE0)) > 0.03 and max(freq(b) for b in range(0xE0, 0xF0)) > 0.02:
        return "KOI8-R"

    # ISO-8859-5
    if max(freq(b) for b in range(0xB0, 0xC0)) > 0.03:
        return "ISO-8859-5"

    return "Неопределённая кодировка (возможно другая или смешанная)"


def analyze_encoding(filename):
    """Анализ частот байтов и определение кодировки."""
    with open(filename, "rb") as f:
        data = f.read()

    n = len(data)
    if n == 0:
        print("Файл пустой.")
        return

    counts = Counter(data)

    # Топ-4 наиболее частых байта 
    top4_all = sorted(counts.items(), key=lambda x: -x[1])[:4]

    # Топ-4 не-ASCII байта 
    non_ascii = [(b, c) for b, c in counts.items() if b > 127]
    top4_non_ascii = sorted(non_ascii, key=lambda x: -x[1])[:4]

    print(f"\nАнализ кодировки файла: {filename}")
    print(f"Общее количество байт: {n}")
    print(f"Количество уникальных байт: {len(counts)}")
    print("-" * 60)

    print("Топ-4 наиболее частых байта:")
    for b, c in top4_all:
        char = chr(b) if 32 <= b <= 126 else '.'
        print(f"  {b:3} (0x{b:02X}) '{char}' — {c} раз ({100 * c / n:.2f}%)")

    print("\nТоп-4 наиболее частых не-ASCII байта:")
    for b, c in top4_non_ascii:
        print(f"  {b:3} (0x{b:02X}) — {c} раз ({100 * c / n:.2f}%)")

    print("-" * 60)

    encoding_guess = guess_encoding(counts)
    print(f"\n➡ Предполагаемая кодировка: {encoding_guess}")
    print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python lab2_3.py <имя_файла>")
    else:
        analyze_encoding(sys.argv[1])
