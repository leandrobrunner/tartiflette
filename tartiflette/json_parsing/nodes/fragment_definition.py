from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    NamedNodeMixin,
    TypeConditionedNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
)


class FragmentDefinitionNode(
    NamedNodeMixin,
    TypeConditionedNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
    Node,
):
    KIND = "FragmentDefinition"
