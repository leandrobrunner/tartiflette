from typing import Any, Optional


class GraphQLType:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_not_null: Optional[bool] = False,
        is_list: Optional[bool] = False,
        is_enum_value: Optional[bool] = False,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        self.name = name
        self.description = description
        self._is_list = is_list
        self._is_not_null = is_not_null
        self._is_enum_value = is_enum_value
        self._schema = schema
        self._introspection_directives = None

    def __eq__(self, other: Any) -> bool:
        return self is other or (
            type(self) is type(other) and self.name == other.name
        )

    def __repr__(self) -> str:
        return "{}(name={!r}, description={!r})".format(
            self.__class__.__name__, self.name, self.description
        )

    def __str__(self) -> str:
        return "{!s}".format(self.name)

    @property
    def is_list(self) -> bool:
        return self._is_list

    @property
    def is_not_null(self) -> bool:
        return self._is_not_null

    @property
    def is_enum_value(self) -> bool:
        return self._is_enum_value

    @property
    def is_union(self) -> bool:
        return False

    @property
    def contains_not_null(self) -> bool:
        return False

    @property
    def contains_a_list(self) -> bool:
        return False

    @property
    def schema(self) -> Optional["GraphQLSchema"]:
        return self._schema

    @property
    def introspection_directives(self):
        return self._introspection_directives

    def bake(self, schema: "GraphQLSchema") -> None:
        self._schema = schema

    # Introspection attributes
    @property
    def ofType(self) -> None:  # pylint: disable=invalid-name
        return None

    @property
    def kind(self) -> str:
        return "TYPE"
