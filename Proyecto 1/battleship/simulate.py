"""Simulador local del juego, para probar y medir el solver sin depender de la
API real (util porque la API del curso no siempre esta disponible fuera de
las fechas de evaluacion)."""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from .board import Board
from .shapes import DIRECTIONS, Cell, Shape, all_rotations, normalize
from .solver import next_shot


def random_polyomino(size: int, rng: random.Random) -> Shape:
    """Genera una forma conexa aleatoria de `size` celdas (todas comparten al
    menos una arista con otra, como exige el enunciado)."""
    if size < 2:
        raise ValueError("Toda embarcacion debe tener al menos 2 celdas")
    cells = {(0, 0)}
    frontier = set(DIRECTIONS)
    while len(cells) < size:
        cell = rng.choice(list(frontier))
        frontier.discard(cell)
        cells.add(cell)
        for dr, dc in DIRECTIONS:
            nb = (cell[0] + dr, cell[1] + dc)
            if nb not in cells:
                frontier.add(nb)
    return normalize(frozenset(cells))


def _fits(cells: Shape, occupied: set[Cell]) -> bool:
    if cells & occupied:
        return False
    for r, c in cells:
        for dr, dc in DIRECTIONS:
            nb = (r + dr, c + dc)
            if nb in occupied and nb not in cells:
                return False
    return True


def _place_ships(
    rows: int, cols: int, shapes: list[Shape], rng: random.Random, max_attempts: int = 500
) -> list[frozenset[Cell]]:
    order = sorted(shapes, key=len, reverse=True)
    for _ in range(max_attempts):
        placements: list[frozenset[Cell]] = []
        occupied: set[Cell] = set()
        ok = True
        for shape in order:
            variants = list(all_rotations(shape))
            rng.shuffle(variants)
            placed = False
            for variant in variants:
                max_r = max(r for r, _ in variant)
                max_c = max(c for _, c in variant)
                positions = [
                    (dr, dc) for dr in range(rows - max_r) for dc in range(cols - max_c)
                ]
                rng.shuffle(positions)
                for dr, dc in positions:
                    cells = frozenset((r + dr, c + dc) for r, c in variant)
                    if _fits(cells, occupied):
                        placements.append(cells)
                        occupied |= cells
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                ok = False
                break
        if ok:
            return placements
    raise RuntimeError(
        "No se pudieron posicionar las embarcaciones: tablero muy pequeno para esas formas"
    )


class GameSimulator:
    """Un tablero rival oculto contra el que se puede disparar, con la misma
    semantica de resultados que la API (0 agua, 1 toque, 2 hundida, 3 fin)."""

    def __init__(
        self,
        rows: int,
        cols: int,
        ship_shapes: list[Shape],
        rng: random.Random | None = None,
    ):
        self.rows = rows
        self.cols = cols
        self.ship_shapes = ship_shapes
        rng = rng or random.Random()
        self.placements = _place_ships(rows, cols, ship_shapes, rng)
        self.ship_of_cell: dict[Cell, int] = {
            cell: idx for idx, placement in enumerate(self.placements) for cell in placement
        }
        self.hits_remaining = [len(p) for p in self.placements]
        self.sunk_count = 0

    def shoot(self, cell: Cell) -> int:
        idx = self.ship_of_cell.get(cell)
        if idx is None:
            return 0
        self.hits_remaining[idx] -= 1
        if self.hits_remaining[idx] == 0:
            self.sunk_count += 1
            return 3 if self.sunk_count == len(self.placements) else 2
        return 1


def _linear_shapes(lengths: list[int]) -> list[Shape]:
    return [frozenset((0, i) for i in range(n)) for n in lengths]


def _random_shapes(lengths: list[int], rng: random.Random) -> list[Shape]:
    return [random_polyomino(n, rng) for n in lengths]


@dataclass
class BenchmarkResult:
    shots: list[int]

    @property
    def mean(self) -> float:
        return statistics.mean(self.shots)

    @property
    def stdev(self) -> float:
        return statistics.pstdev(self.shots)

    def __str__(self) -> str:
        return (
            f"n={len(self.shots)} media={self.mean:.1f} "
            f"min={min(self.shots)} max={max(self.shots)} stdev={self.stdev:.1f}"
        )


def run_trial(rows: int, cols: int, ship_lengths: list[int], linear: bool, rng: random.Random) -> int:
    shapes = _linear_shapes(ship_lengths) if linear else _random_shapes(ship_lengths, rng)
    game = GameSimulator(rows, cols, shapes, rng)
    board = Board(rows, cols, shapes)
    shots = 0
    while not board.all_sunk():
        cell = next_shot(board)
        if cell is None:
            break
        result = game.shoot(cell)
        board.record_result(cell, result)
        shots += 1
        if result == 3:
            break
    return shots


def run_benchmark(
    rows: int, cols: int, ship_lengths: list[int], linear: bool, trials: int, seed: int | None = None
) -> BenchmarkResult:
    rng = random.Random(seed)
    shots = [run_trial(rows, cols, ship_lengths, linear, rng) for _ in range(trials)]
    result = BenchmarkResult(shots)
    total_cells = rows * cols
    print(
        f"Tablero {rows}x{cols}, embarcaciones {ship_lengths} "
        f"({'lineales' if linear else 'formas aleatorias'}), {trials} intentos"
    )
    print(f"  turnos: {result}")
    print(f"  celdas del tablero: {total_cells}")
    return result
