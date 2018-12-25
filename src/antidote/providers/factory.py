from typing import Any, Callable, Dict, Optional, Tuple

from .._internal.utils import SlotsReprMixin
from ..core import DependencyInstance, DependencyProvider
from ..exceptions import DuplicateDependencyError


class Build(SlotsReprMixin):
    """
    Custom Dependency wrapper used to pass arguments to the factory used to
    create the actual dependency.

    .. doctest::

        >>> from antidote import Build, factory, global_container
        >>> @factory(dependency='test')
        ... def f(name):
        ...     return {'name': name}
        >>> global_container[Build('test', name='me')]
        {'name': 'me'}

    With no arguments, that is to say :code:`Build(x)`, it is equivalent to
    :code:`x` for the :py:class:`~.core.DependencyContainer`.
    """
    __slots__ = ('wrapped', 'args', 'kwargs')

    __str__ = SlotsReprMixin.__repr__

    def __init__(self, *args, **kwargs):
        """
        Args:
            *args: The first argument is the dependency, all others are passed
                on to the factory.
            **kwargs: Passed on to the factory.
        """
        if not args:
            raise TypeError("At least the dependency and one additional argument "
                            "are mandatory.")

        self.wrapped = args[0]
        self.args = args[1:]  # type: Tuple
        self.kwargs = kwargs  # type: Dict

        if not self.args and not self.kwargs:
            raise TypeError("Without additional arguments, Build must not be used.")

    def __hash__(self):
        try:
            # Try most precise hash first
            return hash((self.wrapped, self.args, tuple(self.kwargs.items())))
        except TypeError:
            # If type error, return the best error-free hash possible
            return hash((self.wrapped, len(self.args), tuple(self.kwargs.keys())))

    def __eq__(self, other):
        return isinstance(other, Build) \
               and (self.wrapped is other.wrapped or self.wrapped == other.wrapped) \
               and self.args == other.args \
               and self.kwargs == self.kwargs


class FactoryProvider(DependencyProvider):
    """
    Provider managing factories. Also used to register classes directly.
    """
    bound_types = (Build,)

    def __init__(self):
        self._factories = dict()  # type: Dict[Any, Factory]

    def __repr__(self):
        return "{}(factories={!r})".format(type(self).__name__,
                                           tuple(self._factories.keys()))

    def provide(self, dependency) -> Optional[DependencyInstance]:
        """

        Args:
            dependency:

        Returns:

        """
        if isinstance(dependency, Build):
            key = dependency.wrapped
        else:
            key = dependency

        try:
            factory = self._factories[key]  # type: Factory
        except KeyError:
            return None

        if isinstance(dependency, Build):
            args = dependency.args
            kwargs = dependency.kwargs
        else:
            args = tuple()
            kwargs = dict()

        if factory.takes_dependency:
            args = (key,) + args

        return DependencyInstance(factory(*args, **kwargs),
                                  singleton=factory.singleton)

    def register(self,
                 dependency: Any,
                 factory: Callable,
                 singleton: bool = True,
                 takes_dependency: bool = False):
        """
        Register a factory for a dependency.

        Args:
            dependency: dependency to register.
            factory: Callable used to instantiate the dependency.
            singleton: Whether the dependency should be mark as singleton or
                not for the :py:class:`~..core.DependencyContainer`.
            takes_dependency: If True, the factory will be given the requested
                dependency as its first arguments. This allows re-using the
                same factory for different dependencies.
        """
        if not callable(factory):
            raise ValueError("The `factory` must be callable.")

        if dependency is None:
            raise ValueError("`dependency` parameter must be specified.")

        factory_ = Factory(func=factory,
                           singleton=singleton,
                           takes_dependency=takes_dependency)

        if dependency in self._factories:
            raise DuplicateDependencyError(dependency)

        self._factories[dependency] = factory_


class Factory(SlotsReprMixin):
    """
    Not part of the public API.

    Only used by the FactoryProvider to store information on how the factory
    has to be used.
    """
    __slots__ = ('func', 'singleton', 'takes_dependency')

    def __init__(self, func: Callable, singleton: bool, takes_dependency: bool):
        self.func = func
        self.singleton = singleton
        self.takes_dependency = takes_dependency

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
