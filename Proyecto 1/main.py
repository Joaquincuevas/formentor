"""CLI del jugador de Combate Naval (PDS Proyecto 1).

Ejemplos:
    python main.py list
    python main.py play --game 12 --key MI_KEY --reset
    python main.py play-all --key MI_KEY
    python main.py simulate --rows 10 --cols 10 --ships 3 4 5 --linear
"""

from __future__ import annotations

import argparse
import os
import sys

from battleship.api import DEFAULT_BASE_URL, BadRequestError, BattleshipAPI
from battleship.player import Player


def _require_key(args) -> str:
    key = args.key or os.environ.get("BATTLESHIP_KEY")
    if not key:
        sys.exit("Falta la key del jugador (usa --key o la variable de entorno BATTLESHIP_KEY)")
    return key


def cmd_list(args) -> None:
    api = BattleshipAPI(args.base_url)
    for game in api.list_games():
        print(game)


def cmd_play(args) -> None:
    key = _require_key(args)
    api = BattleshipAPI(args.base_url)
    if args.reset:
        api.reset(args.game, key)
    player = Player(api, args.game, key, verbose=not args.quiet)
    try:
        turns = player.play_game(max_turns=args.max_turns)
    except BadRequestError as exc:
        sys.exit(f"La API rechazo la jugada: {exc}")
    done = player.board.all_sunk()
    print(f"Juego {args.game}: {'terminado' if done else 'incompleto'} en {turns} turnos")


def cmd_play_all(args) -> None:
    key = _require_key(args)
    api = BattleshipAPI(args.base_url)
    games = api.list_games()
    total = 0
    for game in games:
        gid = game["id"]
        if args.reset:
            api.reset(gid, key)
        player = Player(api, gid, key, verbose=not args.quiet)
        try:
            turns = player.play_game(max_turns=args.max_turns)
        except BadRequestError as exc:
            print(f"Juego {gid}: error ({exc})")
            continue
        done = player.board.all_sunk()
        total += turns
        print(f"Juego {gid}: {'terminado' if done else 'incompleto'} en {turns} turnos")
    print(f"Total: {total} turnos en {len(games)} juegos")


def cmd_simulate(args) -> None:
    from battleship.simulate import run_benchmark

    run_benchmark(
        rows=args.rows,
        cols=args.cols,
        ship_lengths=args.ships,
        linear=args.linear,
        trials=args.trials,
        seed=args.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jugador de Combate Naval (PDS Proyecto 1)")
    parser.add_argument(
        "--base-url", default=os.environ.get("BATTLESHIP_BASE_URL", DEFAULT_BASE_URL)
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Lista los juegos activos (GET /api/games/)")
    p_list.set_defaults(func=cmd_list)

    p_play = sub.add_parser("play", help="Juega un juego especifico hasta terminarlo")
    p_play.add_argument("--game", required=True)
    p_play.add_argument("--key", default=None)
    p_play.add_argument("--reset", action="store_true", help="Reinicia el juego antes de jugar")
    p_play.add_argument("--max-turns", type=int, default=None)
    p_play.add_argument("--quiet", action="store_true")
    p_play.set_defaults(func=cmd_play)

    p_all = sub.add_parser("play-all", help="Juega todos los juegos activos reportados por la API")
    p_all.add_argument("--key", default=None)
    p_all.add_argument("--reset", action="store_true")
    p_all.add_argument("--max-turns", type=int, default=None)
    p_all.add_argument("--quiet", action="store_true")
    p_all.set_defaults(func=cmd_play_all)

    p_sim = sub.add_parser(
        "simulate", help="Benchmark local del solver sin necesidad de la API (para probar/afinar)"
    )
    p_sim.add_argument("--rows", type=int, default=10)
    p_sim.add_argument("--cols", type=int, default=10)
    p_sim.add_argument("--ships", type=int, nargs="+", default=[3, 3, 4, 5])
    p_sim.add_argument(
        "--linear", action="store_true", help="Fuerza formas lineales (como la entrega parcial)"
    )
    p_sim.add_argument("--trials", type=int, default=200)
    p_sim.add_argument("--seed", type=int, default=None)
    p_sim.set_defaults(func=cmd_simulate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
