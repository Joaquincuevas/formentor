"""Estado interno del tablero que mantiene el jugador para un juego en curso."""

from __future__ import annotations

from dataclasses import dataclass, field

from .shapes import DIRECTIONS, Cell, Shape, all_rotations, normalize

UNKNOWN = "U"
WATER = "W"
HIT = "H"
SUNK = "S"


@dataclass
class ShipTemplate:
    """Un grupo de embarcaciones restantes que comparten exactamente la misma forma."""

    rotations: frozenset[Shape]
    size: int
    count: int


class Board:
    """Tablero conocido/inferido de un rival: celdas disparadas y embarcaciones restantes."""

    def __init__(self, rows: int, cols: int, ship_shapes: list[Shape]):
        self.rows = rows
        self.cols = cols
        self.status: dict[Cell, str] = {
            (r, c): UNKNOWN for r in range(rows) for c in range(cols)
        }
        self.templates: list[ShipTemplate] = []
        for shape in ship_shapes:
            rotations = frozenset(all_rotations(shape))
            existing = next((t for t in self.templates if t.rotations == rotations), None)
            if existing is not None:
                existing.count += 1
            else:
                self.templates.append(ShipTemplate(rotations=rotations, size=len(shape), count=1))

    # -- consultas -----------------------------------------------------

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def remaining_ships(self) -> list[ShipTemplate]:
        return [t for t in self.templates if t.count > 0]

    def all_sunk(self) -> bool:
        return all(t.count == 0 for t in self.templates)

    def unknown_cells(self) -> list[Cell]:
        return [cell for cell, val in self.status.items() if val == UNKNOWN]

    def _cluster(self, start: Cell, value: str) -> frozenset[Cell]:
        stack = [start]
        seen = {start}
        while stack:
            cur = stack.pop()
            for dr, dc in DIRECTIONS:
                nb = (cur[0] + dr, cur[1] + dc)
                if nb in self.status and nb not in seen and self.status[nb] == value:
                    seen.add(nb)
                    stack.append(nb)
        return frozenset(seen)

    def hit_clusters(self) -> list[frozenset[Cell]]:
        """Grupos de celdas 'H' conectadas: cada grupo pertenece siempre a una unica embarcacion,
        porque dos embarcaciones nunca pueden tocarse por una arista."""
        seen: set[Cell] = set()
        clusters = []
        for cell, val in self.status.items():
            if val == HIT and cell not in seen:
                cluster = self._cluster(cell, HIT)
                seen |= cluster
                clusters.append(cluster)
        return clusters

    # -- actualizacion ---------------------------------------------------

    def record_result(self, cell: Cell, result: int) -> None:
        """Aplica el resultado de un disparo (0=agua, 1=toque, 2=hundida, 3=hundida y fin)."""
        if result == 0:
            self.status[cell] = WATER
            return
        if result in (1, 2, 3):
            self.status[cell] = HIT
            if result in (2, 3):
                self._sink_cluster_containing(cell)
            return
        raise ValueError(f"Resultado de disparo desconocido: {result!r}")

    def _sink_cluster_containing(self, cell: Cell) -> None:
        cluster = self._cluster(cell, HIT)
        for c in cluster:
            self.status[c] = SUNK

        shape = normalize(cluster)
        for template in self.templates:
            if template.count > 0 and shape in template.rotations:
                template.count -= 1
                break

        # Como dos embarcaciones nunca comparten una arista, todas las celdas
        # adyacentes (ortogonales) a una embarcacion hundida son agua garantizada.
        # Lo marcamos internamente para no gastar disparos ahi, sin necesidad
        # de consultarlo a la API.
        for c in cluster:
            for dr, dc in DIRECTIONS:
                nb = (c[0] + dr, c[1] + dc)
                if nb in self.status and self.status[nb] == UNKNOWN:
                    self.status[nb] = WATER
