#!/usr/bin/env python3
"""
Л3.1. Нулевая версия формата архива

Заголовок (ровно 16 байт), little-endian:
  0..5  : сигнатура формата (6 байт)          -> b"OTIK01"
  6..7  : версия формата (uint16)             -> 0
  8..15 : исходная длина n (uint64)           -> размер файла Q в байтах

далее идут "сырые" данные исходного файла Q длиной n байт.

CLI:
  encode <path_to_Q> <path_to_R>
  decode <path_to_R> <path_to_Q_out>

Linux:
  ./n1.py encode ./q.txt ./r.otik
  ./n1.py decode ./r.otik ./q_out.txt

Код ниже снабжён подробными комментариями к каждому действию.
"""

from __future__ import annotations

import os
import struct
import sys
from typing import BinaryIO

# --- Константы формата ---

# Выбранная сигнатура формата (строго 6 байт)
SIGNATURE: bytes = b"OTIK01"

# Номер версии формата для задания Л3.1 (uint16 = 0)
VERSION: int = 0

# Описание заголовка для struct: < = little-endian, 6s (6 байт), H (uint16), Q (uint64)
HEADER_FMT: str = "<6sHQ"
HEADER_SIZE: int = struct.calcsize(HEADER_FMT)  # 16 байт


def write_header(f: BinaryIO, data_len: int) -> None:
    """Записать 16-байтовый заголовок в поток f.

    Проверки:
      - data_len должен попадать в диапазон uint64.
      - Сигнатура и версия жёстко фиксированы для Л3.1.
    """

    if data_len < 0 or data_len > (1 << 64) - 1:
        raise ValueError("data_len out of uint64 range")

    header = struct.pack(HEADER_FMT, SIGNATURE, VERSION, data_len)
    f.write(header)


def read_header(f: BinaryIO) -> tuple[int]:
    """Прочитать и проверить заголовок, вернуть (n,).

    Ошибки:
      - короткий файл (меньше 16 байт)
      - неверная сигнатура
      - неподдерживаемая версия
    """

    raw = f.read(HEADER_SIZE)
    if len(raw) != HEADER_SIZE:
        raise ValueError("archive too short: no full header")

    sig, ver, n = struct.unpack(HEADER_FMT, raw)
    if sig != SIGNATURE:
        raise ValueError("bad signature")
    if ver != VERSION:
        raise ValueError(f"unsupported version: {ver}")

    return (n,)


def encode(input_path: str, archive_path: str, *, chunk: int = 1024 * 1024) -> None:
    """Создать архив R по файлу Q.

    Алгоритм:
      1) получить длину Q (n);
      2) записать заголовок (16 байт);
      3) скопировать тело файла блоками (по умолчанию 1 МБ).
    """

    n = os.stat(input_path).st_size  # исходная длина n

    # Открываем выходной архив и исходный файл. Используем двоичный режим.
    with open(archive_path, "wb") as out_f, open(input_path, "rb") as in_f:
        write_header(out_f, n)

        # Потоковая копия: читаем исходные данные блоками и сразу пишем в архив.
        while True:
            buf = in_f.read(chunk)
            if not buf:
                break
            out_f.write(buf)


def decode(archive_path: str, output_path: str, *, chunk: int = 1024 * 1024) -> None:
    """Восстановить файл Q̃ из архива R.

    Проверяем заголовок и согласованность размеров, затем копируем ровно n байт.
    """

    with open(archive_path, "rb") as in_f:
        (n,) = read_header(in_f)

        # Быстрая проверка целостности архива: общий размер должен быть 16 + n.
        try:
            total_size = os.fstat(in_f.fileno()).st_size
            expected = HEADER_SIZE + n
            if total_size != expected:
                raise ValueError(
                    f"archive size mismatch: got {total_size}, expected {expected}"
                )
        except Exception:
            # Если по каким-то причинам fstat недоступен (редко), пропускаем эту проверку.
            pass

        remaining = n
        with open(output_path, "wb") as out_f:
            while remaining:
                to_read = min(chunk, remaining)
                buf = in_f.read(to_read)
                if not buf:
                    # Данные закончились раньше n байт -> битый/обрезанный архив.
                    raise ValueError("unexpected EOF in archive data")
                out_f.write(buf)
                remaining -= len(buf)


def main(argv: list[str]) -> int:
    """Простейший парсер без справки.

    Допустимые вызовы:
      - encode <Q> <R>
      - decode <R> <Q_out>
    Любой другой набор аргументов приводит к короткому сообщению об использовании.
    """

    if len(argv) == 0:
        print("usage: n1.py encode <Q> <R> | n1.py decode <R> <Q_out>", file=sys.stderr)
        return 2

    cmd = argv[0]
    try:
        if cmd == "encode" and len(argv) == 3:
            encode(argv[1], argv[2])
            return 0
        elif cmd == "decode" and len(argv) == 3:
            decode(argv[1], argv[2])
            return 0
        else:
            return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    # передаём только позиционные аргументы без имени скрипта
    raise SystemExit(main(sys.argv[1:]))