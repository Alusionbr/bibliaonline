#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera os icones do site (SVG + PNG) sem dependencias externas.

O PNG e escrito por um encoder minimo (stdlib zlib+struct); a arte e
rasterizada por varredura de linha (scanline) com supersampling 4x para
antialiasing. Nada disso depende de Pillow ou de qualquer pacote externo.

Marca: quadrado navy (--dark/--navy do styles.css) com um livro aberto
dourado (--gold) — geometria pura, sem depender de fonte do sistema.
"""
import math
import struct
import zlib
from pathlib import Path

NAVY = (7, 26, 52)      # --dark / --navy
GOLD = (200, 149, 54)   # --gold
SPINE = (150, 108, 34)  # sombra da lombada, um pouco mais escura que --gold


def _arc(p0, p1, bulge, n=14):
    """Pontos ao longo de um arco raso entre p0 e p1, com deslocamento
    perpendicular maximo `bulge` no meio — da a curva de "pagina" do livro."""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    pts = []
    for i in range(n + 1):
        t = i / n
        off = bulge * math.sin(t * math.pi)
        pts.append((x0 + dx * t + nx * off, y0 + dy * t + ny * off))
    return pts


# Geometria do livro num espaco normalizado 1000x1000 (compartilhado por
# SVG e PNG, para os dois baterem visualmente). Base reta (livro deitado,
# aberto de frente); cada pagina tem a borda superior arqueada (curva
# convexa saindo da lombada) — silhueta reconhecivel de livro aberto,
# em vez de um "telhado" de arestas retas.
SPINE_TOP = (500, 270)
SPINE_BOTTOM = (500, 730)
LEFT_TOP = (140, 430)
LEFT_BOTTOM = (140, 730)
RIGHT_TOP = (860, 430)
RIGHT_BOTTOM = (860, 730)

LEFT_PAGE = (_arc(SPINE_TOP, LEFT_TOP, -70) + [LEFT_BOTTOM, SPINE_BOTTOM])
RIGHT_PAGE = (_arc(SPINE_TOP, RIGHT_TOP, 70) + [RIGHT_BOTTOM, SPINE_BOTTOM])
SPINE_RECT = [(486, 262), (514, 262), (514, 730), (486, 730)]


def _svg_poly(points):
    return " ".join(f"{x},{y}" for x, y in points)


def build_icon_svg():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">
<rect width="1000" height="1000" rx="220" fill="#{NAVY[0]:02x}{NAVY[1]:02x}{NAVY[2]:02x}"/>
<polygon points="{_svg_poly(LEFT_PAGE)}" fill="#{GOLD[0]:02x}{GOLD[1]:02x}{GOLD[2]:02x}"/>
<polygon points="{_svg_poly(RIGHT_PAGE)}" fill="#{GOLD[0]:02x}{GOLD[1]:02x}{GOLD[2]:02x}"/>
<polygon points="{_svg_poly(SPINE_RECT)}" fill="#{SPINE[0]:02x}{SPINE[1]:02x}{SPINE[2]:02x}"/>
</svg>
"""


# ---------- rasterizacao (scanline) ----------

def _fill_polygon(canvas, size, poly, color):
    """Preenche poly (coords 0..1000) num canvas RGB de size x size, por
    varredura de linha (interseccao de arestas por linha horizontal)."""
    scaled = [(x / 1000.0 * size, y / 1000.0 * size) for x, y in poly]
    n = len(scaled)
    edges = []
    for i in range(n):
        x1, y1 = scaled[i]
        x2, y2 = scaled[(i + 1) % n]
        if y1 == y2:
            continue
        edges.append((y1, y2, x1, x2))
    r, g, b = color
    row_bytes = size * 3
    for y in range(size):
        yc = y + 0.5
        xs = []
        for y1, y2, x1, x2 in edges:
            ylo, yhi = (y1, y2) if y1 < y2 else (y2, y1)
            if ylo <= yc < yhi:
                t = (yc - y1) / (y2 - y1)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(xs[i] + 0.5))
            xb = min(size, int(xs[i + 1] + 0.5))
            if xb <= xa:
                continue
            off = y * row_bytes + xa * 3
            canvas[off:off + (xb - xa) * 3] = bytes((r, g, b)) * (xb - xa)


def _rasterize(size, supersample=4):
    """Desenha o icone (fundo + livro) num quadrado `size`x`size` com
    antialiasing por supersampling + box-downsample. Retorna bytes RGB."""
    hi = size * supersample
    bg_row = bytes(NAVY) * hi
    canvas = bytearray(bg_row * hi)
    _fill_polygon(canvas, hi, LEFT_PAGE, GOLD)
    _fill_polygon(canvas, hi, RIGHT_PAGE, GOLD)
    _fill_polygon(canvas, hi, SPINE_RECT, SPINE)

    if supersample == 1:
        return bytes(canvas)

    out = bytearray(size * size * 3)
    s2 = supersample * supersample
    hi_row = hi * 3
    for y in range(size):
        base_y = y * supersample
        for x in range(size):
            base_x = x * supersample * 3
            rt = gt = bt = 0
            for dy in range(supersample):
                off = (base_y + dy) * hi_row + base_x
                for dx in range(supersample):
                    o = off + dx * 3
                    rt += canvas[o]
                    gt += canvas[o + 1]
                    bt += canvas[o + 2]
            o2 = (y * size + x) * 3
            out[o2] = rt // s2
            out[o2 + 1] = gt // s2
            out[o2 + 2] = bt // s2
    return bytes(out)


# ---------- encoder PNG minimo ----------

def _png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))


def _encode_png(rgb_bytes, size):
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # color type 2 = RGB
    raw = bytearray()
    row_len = size * 3
    for y in range(size):
        raw.append(0)  # filtro "None" por linha
        raw += rgb_bytes[y * row_len:(y + 1) * row_len]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", idat)
            + _png_chunk(b"IEND", b""))


def build_icon_png(size):
    rgb = _rasterize(size)
    return _encode_png(rgb, size)


def build_icons(site_dir):
    """Gera site/assets/icons/*.{svg,png}. Chamado por build_site()."""
    out_dir = Path(site_dir) / "assets" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "icon.svg").write_text(build_icon_svg(), encoding="utf-8")
    for name, size in (("icon-180.png", 180), ("icon-192.png", 192),
                        ("icon-512.png", 512), ("icon-512-maskable.png", 512)):
        (out_dir / name).write_bytes(build_icon_png(size))


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "site"
    build_icons(target)
    print(f"OK: icones gerados em {target / 'assets' / 'icons'}")
