from asyncio import iscoroutinefunction

from tartiflette.types.exceptions.tartiflette import (
    UnknownDirectiveDefinition,
    NonAwaitableDirective,
)


class Directive:
    """
    This decorator allows you to link a GraphQL Directive to a Directive class.

    For example, for the following SDL:

        directive @deprecated(
            reason: String = "No longer supported"
        ) on FIELD_DEFINITION | ENUM_VALUE

    Use the Directive decorator the following way:

        @Directive("deprecated")
        class MyDirective:
            ... callbacks here ...

    """

    def __init__(self, name: str, schema):
        self.schema = schema
        try:
            self.directive = self.schema.find_directive(name)
        except KeyError:
            raise UnknownDirectiveDefinition(
                "Unknow Directive Definition %s" % name
            )

    def __call__(self, implementation):
        if not iscoroutinefunction(implementation.on_execution):
            raise NonAwaitableDirective(
                "%s is not awaitable" % repr(implementation)
            )
        self.directive.implementation = implementation
        self.schema.prepare_directives()
        return implementation