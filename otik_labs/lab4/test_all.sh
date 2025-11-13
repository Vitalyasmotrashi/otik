#!/bin/bash
# Скрипт для тестирования всех заданий Л4

set -e  # остановка при ошибке

echo "=== Тестирование лабораторной работы 4 ==="
echo ""

# Создание тестового файла
echo "1. Создание тестовых файлов..."
echo "Hello World! This is a test file for compression algorithms." > test_small.txt
cp ../lab2/1.txt test_large.txt 2>/dev/null || echo "Тестовый файл для сравнения" > test_large.txt

echo "=== Л4.№1: Кодек Хаффмана ==="
echo ""
echo "Сжатие малого файла..."
python3 n1.py encode test_small.txt test_small_h.otik
echo "Распаковка..."
python3 n1.py decode test_small_h.otik test_small_h_out.txt
echo "Проверка..."
diff test_small.txt test_small_h_out.txt && echo "✓ Малый файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "Сжатие большого файла..."
python3 n1.py encode test_large.txt test_large_h.otik
echo "Распаковка..."
python3 n1.py decode test_large_h.otik test_large_h_out.txt
echo "Проверка..."
diff test_large.txt test_large_h_out.txt && echo "✓ Большой файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "Размеры файлов (Хаффман):"
ls -lh test_small.txt test_small_h.otik
ls -lh test_large.txt test_large_h.otik

echo ""
echo "=== Л4.№2: Анализ разрядностей ==="
echo ""
python3 n2.py analyze test_large.txt

echo ""
echo "=== Л4.№6: Кодек Шеннона-Фано ==="
echo ""
echo "Сжатие малого файла..."
python3 n6.py encode test_small.txt test_small_sf.otik
echo "Распаковка..."
python3 n6.py decode test_small_sf.otik test_small_sf_out.txt
echo "Проверка..."
diff test_small.txt test_small_sf_out.txt && echo "✓ Малый файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "Сжатие большого файла..."
python3 n6.py encode test_large.txt test_large_sf.otik
echo "Распаковка..."
python3 n6.py decode test_large_sf.otik test_large_sf_out.txt
echo "Проверка..."
diff test_large.txt test_large_sf_out.txt && echo "✓ Большой файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "Размеры файлов (Шеннон-Фано):"
ls -lh test_small.txt test_small_sf.otik
ls -lh test_large.txt test_large_sf.otik

echo ""
echo "=== Л4.№3: Универсальный декодер ==="
echo ""
echo "Декодирование Хаффмана..."
python3 n3.py decode test_large_h.otik test_n3_h.txt
diff test_large.txt test_n3_h.txt && echo "✓ Хаффман: OK" || echo "✗ ОШИБКА"

echo ""
echo "Декодирование Шеннона-Фано..."
python3 n3.py decode test_large_sf.otik test_n3_sf.txt
diff test_large.txt test_n3_sf.txt && echo "✓ Шеннон-Фано: OK" || echo "✗ ОШИБКА"

echo ""
echo "=== Л4.№4: Интеллектуальный кодер ==="
echo ""
echo "Сжатие малого файла (ожидается без сжатия)..."
python3 n4.py encode test_small.txt test_small_smart.otik

echo ""
echo "Сжатие большого файла (ожидается Хаффман)..."
python3 n4.py encode test_large.txt test_large_smart.otik

echo ""
echo "Декодирование малого файла..."
python3 n4.py decode test_small_smart.otik test_small_smart_out.txt
diff test_small.txt test_small_smart_out.txt && echo "✓ Малый файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "Декодирование большого файла..."
python3 n4.py decode test_large_smart.otik test_large_smart_out.txt
diff test_large.txt test_large_smart_out.txt && echo "✓ Большой файл: OK" || echo "✗ ОШИБКА"

echo ""
echo "=== Сравнение размеров архивов ==="
echo ""
echo "Малый файл:"
ls -lh test_small.txt test_small_h.otik test_small_sf.otik test_small_smart.otik

echo ""
echo "Большой файл:"
ls -lh test_large.txt test_large_h.otik test_large_sf.otik test_large_smart.otik

echo ""
echo "=== Очистка временных файлов ==="
rm -f test_*_out.txt test_n3_*.txt

echo ""
echo "=== Все тесты завершены! ==="
