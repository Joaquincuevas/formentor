from battleship.shapes import all_rotations, parse_ship, parse_ships


def test_parse_ship_simple():
    shape = parse_ship("XX")
    assert shape == frozenset({(0, 0), (0, 1)})


def test_parse_five_ships_example_from_enunciado():
    # Ejemplo textual del enunciado (Figura 2, tablero derecho):
    # "XX|XXXX,X--X,XXXX|-XX,XX-|XXX,X--,X--|X--,X--,XXX,X--"
    ships_str = "XX|XXXX,X--X,XXXX|-XX,XX-|XXX,X--,X--|X--,X--,XXX,X--"
    ships = parse_ships(ships_str)
    assert len(ships) == 5
    assert [len(s) for s in ships] == [2, 10, 4, 5, 6]


def test_rotations_of_asymmetric_shape_are_four():
    # Figura 3 del enunciado: "--X-,X-XX,XXX-"
    shape = parse_ship("--X-,X-XX,XXX-")
    assert len(shape) == 7
    rotations = all_rotations(shape)
    assert len(rotations) == 4


def test_rotations_of_symmetric_shape_can_repeat():
    # Un cuadrado 2x2 es igual en sus 4 rotaciones.
    shape = parse_ship("XX,XX")
    rotations = all_rotations(shape)
    assert len(rotations) == 1


def test_linear_shape_has_two_distinct_rotations():
    shape = parse_ship("XXX")
    rotations = all_rotations(shape)
    assert len(rotations) == 2  # horizontal y vertical
