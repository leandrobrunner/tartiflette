from typing import List, Union

from tartiflette.json_parsing.nodes.base import Node


class DocumentNode(Node):
    KIND = "Document"

    def __init__(
        self,
        definitions: List[
            Union["FragmentDefinitionNode", "OperationDefinitionNode"]
        ],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._definitions = definitions

    @property
    def definitions(
        self
    ) -> List[Union["FragmentDefinitionNode", "OperationDefinitionNode"]]:
        return self._definitions
