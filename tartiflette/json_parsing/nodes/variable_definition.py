from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import TypeReferencedNodeMixin


class VariableDefinitionNode(TypeReferencedNodeMixin, Node):
    KIND = "VariableDefinition"

    def __init__(
        self,
        variable: "VariableNode",
        default_value: "ValueNode",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._variable = variable
        self._default_value = default_value

    @property
    def variable(self) -> "VariableNode":
        return self._variable

    @property
    def default_value(self) -> "ValueNode":
        return self._default_value
