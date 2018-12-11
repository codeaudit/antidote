import threading
from collections import deque
from typing import Any, Callable, Dict, Generic, Iterable, Iterator, List, Tuple, \
    TypeVar, Union

from .dependency import Tag, Tagged
# noinspection PyUnresolvedReferences
from ...container import Dependency, DependencyContainer, Instance, Provider
from ...exceptions import DuplicateTagError

T = TypeVar('T')

from functools import wraps

class TaggedDependencies(Generic[T]):
    def __init__(self, dependencies: Iterable[Tuple[Callable[..., T], Tag]]):
        self._lock = threading.Lock()
        self._instances = []  # type: List[T]
        self._tags = []  # type: List[Tag]
        self._dependencies = deque()

        for dependency, tag in dependencies:
            self._dependencies.append(dependency)
            self._tags.append(tag)

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


class TagProvider(Provider):
    def __init__(self, container: DependencyContainer):
        self._tagged_dependencies = {}  # type: Dict[str, Dict[Any, Tag]]
        self._container = container

    def __repr__(self):
        return "{}(tagged_dependencies={!r})".format(
            type(self).__name__,
            self._tagged_dependencies
        )

    def provide(self, dependency: Dependency) -> Instance:
        if isinstance(dependency, Tagged):
            return Instance(
                TaggedDependencies(
                    dependencies=(
                        ((lambda d=tagged_dependency: self._container[d]), tag)
                        for tagged_dependency, tag
                        in self._tagged_dependencies.get(dependency.name, {}).items()
                        if dependency.filter(tag)
                    ),
                ),
                # Tags are by nature dynamic. Whether the returned dependencies
                # are singletons or not is their decision to take.
                singleton=False
            )

    def register(self, dependency: Any, tags: Iterable[Union[str, Tag]]):
        for tag in tags:
            if isinstance(tag, str):
                tag = Tag(tag)

            if not isinstance(tag, Tag):
                raise ValueError("Expecting tags of type Tag, not {}".format(type(tag)))

            if tag.name not in self._tagged_dependencies:
                self._tagged_dependencies[tag.name] = {dependency: tag}
            elif dependency not in self._tagged_dependencies[tag.name]:
                self._tagged_dependencies[tag.name][dependency] = tag
            else:
                raise DuplicateTagError(tag.name)
