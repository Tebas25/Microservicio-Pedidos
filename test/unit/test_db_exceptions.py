"""Pruebas unitarias de las excepciones de base de datos."""
import pytest

from app.models.db_exceptions import (
    CobotNotFoundError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
)


# ---------- CobotNotFoundError ----------

def test_cobot_not_found_guarda_el_id():
    assert CobotNotFoundError("cobot-1").id_cobot == "cobot-1"


def test_cobot_not_found_tiene_un_mensaje_con_el_id():
    assert str(CobotNotFoundError("cobot-1")) == "Cobot cobot-1 doesnt exist"


# ---------- ItemAlreadyExistsError ----------

def test_item_already_exists_guarda_el_nombre():
    assert ItemAlreadyExistsError("Mojito").nombre_item == "Mojito"


def test_item_already_exists_tiene_un_mensaje_con_el_nombre_entre_comillas():
    assert str(ItemAlreadyExistsError("Mojito")) == 'Item "Mojito" already exists'


# ---------- ItemNotFoundError ----------

def test_item_not_found_guarda_el_nombre():
    assert ItemNotFoundError("Mojito").nombre_item == "Mojito"


def test_item_not_found_tiene_un_mensaje_con_el_nombre():
    assert str(ItemNotFoundError("Mojito")) == "Item Mojito doesn't exist"


# ---------- comportamiento común ----------

@pytest.mark.parametrize("excepcion", [
    CobotNotFoundError("x"),
    ItemAlreadyExistsError("x"),
    ItemNotFoundError("x"),
])
def test_son_excepciones_que_se_pueden_lanzar_y_capturar(excepcion):
    with pytest.raises(type(excepcion)) as exc:
        raise excepcion

    assert exc.value is excepcion


@pytest.mark.parametrize("clase, argumento", [
    (CobotNotFoundError, "cobot-1"),
    (ItemAlreadyExistsError, "Mojito"),
    (ItemNotFoundError, "Mojito"),
])
def test_el_mensaje_es_el_unico_argumento_de_la_excepcion(clase, argumento):
    excepcion = clase(argumento)

    assert excepcion.args == (str(excepcion),)


def test_las_tres_excepciones_son_independientes_entre_si():
    """Los `except` de los endpoints dependen de que no hereden unas de otras."""
    clases = [CobotNotFoundError, ItemAlreadyExistsError, ItemNotFoundError]

    for a in clases:
        for b in clases:
            if a is not b:
                assert not issubclass(a, b)


@pytest.mark.parametrize("nombre", ["Piña colada", 'Con "comillas"', "", "x" * 300])
def test_aceptan_nombres_con_caracteres_especiales(nombre):
    assert nombre in str(ItemAlreadyExistsError(nombre))
    assert nombre in str(ItemNotFoundError(nombre))