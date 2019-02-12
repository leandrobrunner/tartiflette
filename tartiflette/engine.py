import json

from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Union

from tartiflette.execution.execute import execute_operation
from tartiflette.execution.execution_context import build_execution_context
from tartiflette.json_parsing.parser import parse_document
from tartiflette.parser import TartifletteRequestParser
from tartiflette.resolver.factory import default_error_coercer
from tartiflette.schema.bakery import SchemaBakery
from tartiflette.schema.registry import SchemaRegistry
from tartiflette.validations.validation_context import ValidationContext


class Engine:
    def __init__(
        self,
        sdl: Union[str, List[str], "GraphQLSchema"],
        schema_name: str = "default",
        error_coercer: Callable[[Exception], dict] = default_error_coercer,
        custom_default_resolver: Optional[Callable] = None,
        exclude_builtins_scalars: Optional[List[str]] = None,
    ) -> None:
        # TODO: Use the kwargs and add them to the schema
        # SDL can be: raw SDL, file path, folder path, file list, schema object
        self._error_coercer = error_coercer
        self._parser = TartifletteRequestParser()
        SchemaRegistry.register_sdl(schema_name, sdl, exclude_builtins_scalars)
        self._schema = SchemaBakery.bake(
            schema_name, custom_default_resolver, exclude_builtins_scalars
        )

    async def execute(
        self,
        query: str,
        operation_name: Optional[str] = None,
        context_value: Optional[Dict[str, Any]] = None,
        variable_values: Optional[Dict[str, Any]] = None,
        root_value: Optional[Any] = None,
    ) -> dict:
        """
        Parse and execute a GraphQL request (as string).
        :param query: the GraphQL request / query as UTF8-encoded string
        :param operation_name: the operation name to execute
        :param context_value: a dict containing anything you need
        :param variable_values: the variables used in the GraphQL request
        :param root_value: an initial value corresponding to the root type being executed
        :return: a GraphQL response (as dict)
        """

        # Parse query to DocumentNode
        document: "DocumentNode" = self._query_to_ast_document(query)

        # Validate DocumentNode
        validation_context = ValidationContext()
        # TODO: apply all validation rules on document
        if validation_context.errors:
            return validation_context.error_as_graphql_response()

        # Execute query
        execution_context: "ExecutionContext" = build_execution_context(
            self._schema,
            document,
            validation_context,
            operation_name,
            context_value,
            variable_values,
            root_value,
        )

        if validation_context.errors:
            return validation_context.error_as_graphql_response()

        # Execute operation
        return await execute_operation(execution_context, self._error_coercer)

    @lru_cache(1000)
    def _query_to_ast_document(self, query: str) -> "DocumentNode":
        return parse_document(
            json.loads(self._parser.parse_and_jsonify(query))
        )
