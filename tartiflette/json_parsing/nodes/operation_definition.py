from typing import List

from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    NamedNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
)


class OperationDefinitionNode(
    NamedNodeMixin, WithDirectivesNodeMixin, WithSelectionSetNodeMixin, Node
):
    KIND = "OperationDefinition"

    def __init__(
        self,
        operation: str,
        variable_definitions: List["VariableDefinitionNode"],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._operation = operation
        self._variable_definitions = variable_definitions

    def __repr__(self) -> str:
        return "<%s operation=%s>" % (self.KIND, self._operation)

    @property
    def operation(self) -> str:
        return self._operation

    @property
    def variable_definitions(self) -> List["VariableDefinitionNode"]:
        return self._variable_definitions

    @property
    def allow_parallelization(self) -> bool:
        return self._operation != "mutation"
