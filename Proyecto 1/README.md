# Proyecto 1 - Jugador de Combate Naval

Jugador automatico para el juego de Combate Naval (ICC4201 - PDS) que se conecta
a la API del curso y dispara buscando hundir todas las embarcaciones en la menor
cantidad de turnos posible.

## Estructura

- [battleship/shapes.py](battleship/shapes.py) - parseo del campo `ships` de la API y generacion de las 4 rotaciones de una forma.
- [battleship/board.py](battleship/board.py) - estado del tablero rival: celdas conocidas (agua/toque/hundida) y embarcaciones restantes.
- [battleship/solver.py](battleship/solver.py) - eleccion de la siguiente jugada mediante un mapa de densidad de probabilidad.
- [battleship/api.py](battleship/api.py) - cliente HTTP de `/api/games/`, `/api/play/`, `/api/reset/`, `/api/game/status/`.
- [battleship/player.py](battleship/player.py) - orquesta una partida completa (cargar juego -> disparar hasta terminar).
- [battleship/simulate.py](battleship/simulate.py) - simulador local (sin red) para probar y medir el solver.
- [main.py](main.py) - CLI.

## Algoritmo

Para cada embarcacion restante (y cada una de sus 4 rotaciones posibles) se
enumeran todas las ubicaciones del tablero donde podria calzar de forma
consistente con lo ya observado (agua, toques sin hundir, hundidas, y la regla
de que dos embarcaciones nunca se tocan por una arista). Cada celda acumula un
puntaje igual a la cantidad de ubicaciones validas que la cubren, y se dispara
a la celda de mayor puntaje. Esto unifica "caza" (sin toques activos) y
"remate" (con un toque activo) en un solo mecanismo, ya que un toque activo
reduce drasticamente las ubicaciones validas y concentra el puntaje a su
alrededor.

## Uso

```bash
pip install -r requirements.txt

# listar juegos activos
python main.py list

# jugar un juego especifico (opcionalmente reiniciandolo antes)
python main.py play --game <ID> --key <KEY> --reset

# jugar todos los juegos activos reportados por la API
python main.py play-all --key <KEY>

# probar el solver localmente sin necesidad de la API (entrega parcial: formas lineales en 10x10)
python main.py simulate --rows 10 --cols 10 --ships 3 3 4 5 --linear --trials 200

# probar con formas arbitrarias y tablero de otro tamano (entrega final)
python main.py simulate --rows 15 --cols 12 --ships 2 3 3 4 5 6 --trials 100
```

La `key` tambien puede pasarse por la variable de entorno `BATTLESHIP_KEY`, y la
URL base por `BATTLESHIP_BASE_URL` (por defecto la de la API del curso).

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

Los tests verifican el parseo/rotacion de formas contra los ejemplos del
enunciado, y que el solver termina partidas simuladas (formas lineales y
arbitrarias) usando menos turnos que un jugador aleatorio.
