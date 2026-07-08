"""Cliente HTTP para la API de Combate Naval del curso."""

from __future__ import annotations

from typing import Any

import requests

DEFAULT_BASE_URL = "https://pds-battleship-f4aa1a7c95cf.herokuapp.com"


class BadRequestError(RuntimeError):
    """La API respondio 400: juego/key invalidos o fila/columna fuera del tablero."""


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    raise KeyError(f"Ninguna de las claves {keys} esta presente en {data!r}")


class BattleshipAPI:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_games(self) -> list[dict[str, Any]]:
        resp = requests.get(f"{self.base_url}/api/games/", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def play(self, game: Any, key: str, row: int, col: int) -> int:
        resp = requests.post(
            f"{self.base_url}/api/play/",
            data={"game": game, "key": key, "row": row, "col": col},
            timeout=self.timeout,
        )
        if resp.status_code == 400:
            raise BadRequestError(resp.text)
        resp.raise_for_status()
        return self._parse_play_result(resp)

    def reset(self, game: Any, key: str) -> Any:
        resp = requests.post(
            f"{self.base_url}/api/reset/",
            data={"game": game, "key": key},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def status(self, game: Any, key: str) -> dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/api/game/status/",
            params={"game": game, "key": key},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _parse_play_result(resp: requests.Response) -> int:
        # La API puede responder el entero crudo o envuelto en JSON; se
        # manejan ambos casos por robustez ya que el enunciado solo
        # especifica el significado (0/1/2/3), no el formato exacto del body.
        try:
            data = resp.json()
        except ValueError:
            return int(resp.text.strip())
        if isinstance(data, bool):
            raise ValueError(f"Respuesta de /api/play/ inesperada: {data!r}")
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            return int(_first_present(data, "result", "status", "value"))
        raise ValueError(f"Respuesta de /api/play/ inesperada: {data!r}")


def extract_board_dims(game: dict[str, Any]) -> tuple[int, int]:
    rows = _first_present(game, "board_rows", "board_row", "boardRows", "rows")
    cols = _first_present(game, "board_cols", "board_col", "boardCols", "cols")
    return int(rows), int(cols)
