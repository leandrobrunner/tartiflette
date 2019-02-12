from typing import Any, Dict, Optional

from tartiflette.error.base import GraphQLError
from tartiflette.execution.values import coerce_variable_values
from tartiflette.json_parsing.nodes import (
    FragmentDefinitionNode,
    OperationDefinitionNode,
)
from tartiflette.validations.validation_context import ValidationContext


class ExecutionContext(ValidationContext):
    def __init__(
        self,
        schema: "GraphQLSchema",
        operation: "OperationDefinitionNode",
        fragments: Dict[str, "FragmentDefinitionNode"],
        context_value: Optional[Dict[str, Any]] = None,
        variable_values: Optional[Dict[str, Any]] = None,
        root_value: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self._schema = schema
        self._operation = operation
        self._fragments = fragments
        self._context_value = context_value
        self._variable_values = variable_values
        self._root_value = root_value

        # TODO: improve this
        self.is_introspection: bool = False

    @property
    def schema(self) -> "GraphQLSchema":
        return self._schema

    @property
    def operation(self) -> "OperationDefinitionNode":
        return self._operation

    @property
    def fragments(self) -> Dict[str, "FragmentDefinitionNode"]:
        return self._fragments

    @property
    def context_value(self) -> Optional[Dict[str, Any]]:
        return self._context_value

    @property
    def variable_values(self) -> Optional[Dict[str, Any]]:
        return self._variable_values

    @property
    def root_value(self) -> Optional[Any]:
        return self._root_value


def build_execution_context(
    schema: "GraphQLSchema",
    document: "DocumentNode",
    validation_context: "ValidationContext",
    operation_name: Optional[str] = None,
    context_value: Optional[Dict[str, Any]] = None,
    variable_values: Optional[Dict[str, Any]] = None,
    root_value: Optional[Any] = None,
) -> "ExecutionContext":
    operation: Optional["OperationDefinitionNode"] = None
    fragments: Dict[str, "FragmentDefinitionNode"] = {}

    has_multiple_assumed_operations = False

    for definition in document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            if not operation_name and operation:
                has_multiple_assumed_operations = True
            elif not operation_name or (
                definition.name and definition.name.value == operation_name
            ):
                operation = definition
        elif isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition

    if not operation:
        if operation_name:
            validation_context.add_error(
                GraphQLError(  # TODO: raise dedicated error
                    "Unknown operation named < %s >." % operation_name
                )
            )
        else:
            validation_context.add_error(
                GraphQLError(  # TODO: raise dedicated error
                    "Must provide an operation."
                )
            )
    elif has_multiple_assumed_operations:
        validation_context.add_error(
            GraphQLError(  # TODO: raise dedicated error
                "Must provide operation name if query contains multiple "
                "operations."
            )
        )

    coerced_variable_values = (
        coerce_variable_values(
            schema,
            validation_context,
            operation.variable_definitions,
            variable_values,
        )
        if operation
        else {}
    )

    return ExecutionContext(
        schema=schema,
        fragments=fragments,
        operation=operation,
        context_value=context_value,
        variable_values=coerced_variable_values,
        root_value=root_value,
    )
