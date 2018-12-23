import threading
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional

from ._stack import InstantiationStack
from .._internal.utils import SlotReprMixin
from ..exceptions import (DependencyCycleError, DependencyInstantiationError,
                          DependencyNotFoundError)


class Dependency(SlotReprMixin):
    """
    Wrapper of the dependency ID. Its main purpose is to subclasses,
    so providers can define new kind of dependencies.
    :code:`Dependency(dependency_id)` and :code:`dependency_id` are equivalent
    for the :py:class:`~.container.DependencyContainer`.
    """
    __slots__ = ('id',)

    def __init__(self, id):
        self.id = id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return (self.id == other
                or (isinstance(other, Dependency) and self.id == other.id))


class Instance(SlotReprMixin):
    """
    Simple wrapper used by a :py:class:`~.container.Provider` when returning an
    instance of a dependency so it can specify in which scope the instance
    belongs to.
    """
    __slots__ = ('item', 'singleton')

    def __init__(self, item, singleton: bool = False):  # pragma: no cover
        self.item = item
        self.singleton = singleton


class Provider(ABC):
    """
    Abstract base class for a Provider.

    Used by the :py:class:`~.container.DependencyContainer` to instantiate
    dependencies. Several are used in a cooperative manner : the first instance
    to be returned by one of them is used. Thus providers should ideally not
    overlap and handle only one kind of dependencies such as strings or tag.

    This should be used whenever one needs to introduce a new kind of dependency,
    or control how certain dependencies are instantiated.
    """

    @abstractmethod
    def provide(self, dependency: Dependency) -> Optional[Instance]:
        """
        Method called by the :py:class:`~.container.DependencyContainer` when
        searching for a dependency.

        It is necessary to check quickly if the dependency can be provided or
        not, as :py:class:`~.container.DependencyContainer` will try its
        registered providers. A good practice is to subclass
        :py:class:`~.container.Dependency` so custom dependencies be differentiated.

        Args:
            dependency: The dependency to be provided by the provider.

        Returns:
            The requested instance wrapped in a :py:class:`~.container.Instance`
            if available or :py:obj:`None`.
        """


class DependencyContainer:
    """
    Instantiates the dependencies through the registered providers and handles
    their scope.
    """
    SENTINEL = object()

    def __init__(self):
        self._providers = list()  # type: List[Provider]
        self._singletons = dict()
        self._instantiation_lock = threading.RLock()
        self._instantiation_stack = InstantiationStack()

    def __str__(self):
        return "{}(providers=({}))".format(
            type(self).__name__,
            ", ".join("{}={}".format(name, p)
                      for name, p in self.providers.items()),
        )

    def __repr__(self):
        return "{}(providers=({}), singletons={!r})".format(
            type(self).__name__,
            ", ".join("{!r}={!r}".format(name, p)
                      for name, p in self.providers.items()),
            self._singletons
        )

    @property
    def providers(self) -> Mapping[type, Provider]:
        """
        Returns: A mapping of all the registered providers by their type.
        """
        return {type(p): p for p in self._providers}

    @property
    def singletons(self) -> dict:
        """
        Returns: All the defined singletons
        """
        return self._singletons.copy()

    def register_provider(self, provider: Provider):
        """
        Registers a provider, which can then be used to instantiate dependencies.

        Args:
            provider: Provider instance to be registered.

        """
        if not isinstance(provider, Provider):
            raise ValueError("Not a provider")

        self._providers.append(provider)

    def __setitem__(self, dependency_id, dependency):
        """
        Set a dependency in the singletons.
        """
        with self._instantiation_lock:
            self._singletons[dependency_id] = dependency

    def __delitem__(self, dependency_id):
        """
        Delete a dependency in the singletons.
        """
        with self._instantiation_lock:
            del self._singletons[dependency_id]

    def update_singletons(self, dependencies: Mapping):
        """
        Update the singletons.
        """
        with self._instantiation_lock:
            self._singletons.update(dependencies)

    def __getitem__(self, dependency_id):
        """
        Returns an instance for the given dependency ID. All registered providers
        are called sequentially until one returns an instance.  If none is found,
        :py:exc:`~.exceptions.DependencyNotFoundError` is raised.

        Args:
            dependency_id: Passed on to the registered providers.

        Returns:
            instance for the given dependency ID
        """
        instance = self.provide(dependency_id)
        if instance is self.SENTINEL:
            raise DependencyNotFoundError(dependency_id)
        return instance

    def provide(self, dependency_id):
        """
        Internal method which should not be directly called. Prefer
        :py:meth:`~.container.container.DependencyContainer.__getitem__`.
        It may be overridden in a subclass to customize how dependencies are
        instantiated.

        Used by the injection wrappers.
        """
        try:
            return self._singletons[dependency_id]
        except KeyError:
            pass

        try:
            with self._instantiation_lock, \
                    self._instantiation_stack.instantiating(dependency_id):
                try:
                    return self._singletons[dependency_id]
                except KeyError:
                    pass

                if isinstance(dependency_id, Dependency):
                    dependency = dependency_id
                else:
                    dependency = Dependency(dependency_id)

                for provider in self._providers:
                    instance = provider.provide(dependency)
                    if instance is not None:
                        if instance.singleton:
                            self._singletons[dependency_id] = instance.item

                        return instance.item

        except DependencyCycleError:
            raise

        except Exception as e:
            raise DependencyInstantiationError(dependency_id) from e

        return self.SENTINEL
