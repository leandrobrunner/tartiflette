from typing import Any, Callable, Dict, Optional

from tartiflette import Directive


class NonIntrospectable:
    def __init__(self, _config):
        pass

    async def on_introspection(
        self,
        _directive_args: Dict[str, Any],
        _next_directive: Callable,
        _introspected_element: Any,
        _ctx: Optional[Dict[str, Any]],
        _info: "Info",
    ) -> None:
        return None


def bake(schema_name, config):
    sdl = "directive @nonIntrospectable on FIELD_DEFINITION"

    Directive(name="nonIntrospectable", schema_name=schema_name)(
        NonIntrospectable(config)
    )

    return sdl
