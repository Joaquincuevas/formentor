"""Seleccion de la siguiente jugada mediante un mapa de densidad de probabilidad.

Idea central: para cada embarcacion restante (con sus 4 rotaciones posibles),
se enumeran todas las ubicaciones del tablero donde esa forma podria calzar de
forma consistente con lo que ya sabemos (agua, toques sin hundir, hundidas).
Cada celda recibe un puntaje igual a la cantidad de ubicaciones validas que la
cubren; se dispara a la celda de mayor puntaje.

Esto unifica en un solo mecanismo el modo "caza" (sin toques activos, se busca
la celda estadisticamente mas probable) y el modo "remate" (con un toque activo,
las unicas ubicaciones validas son las que contienen ese toque, concentrando el
puntaje a su alrededor de forma natural).
"""

from __future__ import annotations

from collections import defaultdict

from .board import HIT, SUNK, UNKNOWN, WATER, Board
from .shapes import DIRECTIONS, Cell, Shape


def _is_valid_placement(cells: Shape, board: Board, hit_clusters: list[frozenset[Cell]]) -> bool:
    for cell in cells:
        if board.status[cell] in (WATER, SUNK):
            return False

    # Dos embarcaciones nunca pueden tocarse por una arista: si una celda
    # vecina (no incluida en esta ubicacion) ya es toque o hundida, esta
    # ubicacion es invalida.
    for r, c in cells:
        for dr, dc in DIRECTIONS:
            nb = (r + dr, c + dc)
            if nb in board.status and nb not in cells and board.status[nb] in (HIT, SUNK):
                return False

    # Toda celda de toque conectada (cluster) que esta ubicacion intersecte
    # debe quedar completamente contenida, ya que un cluster de toques
    # siempre pertenece a una unica embarcacion.
    for cluster in hit_clusters:
        if cells & cluster and not cluster <= cells:
            return False

    return True


def compute_heatmap(board: Board) -> dict[Cell, int]:
    heat: dict[Cell, int] = defaultdict(int)
    hit_clusters = board.hit_clusters()

    for template in board.remaining_ships():
        for shape in template.rotations:
            max_r = max(r for r, _ in shape)
            max_c = max(c for _, c in shape)
            for dr in range(board.rows - max_r):
                for dc in range(board.cols - max_c):
                    cells = frozenset((r + dr, c + dc) for r, c in shape)
                    if _is_valid_placement(cells, board, hit_clusters):
                        for cell in cells:
                            if board.status[cell] == UNKNOWN:
                                heat[cell] += template.count

    return heat


def next_shot(board: Board) -> Cell | None:
    """Retorna la mejor celda para disparar, o None si no quedan celdas desconocidas."""
    heat = compute_heatmap(board)
    if heat:
        return max(heat.items(), key=lambda kv: kv[1])[0]

    # Respaldo (no deberia ocurrir si el estado del tablero es consistente):
    # preferir una celda desconocida adyacente a un toque activo.
    for cluster in board.hit_clusters():
        for cell in cluster:
            for dr, dc in DIRECTIONS:
                nb = (cell[0] + dr, cell[1] + dc)
                if nb in board.status and board.status[nb] == UNKNOWN:
                    return nb

    unknown = board.unknown_cells()
    return unknown[0] if unknown else None
