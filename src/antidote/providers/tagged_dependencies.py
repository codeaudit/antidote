import threading
from collections import deque
from typing import (Callable, Generic, Iterable, Iterator, List, Tuple,
                    TypeVar)

from .tags import Tag

T = TypeVar('T')


class TaggedDependencies(Generic[T]):
    def __init__(self, dependencies: Iterable[Tuple[Callable[..., T], Tag]]):
        self._instances = []  # type: List[T]
        self._tags = []  # type: List[Tag]
        self._dependencies = deque()

        for dependency, tag in dependencies:
            self._dependencies.append(dependency)
            self._tags.append(tag)

        self._lock = threading.Lock()

    def __iter__(self) -> Iterable[T]:
        return iter(self.dependencies())

    def __len__(self):
        return len(self._tags)

    def items(self) -> Iterable[Tuple[T, Tag]]:
        return zip(self.dependencies(), self.tags())

    def tags(self) -> Iterable[Tag]:
        return iter(self._tags)

    def dependencies(self) -> Iterator[T]:
        i = -1
        for i, dependency in enumerate(self._instances):
            yield dependency

        i += 1

        while i < len(self):
            try:
                yield self._instances[i]
            except IndexError:
                with self._lock:
                    try:
                        getter = self._dependencies.popleft()
                    except IndexError:
                        pass
                    else:
                        self._instances.append(getter())
                yield self._instances[i]
            i += 1
