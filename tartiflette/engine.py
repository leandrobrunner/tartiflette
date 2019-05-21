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
        error_coercer: Callable[[Exception], dict] = default_error_coercer,
        custom_default_resolver: Optional[Callable] = None,
        exclude_builtins_scalars: Optional[List[str]] = None,
        modules: Optional[Union[str, List[str]]] = None,
    ) -> None:
        """
        TODO:
        :param sdl: TODO:
        :param schema_name: TODO:
        :param error_coercer: TODO:
        :param custom_default_resolver: TODO:
        :param exclude_builtins_scalars: TODO:
        :param modules: TODO:
        :type sdl: TODO:
        :type schema_name: TODO:
        :type error_coercer: TODO:
        :type custom_default_resolver: TODO:
        :type exclude_builtins_scalars: TODO:
        :type modules: TODO:
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
        query: str,
        operation_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        initial_value: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        TODO:
        :param query: TODO:
        :param operation_name: TODO:
        :param context: TODO:
        :param variables: TODO:
        :param initial_value: TODO:
        :type query: TODO:
        :type operation_name: TODO:
        :type context: TODO:
        :type variables: TODO:
        :type initial_value: TODO:
        :return: TODO:
        :rtype: TODO:
        """
        print()
        document, errors = parse_and_validate_query(query)
        if errors:
            return self._build_response(errors=errors)

        execution_context, errors = build_execution_context(
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
        query: str,
        operation_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        initial_value: Optional[Any] = None,
    ) -> AsyncIterable[Dict[str, Any]]:
        """
        TODO:
        :param query: TODO:
        :param operation_name: TODO:
        :param context: TODO:
        :param variables: TODO:
        :param initial_value: TODO:
        :type query: TODO:
        :type operation_name: TODO:
        :type context: TODO:
        :type variables: TODO:
        :type initial_value: TODO:
        :return: TODO:
        :rtype: TODO:
        """
        document, errors = parse_and_validate_query(query)
        if errors:
            yield self._build_response(errors=errors)
            return

        execution_context, errors = build_execution_context(
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
