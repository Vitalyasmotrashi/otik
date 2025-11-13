
#!/bin/bash

SCRIPT="$(dirname "$0")/lab2_3.py"

FILES_DIR="../labs-files/Файлы в формате простого текста — кодировки разные"

OUTPUT_FILE="encoding_analysis_results1.txt"

if [ ! -f "$SCRIPT" ]; then
    echo "Ошибка: файл $SCRIPT не найден!"
    exit 1
fi

if [ ! -d "$FILES_DIR" ]; then
    echo "Ошибка: папка '$FILES_DIR' не найдена!"
    echo "Текущая директория: $(pwd)"
    exit 1
fi

> "$OUTPUT_FILE"

echo "========================================" | tee -a "$OUTPUT_FILE"
echo "Анализ кодировок текстовых файлов" | tee -a "$OUTPUT_FILE"
echo "Дата: $(date)" | tee -a "$OUTPUT_FILE"
echo "========================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

count=0

for file in "$FILES_DIR"/*; do
    # директории
    if [ -d "$file" ]; then
        continue
    fi
    
    # скрытые файлы
    basename_file=$(basename "$file")
    if [[ "$basename_file" == .* ]]; then
        continue
    fi
    
    echo "Обработка: $file" | tee -a "$OUTPUT_FILE"
    
    python3 "$SCRIPT" "$file" >> "$OUTPUT_FILE" 2>&1
    
    echo "" >> "$OUTPUT_FILE"
    echo "========================================" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    ((count++))
done

echo "" | tee -a "$OUTPUT_FILE"
echo "Обработано файлов: $count" | tee -a "$OUTPUT_FILE"
echo "Результаты сохранены в: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
