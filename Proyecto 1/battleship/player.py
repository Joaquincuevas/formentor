"""Orquesta una partida completa contra la API: carga el juego, dispara hasta
hundir todas las embarcaciones (o hasta agotar un limite de turnos)."""

from __future__ import annotations

from .api import BattleshipAPI, extract_board_dims
from .board import Board
from .shapes import parse_ships
from .solver import next_shot

RESULT_NAMES = {0: "agua", 1: "toque", 2: "hundida", 3: "hundida (fin del juego)"}


class Player:
    def __init__(self, api: BattleshipAPI, game_id, key: str, verbose: bool = True):
        self.api = api
        self.game_id = game_id
        self.key = key
        self.verbose = verbose
        self.board: Board | None = None

    def load_game(self) -> None:
        games = self.api.list_games()
        game = next((g for g in games if str(g["id"]) == str(self.game_id)), None)
        if game is None:
            raise ValueError(f"No se encontro el juego {self.game_id!r} en /api/games/")
        rows, cols = extract_board_dims(game)
        ships = parse_ships(game["ships"])
        self.board = Board(rows, cols, ships)

    def play_turn(self) -> tuple[tuple[int, int], int]:
        if self.board is None:
            raise RuntimeError("Debe llamar a load_game() antes de jugar")
        cell = next_shot(self.board)
        if cell is None:
            raise RuntimeError("No quedan celdas por disparar pero el juego no termino")
        row, col = cell
        result = self.api.play(self.game_id, self.key, row, col)
        self.board.record_result(cell, result)
        if self.verbose:
            print(f"  disparo ({row}, {col}) -> {result} [{RESULT_NAMES.get(result, '?')}]")
        return cell, result

    def play_game(self, max_turns: int | None = None) -> int:
        if self.board is None:
            self.load_game()
        turns = 0
        while not self.board.all_sunk():
            if max_turns is not None and turns >= max_turns:
                break
            _, result = self.play_turn()
            turns += 1
            if result == 3:
                break
        return turns
