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
    Utility class containing all the information needed to run an end-to-end
    GraphQL request.
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
        :param schema: the GraphQLSchema schema instance linked to the engine
        :param build_response: callable in charge of returning the formatted
        GraphQL response
        :param fragments: the dictionary of fragment definition AST node
        contained in the request
        :param operation: the executable operation to execute
        :param context: value that can contain everything you need and that
        will be accessible from the resolvers
        :param root_value: an initial value corresponding to the root type
        being executed
        :param variable_values: the variables used in the GraphQL request
        :type schema: GraphQLSchema
        :type build_response: Callable
        :type fragments: Dict[str, FragmentDefinitionNode]
        :type operation: ExecutableOperationNode
        :type context: Optional[Any]
        :type root_value: Optional[Any]
        :type variable_values: Optional[Dict[str, Any]]
        """
        self.schema = schema
        self.build_response = build_response
        self.fragments = fragments
        self.operation = operation
        self.context = context
        self.root_value = root_value
        self.variable_values = variable_values
        self.errors: List["GraphQLError"] = []

        # TODO: backward compatibility old execution style
        self.is_introspection: bool = False

    def add_error(
        self,
        raw_exception: Union["GraphQLError", "MultipleException", Exception],
        path: Optional[List[str]] = None,
        locations: Optional[List["Location"]] = None,
    ) -> None:
        """
        Adds the contents of an exception to the known execution errors.
        :param raw_exception: the raw exception to treat
        :param path: the path where the raw exception occurred
        :param locations: the locations linked to the raw exception
        :type raw_exception: Union[GraphQLError, MultipleException, Exception]
        :type path: Optional[List[str]]
        :param locations: Optional[List["Location"]]
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
        Runs the execution of the executable operation.
        :return: the GraphQL response linked to the operation execution
        :rtype: Dict[str, Any]
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


async def build_execution_context(
    schema: "GraphQLSchema",
    document: "DocumentNode",
    root_value: Optional[Any],
    context: Optional[Any],
    raw_variable_values: Optional[Dict[str, Any]],
    operation_name: str,
    build_response: Callable,
) -> Tuple[Optional["ExecutionContext"], Optional[List["GraphQLError"]]]:
    """
    Factory function to build and return an ExecutionContext instance.
    :param schema: the GraphQLSchema schema instance linked to the engine
    :param document: the DocumentNode instance linked to the GraphQL request
    :param root_value: an initial value corresponding to the root type being
    executed
    :param context: value that can contain everything you need and that will be
    accessible from the resolvers
    :param raw_variable_values: the variables used in the GraphQL request
    :param operation_name: the operation name to execute
    :param build_response: callable in charge of returning the formatted
    GraphQL response
    :type schema: GraphQLSchema
    :type document: DocumentNode
    :type root_value: Optional[Any]
    :type context: Optional[Any]
    :type raw_variable_values: Optional[Dict[str, Any]]
    :type operation_name: str
    :type build_response: Callable
    :return: an ExecutionContext instance
    :rtype: Tuple[Optional[ExecutionContext], Optional[List[GraphQLError]]]
    """
    # pylint: disable=too-many-locals
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

        variable_values, variable_errors = await coerce_variable_definitions(
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
