from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import NamedNodeMixin


class ArgumentNode(NamedNodeMixin, Node):
    KIND = "Argument"

    def __init__(self, value: "ValueNode", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._value = value

    @property
    def value(self) -> "ValueNode":
        return self._value
