from typing import List, Optional, Union


class NamedNodeMixin:
    def __init__(self, name: "NameNode", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._name = name

    @property
    def name(self) -> "NameNode":
        return self._name


class TypeConditionedNodeMixin:
    def __init__(
        self, type_condition: "NamedTypeNode", *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._type_condition = type_condition

    @property
    def type_condition(self) -> "NamedTypeNode":
        return self._type_condition


class TypeReferencedNodeMixin:
    def __init__(
        self,
        type_reference: Union[
            "NonNullTypeNode", "ListTypeNode", "NamedTypeNode"
        ],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._type_reference = type_reference

    @property
    def type_reference(
        self
    ) -> Union["NonNullTypeNode", "ListTypeNode", "NamedTypeNode"]:
        return self._type_reference


class WithArgumentsNodeMixin:
    def __init__(
        self, arguments: List["ArgumentNode"], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._arguments = arguments

    @property
    def arguments(self) -> List["ArgumentNode"]:
        return self._arguments


class WithDirectivesNodeMixin:
    def __init__(
        self, directives: List["DirectiveNode"], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._directives = directives

    @property
    def directives(self) -> List["DirectiveNode"]:
        return self._directives


class WithSelectionSetNodeMixin:
    def __init__(
        self, selection_set: Optional["SelectionSetNode"], *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._selection_set = selection_set

    @property
    def selection_set(self) -> Optional["SelectionSetNode"]:
        return self._selection_set
