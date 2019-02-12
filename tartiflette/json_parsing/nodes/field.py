from typing import Optional

from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    NamedNodeMixin,
    WithArgumentsNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
)


class FieldNode(
    NamedNodeMixin,
    WithArgumentsNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
    Node,
):
    KIND = "Field"

    def __init__(self, alias: Optional[str] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._alias: "NameNode" = alias

    def __repr__(self) -> str:
        return "<%s name=%s alias=%s>" % (
            self.KIND,
            self._name.value,
            self._alias.value if self._alias else None,
        )

    @property
    def alias(self) -> Optional[str]:
        return self._alias

    @property
    def response_key(self) -> str:
        if self._alias:
            return self._alias.value
        return self._name.value
