#!/usr/bin/env python3
"""
Л3.№2 — Codec для формата OTIK v2 с иерархией папок.

CLI 
    pack <root_dir> <archive>   — собрать архив из каталога (с иерархией)
    unpack <archive> <out_dir>  — восстановить каталог из архива

- Все целые — little-endian.
- Выравнивание границ важных блоков — до 8 байт нулями.
- Сигнатура архива: b"SOBSTV02" (первые 6 байт совпадают с Л3.№1 — OTIK01).
- Версия формата — 2
"""
from __future__ import annotations

import os
import io
import sys
import stat as statmod
import struct
import time
from pathlib import Path
from typing import BinaryIO, List, Tuple

# константы формата
SIG = b"SOBSTV02"  # 8 байт сигнатуры
VER_MAJOR = 2
VER_MINOR = 0
COMP_CTX = 0       # по умолчанию: нет
COMP_NCTX = 0      # по умолчанию: нет
PROTECT = 0        # по умолчанию: нет

# фиксированная часть, 56 байт
#  8s signature; H major; H minor; B comp_ctx; B comp_nctx; B protection; B reserved;
#  I toc_entries; Q global_meta_offset; I global_meta_length; Q toc_offset; Q data_offset; Q total_original_size
HDR_FMT = "<8sHHBBBBI Q I Q Q Q"
HDR_SIZE = struct.calcsize(HDR_FMT)

#  H path_len; H flags; I mode; Q mtime; B comp_ctx; B comp_nctx; B protection; B reserved;
#  Q original_size; Q stored_size; Q data_offset; I extra_len; Q entry_id
ENTRY_FMT = "<HHI Q BBBB Q Q Q I Q"
ENTRY_SIZE = struct.calcsize(ENTRY_FMT)

FLAG_DIR = 0x1
FLAG_FILE = 0x2

ALIGN = 8

def _align(n: int, k: int = ALIGN) -> int:
    r = n % k
    return n if r == 0 else n + (k - r)

# --- сканирование каталога и сбор TOC ---

def _collect_entries(root: Path) -> List[dict]:
    """
    - 'path'    : относительный путь UTF‑8 (разделитель '/')
    - 'is_dir'  : True для каталогов, False для файлов
    - 'mode'    : POSIX-права (нижние 12 бит st_mode)
    - 'mtime'   : mtime (секунды, int)
    - 'size'    : исходный размер файла (для каталога 0)
    Позже при упаковке добавим:
    - 'stored_size' : размер сохранённых данных (для профиля 0 равен 'size')
    - 'data_offset' : смещение данных файла в архиве
    """
    entries: List[dict] = []
    root = root.resolve()

    # каталоги: отдельные записи с путём вида "dir/" (обязательный хвостовой '/')
    for dirpath, dirnames, _ in os.walk(root):
        rel = Path(dirpath).resolve().relative_to(root)
        if str(rel) != '.':
            p = str(rel).replace(os.sep, '/') + '/'
            st = os.stat(dirpath)
            entries.append({
                'path': p,
                'is_dir': True,
                'mode': st.st_mode & 0o7777,
                'mtime': int(st.st_mtime),
                'size': 0,
            })
    # Файлы: обычные записи, путь без завершающего '/'
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            fp = Path(dirpath) / name
            st = os.stat(fp)
            rel = fp.resolve().relative_to(root)
            p = str(rel).replace(os.sep, '/')
            entries.append({
                'path': p,
                'is_dir': False,
                'mode': st.st_mode & 0o7777,
                'mtime': int(st.st_mtime),
                'size': st.st_size,
            })

    # включаем запись для корневого каталога (пустой путь ''): это удобный маркер,
    # чтобы при распаковке однозначно создать out_dir и применить к нему метаданные.
    st_root = os.stat(root)
    entries.insert(0, {
        'path': '',
        'is_dir': True,
        'mode': st_root.st_mode & 0o7777,
        'mtime': int(st_root.st_mtime),
        'size': 0,
    })

    return entries


def pack(root_dir: str, archive: str) -> None:
    """
      1) Сканируем дерево и формируем TOC (без смещений на данные).
      2) Подсчитываем размеры TOC и вычисляем: toc_offset, data_offset.
      3) Назначаем каждому файлу data_offset в области данных (с выравниванием).
      4) Пишем заголовок, затем TOC + пути, делаем выравнивание на 8.
      5) Потоково записываем данные файлов по рассчитанным смещениям.

    """
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(root)

    entries = _collect_entries(root)
    toc_entries = len(entries)
    total_orig = sum(e['size'] for e in entries if not e['is_dir'])

    # подсчитаем общий размер TOC: сумма фиксированных записей и строк путей.
    toc_size = 0
    paths_bytes: List[bytes] = []
    for e in entries:
        p = e['path'].encode('utf-8')
        paths_bytes.append(p)
        toc_size += ENTRY_SIZE + len(p)  # extra_len = 0 (в нулевом профиле)
    toc_size_aligned = _align(toc_size)

    toc_offset = HDR_SIZE
    data_offset = HDR_SIZE + toc_size_aligned

    # проставим каждому файлу своё смещение в области данных.
    # выравнивание по 8 — чтобы оставаться совместимыми с возможными блоковыми алгоритмами/ДМА.
    cursor = data_offset
    for i, e in enumerate(entries):
        if e['is_dir']:
            e['stored_size'] = 0
            e['data_offset'] = 0
        else:
            cursor = _align(cursor)
            e['data_offset'] = cursor
            e['stored_size'] = e['size']
            cursor += e['stored_size']

    with open(archive, 'wb') as out:
        # Заголовок
        hdr = struct.pack(
            HDR_FMT,
            SIG,
            VER_MAJOR,
            VER_MINOR,
            COMP_CTX,
            COMP_NCTX,
            PROTECT,
            0,  # reserved
            toc_entries,
            0,  # global_meta_offset
            0,  # global_meta_length (uint32)
            toc_offset,
            data_offset,
            total_orig,
        )
        out.write(hdr)

        # TOC: пишем фиксированную часть записи, затем байты пути.
        for e, p_bytes in zip(entries, paths_bytes):
            path_len = len(p_bytes)
            flags = FLAG_DIR if e['is_dir'] else FLAG_FILE
            mode = e['mode']
            mtime = e['mtime']
            # 0xFF означает «наследовать значение из общего заголовка» —
            # это делает формат гибким, но не дублирует коды у каждой записи.
            comp_ctx = 0xFF
            comp_nctx = 0xFF
            protection = 0xFF
            reserved = 0
            original_size = e['size'] if not e['is_dir'] else 0
            stored_size = e['stored_size']
            data_off = e['data_offset']
            extra_len = 0
            entry_id = 0

            out.write(struct.pack(
                ENTRY_FMT,
                path_len, flags, mode, mtime,
                comp_ctx, comp_nctx, protection, reserved,
                original_size, stored_size, data_off, extra_len, entry_id
            ))
            out.write(p_bytes)
        # выравнивание после TOC — до ближайшей границы 8 байт нулями
        pad = _align(out.tell()) - out.tell()
        if pad:
            out.write(b"\x00" * pad)

        # данные файлов (пул payload):
        # для профиля 0/0/0 просто копируем «как есть». При включении алгоритмов
        # здесь должен происходить пайплайн: encode_ctx -> encode_nctx -> protect.
        for e in entries:
            if e['is_dir'] or e['stored_size'] == 0:
                continue
            # переход к заранее посчитанному смещению (на случай, если будущие версии пишут не последовательно)
            cur = out.tell()
            if cur < e['data_offset']:
                out.write(b"\x00" * (e['data_offset'] - cur))
            elif cur > e['data_offset']:
                raise RuntimeError("internal offset miscalc")

            src = root / e['path']
            with open(src, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)

# --- Чтение архива ---

def _safe_join(base: Path, rel: str) -> Path:
    """
      - абсолютные пути внутри архива ("/etc/passwd");
      - выход за пределы каталога назначения через "..".
    """
    rel_path = Path(rel)
    if rel_path.is_absolute():
        raise ValueError("absolute path in archive")
    full = (base / rel_path).resolve()
    if not str(full).startswith(str(base.resolve())):
        raise ValueError("path traversal detected")
    return full


def unpack(archive: str, out_dir: str) -> None:
    """распаковать архив в каталог out_dir.

    Схема чтения:
      1) Проверяем сигнатуру/версию и читаем общие коды алгоритмов.
      2) Переходим на TOC и читаем его записи + пути.
      3) Создаём каталоги (включая пустой путь для корня), проставляем права/mtime.
      4) Для каждого файла читаем данные по data_offset длиной stored_size и пишем.
    """
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    with open(archive, 'rb') as f:
        hdr_raw = f.read(HDR_SIZE)
        if len(hdr_raw) != HDR_SIZE:
            raise ValueError("short header")
        (
            sig,
            vmaj,
            vmin,
            comp_ctx,
            comp_nctx,
            protection,
            _reserved,
            toc_entries,
            global_meta_off,
            global_meta_len,
            toc_off,
            data_off,
            total_orig,
        ) = struct.unpack(HDR_FMT, hdr_raw)

        if sig != SIG:
            raise ValueError("bad signature")
        if vmaj < 1:
            raise ValueError("unsupported version")

        # читаем TOC: фиксированная часть записи + путь UTF‑8
        f.seek(toc_off)
        entries = []
        for i in range(toc_entries):
            eraw = f.read(ENTRY_SIZE)
            if len(eraw) != ENTRY_SIZE:
                raise ValueError("short TOC entry")
            (
                path_len, flags, mode, mtime,
                e_comp_ctx, e_comp_nctx, e_prot, e_res,
                original_size, stored_size, data_offset, extra_len, entry_id
            ) = struct.unpack(ENTRY_FMT, eraw)
            p = f.read(path_len)
            if len(p) != path_len:
                raise ValueError("short path")
            path = p.decode('utf-8')

            entries.append({
                'path': path,
                'is_dir': bool(flags & FLAG_DIR),
                'mode': mode,
                'mtime': mtime,
                'original_size': original_size,
                'stored_size': stored_size,
                'data_offset': data_offset,
                'comp_ctx': comp_ctx if e_comp_ctx == 0xFF else e_comp_ctx,
                'comp_nctx': comp_nctx if e_comp_nctx == 0xFF else e_comp_nctx,
                'protection': protection if e_prot == 0xFF else e_prot,
            })
        
        # восстановление каталогов и файлов
        # сначала каталоги (включая корень с пустым путём)
        for e in entries:
            if not e['is_dir']:
                continue
            rel = e['path']
            target = out_root if rel == '' else _safe_join(out_root, rel)
            target.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(target, e['mode'])
            except PermissionError:
                pass
            try:
                os.utime(target, (e['mtime'], e['mtime']))
            except Exception:
                pass

        # затем файлы: для профиля 0/0/0 читаем порциями и пишем как есть.
        for e in entries:
            if e['is_dir']:
                continue
            target = _safe_join(out_root, e['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            f.seek(e['data_offset'])
            remaining = e['stored_size']
            with open(target, 'wb') as out:
                while remaining:
                    chunk = f.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("unexpected EOF in data")
                    out.write(chunk)
                    remaining -= len(chunk)
            try:
                os.chmod(target, e['mode'])
            except PermissionError:
                pass
            try:
                os.utime(target, (e['mtime'], e['mtime']))
            except Exception:
                pass


def main(argv: list[str]) -> int:
    if len(argv) == 0:
        print("usage: n2.py pack <root_dir> <archive> | n2.py unpack <archive> <out_dir>", file=sys.stderr)
        return 2
    cmd = argv[0]
    try:
        if cmd == 'pack' and len(argv) == 3:
            pack(argv[1], argv[2])
            return 0
        if cmd == 'unpack' and len(argv) == 3:
            unpack(argv[1], argv[2])
            return 0
        print("usage: n2.py pack <root_dir> <archive> | n2.py unpack <archive> <out_dir>", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
