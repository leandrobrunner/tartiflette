from functools import partial
from importlib import import_module, invalidate_caches
from typing import Any, AsyncIterable, Callable, Dict, List, Optional, Union

from tartiflette.execution.collect import parse_and_validate_query
from tartiflette.execution.context import build_execution_context
from tartiflette.execution.response import build_response
from tartiflette.parser import TartifletteRequestParser
from tartiflette.resolver.factory import (
    default_error_coercer,
    error_coercer_factory,
)
from tartiflette.schema.bakery import SchemaBakery
from tartiflette.schema.registry import SchemaRegistry


def _import_modules(modules):
    if modules:
        invalidate_caches()
        return [import_module(x) for x in modules]
    return []


class Engine:
    def __init__(
        self,
        sdl: Union[str, List[str]],
        schema_name: str = "default",
        error_coercer: Callable[
            [Exception], Dict[str, Any]
        ] = default_error_coercer,
        custom_default_resolver: Optional[Callable] = None,
        exclude_builtins_scalars: Optional[List[str]] = None,
        modules: Optional[Union[str, List[str]]] = None,
    ) -> None:
        """
        Create an engine by analyzing the SDL and connecting it with the
        imported Resolver, Mutation, Subscription, Directive and Scalar linking
        them through the schema name.
        :param sdl: path or list of path to the files / directories containing
        the SDL
        :param schema_name: name of the SDL
        :param error_coercer: callable in charge of transforming a couple
        Exception/error into an error dictionary
        :param custom_default_resolver: callable that will replace the builtin
        default_resolver (called as resolver for each UNDECORATED field)
        :param exclude_builtins_scalars: list of string containing the names of
        the builtin scalar you don't want to be automatically included, usually
        it's Date, DateTime or Time scalars
        :param modules: list of string containing the name of the modules you
        want the engine to import, usually this modules contains your
        Resolvers, Directives, Scalar or Subscription code
        :type sdl: Union[str, List[str]]
        :type schema_name: str
        :type error_coercer: Callable[[Exception], Dict[str, Any]]
        :type custom_default_resolver: Optional[Callable]
        :type exclude_builtins_scalars: Optional[List[str]]
        :type modules: Optional[Union[str, List[str]]]
        """
        if isinstance(modules, str):
            modules = [modules]

        self._modules = _import_modules(modules)
        self._parser = TartifletteRequestParser()
        SchemaRegistry.register_sdl(schema_name, sdl, exclude_builtins_scalars)
        self._schema = SchemaBakery.bake(
            schema_name, custom_default_resolver, exclude_builtins_scalars
        )
        self._build_response = partial(
            build_response, error_coercer=error_coercer_factory(error_coercer)
        )

    async def execute(
        self,
        query: Union[str, bytes],
        operation_name: Optional[str] = None,
        context: Optional[Any] = None,
        variables: Optional[Dict[str, Any]] = None,
        initial_value: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parses and executes a GraphQL query/mutation request.
        :param query: the GraphQL request / query as UTF8-encoded string
        :param operation_name: the operation name to execute
        :param context: value that can contain everything you need and that
        will be accessible from the resolvers
        :param variables: the variables used in the GraphQL request
        :param initial_value: an initial value corresponding to the root type
        being executed
        :type query: Union[str, bytes]
        :type operation_name: Optional[str]
        :type context: Optional[Any]
        :type variables: Optional[Dict[str, Any]]
        :type initial_value: Optional[Any]
        :return: computed response corresponding to the request
        :rtype: Dict[str, Any]
        """
        print()
        document, errors = parse_and_validate_query(query)
        if errors:
            return self._build_response(errors=errors)

        execution_context, errors = await build_execution_context(
            self._schema,
            document,
            initial_value,
            context,
            variables,
            operation_name,
            self._build_response,
        )

        return (
            self._build_response(errors=errors)
            if errors
            else await execution_context.execute()
        )

    async def subscribe(
        self,
        query: Union[str, bytes],
        operation_name: Optional[str] = None,
        context: Optional[Any] = None,
        variables: Optional[Dict[str, Any]] = None,
        initial_value: Optional[Any] = None,
    ) -> AsyncIterable[Dict[str, Any]]:
        """
        Parses and executes a GraphQL subcription request.
        :param query: the GraphQL request / query as UTF8-encoded string
        :param operation_name: the operation name to execute
        :param context: value that can contain everything you need and that
        will be accessible from the resolvers
        :param variables: the variables used in the GraphQL request
        :param initial_value: an initial value corresponding to the root type
        being executed
        :type query: Union[str, bytes]
        :type operation_name: Optional[str]
        :type context: Optional[Any]
        :type variables: Optional[Dict[str, Any]]
        :type initial_value: Optional[Any]
        :return: computed response corresponding to the request
        :rtype: AsyncIterable[Dict[str, Any]]
        """
        # pylint: disable=too-many-locals
        document, errors = parse_and_validate_query(query)
        if errors:
            yield self._build_response(errors=errors)
            return

        execution_context, errors = await build_execution_context(
            self._schema,
            document,
            initial_value,
            context,
            variables,
            operation_name,
            self._build_response,
        )
        if errors:
            yield self._build_response(errors=errors)
            return

        async for result in execution_context.subscribe():
            yield result
