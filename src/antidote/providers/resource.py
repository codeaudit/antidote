import bisect
import re
from typing import Any, Callable, Dict, List, Optional

from .._internal.utils import SlotsReprMixin
from ..core import DependencyInstance, DependencyProvider
from ..exceptions import GetterPriorityConflict


class ResourceProvider(DependencyProvider):
    """
    Provider managing resources, such as configuration, remote static content,
    etc...
    """
    def __init__(self):
        self._priority_sorted_getters_by_namespace = dict()  # type: Dict[str, List[ResourceGetter]]  # noqa

    def __repr__(self):
        return "{}(getters={!r})".format(type(self).__name__,
                                         self._priority_sorted_getters_by_namespace)

    def provide(self, dependency) -> Optional[DependencyInstance]:
        """

        Args:
            dependency:

        Returns:

        """
        if isinstance(dependency, str) and ':' in dependency:
            namespace, resource_name = dependency.split(':', 1)
            getters = self._priority_sorted_getters_by_namespace.get(namespace)
            if getters is not None:
                for getter in getters:
                    try:
                        if getter.omit_namespace:
                            instance = getter.func(resource_name)
                        else:
                            instance = getter.func(dependency)
                    except LookupError:
                        pass
                    else:
                        return DependencyInstance(instance, singleton=getter.singleton)

        return None

    def register(self,
                 resource_getter: Callable[[str], Any],
                 namespace: str,
                 priority: float = 0,
                 omit_namespace: bool = True,
                 singleton: bool = True):
        """
        Register a function used to retrieve a certain kind of resource.
        Resources must each have their own namespace which must be specified
        upon retrieval, like :code:`'<NAMESPACE>:<RESOURCE NAME>'`.

        Args:
            resource_getter: Function used to retrieve a requested dependency
                which will be given as an argument. If the dependency cannot
                be provided,  it should raise a :py:exc:`LookupError`.
            namespace: Used to identity which getter should be used with a
                dependency. It should only contain characters in
                :code:`[a-zA-Z0-9_]`.
            priority: Used to determine which getter should be called first
                when they share the same namespace. Highest priority wins.
                Defaults to 0.
            omit_namespace: Whether or not the namespace should be kept when
                passing the dependency to the :code:`resource_getter`.
                Defaults to True.
            singleton: Whether the dependency should be mark as singleton or
                not for the :py:class:`~..core.DependencyContainer`.

        """
        if not isinstance(namespace, str):
            raise ValueError(
                "namespace must be a string, not a {!r}".format(type(namespace))
            )
        elif not re.match(r'^\w+$', namespace):
            raise ValueError("namespace can only contain characters in [a-zA-Z0-9_]")

        if not isinstance(priority, (int, float)):
            raise ValueError(
                "priority must be a number, not a {!r}".format(type(priority))
            )

        getters = self._priority_sorted_getters_by_namespace.get(namespace) or []

        for g in getters:
            if g.priority == priority:
                raise GetterPriorityConflict(repr(g), repr(resource_getter))

        # Highest priority should be first
        idx = bisect.bisect([-g.priority for g in getters], -priority)
        getters.insert(idx, ResourceGetter(func=resource_getter,
                                           namespace=namespace,
                                           priority=priority,
                                           omit_namespace=omit_namespace,
                                           singleton=singleton))

        self._priority_sorted_getters_by_namespace[namespace] = getters


class ResourceGetter(SlotsReprMixin):
    """
    Not part of the public API.

    Only used by the GetterProvider to store information on how a getter has to
    be used.
    """
    __slots__ = ('func', 'omit_namespace', 'namespace_', 'priority',
                 'singleton')

    def __init__(self,
                 func: Callable[[str], Any],
                 namespace: str,
                 priority: float,
                 omit_namespace: bool,
                 singleton: bool):
        self.func = func
        self.omit_namespace = omit_namespace
        self.namespace_ = namespace
        self.singleton = singleton
        self.priority = priority
