import random

from battleship.board import Board
from battleship.simulate import GameSimulator, _linear_shapes, _random_shapes
from battleship.solver import next_shot


def _play_out(rows, cols, shapes, rng):
    game = GameSimulator(rows, cols, shapes, rng)
    board = Board(rows, cols, shapes)
    shots = 0
    max_shots = rows * cols
    while not board.all_sunk() and shots < max_shots:
        cell = next_shot(board)
        assert cell is not None
        result = game.shoot(cell)
        board.record_result(cell, result)
        shots += 1
        if result == 3:
            break
    return shots, board


def test_solver_finishes_linear_ships_entrega_parcial():
    rng = random.Random(1)
    shapes = _linear_shapes([3, 4, 5])
    shots, board = _play_out(10, 10, shapes, rng)
    assert board.all_sunk()
    assert shots <= 100


def test_solver_finishes_arbitrary_shapes_entrega_final():
    rng = random.Random(2)
    shapes = _random_shapes([2, 3, 3, 4, 5, 6], rng)
    shots, board = _play_out(15, 12, shapes, rng)
    assert board.all_sunk()
    assert shots <= 15 * 12


def test_solver_beats_random_baseline_on_average():
    def random_baseline_shots(rows, cols, shapes, rng):
        game = GameSimulator(rows, cols, shapes, rng)
        board = Board(rows, cols, shapes)
        shots = 0
        while not board.all_sunk():
            cell = rng.choice(board.unknown_cells())
            result = game.shoot(cell)
            board.record_result(cell, result)
            shots += 1
        return shots

    rng_solver = random.Random(42)
    rng_random = random.Random(42)
    solver_totals = []
    random_totals = []
    for _ in range(15):
        shapes = _linear_shapes([3, 3, 4, 5])
        solver_shots, _ = _play_out(10, 10, shapes, rng_solver)
        solver_totals.append(solver_shots)
        random_totals.append(random_baseline_shots(10, 10, shapes, rng_random))

    assert sum(solver_totals) < sum(random_totals)


def test_repeated_shapes_are_tracked_independently():
    # Dos embarcaciones identicas de 3 celdas: al hundir una, la otra debe
    # seguir contando como pendiente.
    rng = random.Random(3)
    shapes = _linear_shapes([3, 3])
    shots, board = _play_out(10, 10, shapes, rng)
    assert board.all_sunk()
    assert all(t.count == 0 for t in board.templates)
