from typing import Any

from .._internal.utils import SlotsReprMixin


class Lazy(SlotsReprMixin):
    __slots__ = ('dependency',)

    def __init__(self, dependency: Any):
        self.dependency = dependency
