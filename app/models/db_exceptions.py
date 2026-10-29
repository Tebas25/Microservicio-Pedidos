class CobotNotFoundError(Exception):
    def __init__(self, id_cobot: str):
        self.id_cobot = id_cobot
        super().__init__(f"Cobot {id_cobot} doesnt exist")


class ItemAlreadyExistsError(Exception):
    def __init__(self, nombre_item: str):
        self.nombre_item = nombre_item
        super().__init__(f'Item "{nombre_item}" already exists')


class ItemNotFoundError(Exception):
    def __init__(self, nombre_item: str):
        self.nombre_item = nombre_item
        super().__init__(f"Item {nombre_item} doesn't exist")
