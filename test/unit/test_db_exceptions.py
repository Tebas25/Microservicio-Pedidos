from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError


def test_cobot_not_found_error_guarda_id_y_mensaje():
    exc = CobotNotFoundError("CBT999")

    assert exc.id_cobot == "CBT999"
    assert str(exc) == "Cobot CBT999 doesnt exist"


def test_item_already_exists_error_guarda_datos_y_mensaje():
    exc = ItemAlreadyExistsError("Mojito", "CBT001")

    assert exc.nombre_item == "Mojito"
    assert exc.id_cobot == "CBT001"
    assert str(exc) == 'Item "Mojito" already exists for cobot CBT001'


def test_cobot_not_found_error_es_instancia_de_exception():
    assert isinstance(CobotNotFoundError("CBT001"), Exception)


def test_item_already_exists_error_es_instancia_de_exception():
    assert isinstance(ItemAlreadyExistsError("x", "y"), Exception)