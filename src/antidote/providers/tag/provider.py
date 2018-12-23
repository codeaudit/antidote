import threading
from collections import deque
from typing import (Any, Callable, Deque, Dict, Generic, Iterable, Iterator, List,
                    Optional, Tuple, TypeVar, Union)

from .dependency import Tag, Tagged
# noinspection PyUnresolvedReferences
from ...container import Dependency, DependencyContainer, Instance, Provider
from ...exceptions import DuplicateTagError

T = TypeVar('T')


class TaggedDependencies(Generic[T]):
    """
    Collection containing dependencies and their tags. Dependencies are lazily
    instantiated. This is thread-safe.

    Used by :py:class:`~.TagProvider` to return the dependencies matching a tag.
    """

    def __init__(self, getter_tag_pairs: Iterable[Tuple[Callable[..., T], Tag]]):
        self._lock = threading.Lock()
        self._instances = []  # type: List[T]
        self._tags = []  # type: List[Tag]
        self._getters = deque()  # type: Deque[Callable]

        for getter, tag in getter_tag_pairs:
            self._getters.append(getter)
            self._tags.append(tag)

    def __iter__(self) -> Iterable[T]:
        return iter(self.dependencies())

    def __len__(self):
        return len(self._tags)

    def items(self) -> Iterable[Tuple[T, Tag]]:
        """
        Returns the dependencies and their associated tags.
        """
        return zip(self.dependencies(), self.tags())

    def tags(self) -> Iterable[Tag]:
        """
        Returns all the tags retrieved. This does not instantiate the
        dependencies.
        """
        return iter(self._tags)

    def dependencies(self) -> Iterator[T]:
        """
        Returns the dependencies, in a stable order for multi-threaded
        environments.
        """
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
                        getter = self._getters.popleft()
                    except IndexError:
                        pass
                    else:
                        self._instances.append(getter())
                yield self._instances[i]
            i += 1


class TagProvider(Provider):
    """
    Provider managing string tag. Tags allows one to retrieve a collection of
    dependencies marked by their creator.
    """

    def __init__(self, container: DependencyContainer):
        self._tagged_dependencies = {}  # type: Dict[str, Dict[Any, Tag]]
        self._container = container

    def __repr__(self):
        return "{}(tagged_dependencies={!r})".format(
            type(self).__name__,
            self._tagged_dependencies
        )

    def provide(self, dependency: Dependency) -> Optional[Instance]:
        """
        Returns all dependencies matching the tag name specified with a
        :py:class:`~.dependency.Tagged`. For every other case, :obj:`None` is
        returned.

        Args:
            dependency: Only :py:class:`~.dependency.Tagged` is supported, all
                others are ignored.

        Returns:
            :py:class:`~.TaggedDependencies` wrapped in a
            :py:class:`~..container.Instance`.
        """
        if isinstance(dependency, Tagged):
            return Instance(
                TaggedDependencies(
                    getter_tag_pairs=(
                        ((lambda d=tagged_dependency: self._container[d]), tag)
                        for tagged_dependency, tag
                        in self._tagged_dependencies.get(dependency.name, {}).items()
                    ),
                ),
                # Tags are by nature dynamic. Whether the returned dependencies
                # are singletons or not is their decision to take.
                singleton=False
            )

        return None

    def register(self, dependency_id, tags: Iterable[Union[str, Tag]]):
        """
        Mark a dependency with all the supplied tags. Raises
        :py:exc:`~.exceptions.DuplicateTagError` if the tag has already been
        used for this dependency ID.

        Args:
            dependency_id: dependency ID to be marked
            tags: Iterable of tags which should be associated with the
                dependency ID
        """
        for tag in tags:
            if isinstance(tag, str):
                tag = Tag(tag)

            if not isinstance(tag, Tag):
                raise ValueError("Expecting tag of type Tag, not {}".format(type(tag)))

            if tag.name not in self._tagged_dependencies:
                self._tagged_dependencies[tag.name] = {dependency_id: tag}
            elif dependency_id not in self._tagged_dependencies[tag.name]:
                self._tagged_dependencies[tag.name][dependency_id] = tag
            else:
                raise DuplicateTagError(tag.name)
