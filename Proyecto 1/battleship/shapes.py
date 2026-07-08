"""Parsing y utilidades geometricas para las formas de las embarcaciones.

El formato de la API representa cada embarcacion como texto: filas separadas
por ',', y cada caracter de una fila es 'X' (celda ocupada) o '-' (vacia).
Varias embarcaciones vienen concatenadas en un solo string separadas por '|'.
"""

from __future__ import annotations

Cell = tuple[int, int]
Shape = frozenset[Cell]

DIRECTIONS: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


def normalize(cells: Shape) -> Shape:
    """Traslada un conjunto de celdas para que su esquina superior izquierda sea (0, 0)."""
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def rotate90(cells: Shape) -> Shape:
    """Rota 90 grados un conjunto de celdas (sentido arbitrario, se normaliza despues)."""
    return normalize(frozenset((c, -r) for r, c in cells))


def all_rotations(cells: Shape) -> set[Shape]:
    """Retorna el conjunto (deduplicado) de las 4 rotaciones posibles de una forma."""
    rotations: set[Shape] = set()
    current = normalize(cells)
    for _ in range(4):
        rotations.add(current)
        current = rotate90(current)
    return rotations


def parse_ship(ship_str: str) -> Shape:
    """Convierte el texto de una sola embarcacion (filas separadas por ',') en celdas."""
    rows = ship_str.split(",")
    cells = frozenset(
        (r, c)
        for r, row in enumerate(rows)
        for c, ch in enumerate(row)
        if ch == "X"
    )
    if not cells:
        raise ValueError(f"Embarcacion sin celdas validas: {ship_str!r}")
    return normalize(cells)


def parse_ships(ships_str: str) -> list[Shape]:
    """Convierte el texto completo del campo 'ships' de la API en una lista de formas."""
    return [parse_ship(part) for part in ships_str.split("|") if part != ""]
