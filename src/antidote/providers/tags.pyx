# cython: language_level=3, boundscheck=False, wraparound=False
from typing import (Any, Callable, Dict, Iterable, TypeVar, Union)

from .tagged_dependencies import TaggedDependencies
# @formatter:off
# noinspection PyUnresolvedReferences
from ..container cimport Dependency, DependencyContainer, Instance, Provider
# @formatter:on
from ..exceptions import DuplicateTagError

T = TypeVar('T')

cdef class Tag:
    def __init__(self, name: str, **attrs):
        self.name = name
        self._attrs = attrs

    def __getattr__(self, item):
        return self._attrs.get(item)

cdef class Tagged(Dependency):
    def __init__(self, name: str, filter: Union[Callable[[Tag], bool]] = None):
        # If filter is None -> caching works.
        # If not, dependencies are still cached if necessary.
        super().__init__(name)
        if filter is not None and not callable(filter):
            raise ValueError("filter must be either a function or None")

        self.filter = filter or (lambda _: True)  # type: Callable[[Tag], bool]

    @property
    def name(self) -> str:
        return self.id

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        return object.__eq__(self, other)

cdef class TagProvider(Provider):
    def __init__(self, container: DependencyContainer):
        self._tagged_dependencies = {}  # type: Dict[str, Dict[Any, Tag]]
        self._container = container

    def __repr__(self):
        return "{}(tagged_dependencies={!r})".format(
            type(self).__name__,
            self._tagged_dependencies
        )

    def provide(self, dependency: Dependency) -> Instance:
        cdef:
            Tag tag
            object tagged_dependency

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
