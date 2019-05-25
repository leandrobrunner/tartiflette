from datetime import datetime
from typing import Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import StringValueNode


class ScalarDate:
    @staticmethod
    def coerce_output(val: datetime) -> str:
        return val.isoformat().split("T")[0]

    @staticmethod
    def coerce_input(val: str) -> datetime:
        return datetime.strptime(val, "%Y-%m-%d")

    @staticmethod
    def parse_literal(ast: "Node") -> Union[datetime, "UNDEFINED_VALUE"]:
        if not isinstance(ast, StringValueNode):
            return UNDEFINED_VALUE

        try:
            return datetime.strptime(ast.value, "%Y-%m-%d")
        except Exception:  # pylint: disable=broad-except
            pass
        return UNDEFINED_VALUE
