from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from tartiflette.execution.collect import (
    collect_executable_variable_definitions,
)
from tartiflette.execution.execute import execute_operation
from tartiflette.execution.values import coerce_variable_definitions
from tartiflette.language.ast import (
    FragmentDefinitionNode,
    OperationDefinitionNode,
)
from tartiflette.types.exceptions import GraphQLError
from tartiflette.types.exceptions.tartiflette import MultipleException
from tartiflette.utils.errors import is_coercible_exception

__all__ = ["build_execution_context"]


class ExecutionContext:
    """
    TODO:
    """

    def __init__(
        self,
        schema: "GraphQLSchema",
        build_response: Callable,
        fragments: Dict[str, "FragmentDefinitionNode"],
        operation: "ExecutableOperationNode",
        context: Optional[Any],
        root_value: Optional[Any],
        variable_values: Optional[Dict[str, Any]],
    ) -> None:
        """
        TODO:
        :param schema: TODO:
        :param build_response: TODO:
        :param fragments: TODO:
        :param operation: TODO:
        :param context: TODO:
        :param root_value: TODO:
        :param variable_values: TODO:
        :type schema: TODO:
        :type build_response: TODO:
        :type fragments: TODO:
        :type operation: TODO:
        :type context: TODO:
        :type root_value: TODO:
        :type variable_values: TODO:
        """
        self.schema = schema
        self.build_response = build_response
        self.fragments = fragments
        self.operation = operation
        self.context = context
        self.root_value = root_value
        self.variable_values = variable_values
        self.errors: List["GraphQLError"] = []

        # TODO: retrocompatibility
        self.is_introspection: bool = False

    def add_error(
        self,
        raw_exception: Union["GraphQLError", "MultipleException", Exception],
        path: Optional[List[str]] = None,
        locations: Optional[List["Location"]] = None,
    ) -> None:
        """
        TODO:
        :param raw_exception: TODO:
        :param path: TODO:
        :param locations: TODO:
        :type raw_exception: TODO:
        :type path: TODO:
        :param locations: TODO:
        :return: TODO:
        :rtype: TODO:
        """
        exceptions = (
            raw_exception.exceptions
            if isinstance(raw_exception, MultipleException)
            else [raw_exception]
        )

        for exception in exceptions:
            graphql_error = (
                exception
                if is_coercible_exception(exception)
                else GraphQLError(
                    str(exception), path, locations, original_error=exception
                )
            )

            graphql_error.coerce_value = partial(
                graphql_error.coerce_value, path=path, locations=locations
            )

            self.errors.append(graphql_error)

    async def execute(self) -> Dict[str, Any]:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
        """
        return await execute_operation(self)

    async def subscribe(self) -> Dict[str, Any]:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
        """
        # run_subscription(self)
        yield {"data": {"name": "Hello"}}


def build_execution_context(
    schema: "GraphQLSchema",
    document: "DocumentNode",
    root_value: Optional[Any],
    context: Optional[Any],
    raw_variable_values: Optional[Dict[str, Any]],
    operation_name: str,
    build_response: Callable,
) -> Tuple[Optional["ExecutionContext"], Optional[List["GraphQLError"]]]:
    """
    TODO:
    :param schema: TODO:
    :param document: TODO:
    :param root_value: TODO:
    :param context: TODO:
    :param raw_variable_values: TODO:
    :param operation_name: TODO:
    :param build_response: TODO:
    :type schema: TODO:
    :type document: TODO:
    :type root_value: TODO:
    :type context: TODO:
    :type raw_variable_values: TODO:
    :type operation_name: TODO:
    :type build_response: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    errors: List["GraphQLError"] = []
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
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition

    if not operation:
        errors.append(
            GraphQLError(
                f"Unknown operation named < {operation_name} >."
                if operation_name
                else "Must provide an operation."
            )
        )
    elif has_multiple_assumed_operations:
        errors.append(
            GraphQLError(
                "Must provide operation name if query contains multiple operations."
            )
        )

    variable_values: Dict[str, Any] = {}
    if operation:
        executable_variable_definitions = collect_executable_variable_definitions(
            schema, operation.variable_definitions or []
        )

        variable_values, variable_errors = coerce_variable_definitions(
            executable_variable_definitions, raw_variable_values or {}
        )

        if variable_errors:
            errors.extend(variable_errors)

    if errors:
        return None, errors

    return (
        ExecutionContext(
            schema=schema,
            build_response=build_response,
            fragments=fragments,
            operation=operation,
            context=context,
            root_value=root_value,
            variable_values=variable_values,
        ),
        None,
    )
