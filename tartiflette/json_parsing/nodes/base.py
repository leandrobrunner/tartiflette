from typing import Optional


class Node:
    KIND: Optional[str] = None

    def __init__(self, location: "Location") -> None:
        self._location = location

    def __repr__(self):
        return "<%s>" % self.KIND or "UndefinedNode"

    @property
    def kind(self) -> Optional[str]:
        return self.KIND

    @property
    def location(self) -> "Location":
        return self._location
