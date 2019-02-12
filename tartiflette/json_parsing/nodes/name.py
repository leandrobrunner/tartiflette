from tartiflette.json_parsing.nodes.base import Node


class NameNode(Node):
    KIND = "Name"

    def __init__(self, value: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._value = value

    @property
    def value(self) -> str:
        return self._value
