from typing import Any, Callable, Dict, Optional, Tuple

from .._internal.utils import SlotReprMixin
from ..container import Dependency, Instance, Provider
from ..exceptions import DuplicateDependencyError


class Build(Dependency):
    """
    Custom Dependency used to pass arguments to the factory used to create
    the given dependency ID.

    .. doctest::

        >>> from antidote import factory, Build, global_container
        >>> @factory(dependency_id='test')
        ... def f(name):
        ...     return {'name': name}
        >>> global_container[Build('test', name='me')]
        {'name': 'me'}

    With no arguments, that is to say :code:`Build(dependency_id)`, it is
    equivalent to :code:`dependency_id` for the
    :py:class:`~.container.DependencyContainer`.
    """
    __slots__ = ('args', 'kwargs')

    def __init__(self, *args, **kwargs):
        """
        Args:
            *args: The first argument is the dependency ID, all others are
                passed on to the factory.
            **kwargs: Passed on to the factory.
        """
        super().__init__(args[0])
        self.args = args[1:]  # type: Tuple
        self.kwargs = kwargs  # type: Dict

    def __hash__(self):
        if self.args or self.kwargs:
            try:
                # Try most precise hash first
                return hash((self.id, self.args, tuple(self.kwargs.items())))
            except TypeError:
                # If type error, return the best error-free hash possible
                return hash((self.id, len(self.args), tuple(self.kwargs.keys())))

        return hash(self.id)

    def __eq__(self, other):
        return ((not self.kwargs and not self.args
                 and (self.id is other or self.id == other))
                or (isinstance(other, Build)
                    and (self.id is other.id or self.id == other.id)
                    and self.args == other.args
                    and self.kwargs == other.kwargs))


class FactoryProvider(Provider):
    """
    Provider managing factories. Also used to register classes directly.
    """

    def __init__(self):
        self._factories = dict()  # type: Dict[Any, DependencyFactory]

    def __repr__(self):
        return (
            "{}(factories={!r})"
        ).format(
            type(self).__name__,
            tuple(self._factories.keys()),
        )

    def provide(self, dependency: Dependency) -> Optional[Instance]:
        """

        Args:
            dependency:

        Returns:

        """
        try:
            factory = self._factories[dependency.id]  # type: DependencyFactory
        except KeyError:
            return None

        if isinstance(dependency, Build):
            args = dependency.args
            kwargs = dependency.kwargs
        else:
            args = tuple()
            kwargs = dict()

        if factory.takes_dependency_id:
            args = (dependency.id,) + args

        return Instance(factory(*args, **kwargs),
                        singleton=factory.singleton)

    def register(self,
                 dependency_id,
                 factory: Callable,
                 singleton: bool = True,
                 takes_dependency_id: bool = False):
        """
        Register a factory for a dependency ID.

        Args:
            dependency_id: ID of the dependency.
            factory: Callable used to instantiate the dependency.
            singleton: Whether the dependency should be mark as singleton or
                not for the :py:class:`~..container.DependencyContainer`.
            takes_dependency_id: If True, the factory will be given the requested
                dependency ID as its first arguments. This allows re-using the
                same factory for different dependencies.
        """
        if not callable(factory):
            raise ValueError("The `factory` must be callable.")

        if dependency_id is None:
            raise ValueError("`dependency_id` parameter must be specified.")

        dependency_factory = DependencyFactory(factory=factory,
                                               singleton=singleton,
                                               takes_dependency_id=takes_dependency_id)

        if dependency_id in self._factories:
            raise DuplicateDependencyError(dependency_id)

        self._factories[dependency_id] = dependency_factory


class DependencyFactory(SlotReprMixin):
    """
    Not part of the public API.

    Only used by the FactoryProvider to store information on how the factory
    has to be used.
    """
    __slots__ = ('factory', 'singleton', 'takes_dependency_id')

    def __init__(self, factory: Callable, singleton: bool, takes_dependency_id: bool):
        self.factory = factory
        self.singleton = singleton
        self.takes_dependency_id = takes_dependency_id

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)
