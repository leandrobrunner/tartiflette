from typing import Any, List

from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import NamedNodeMixin


class ValueNode(Node):
    def __init__(self, value: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._value = value

    @property
    def value(self):
        return self._value


class BooleanValueNode(ValueNode):
    KIND = "BooleanValue"


class EnumValueNode(ValueNode):
    KIND = "EnumValue"


class FloatValueNode(ValueNode):
    KIND = "FloatValue"


class IntValueNode(ValueNode):
    KIND = "IntValue"


class NullValueNode(ValueNode):
    KIND = "NullValue"


class StringValueNode(ValueNode):
    KIND = "StringValue"


class ListValueNode(Node):
    KIND = "ListValue"

    def __init__(self, values: List["ValueNode"], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._values = values

    @property
    def values(self) -> List["ValueNode"]:
        return self._values


class ObjectFieldNode(NamedNodeMixin, ValueNode):
    KIND = "ObjectField"


class ObjectValueNode(Node):
    KIND = "ObjectValue"

    def __init__(
        self, fields: List["ObjectFieldNode"], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._fields = fields

    @property
    def fields(self) -> List["ObjectFieldNode"]:
        return self._fields
