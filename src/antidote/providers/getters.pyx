# cython: language_level=3, boundscheck=False, wraparound=False
from typing import Any, Callable, List

# @formatter:off
from libcpp cimport bool as cbool

# noinspection PyUnresolvedReferences
from ..container cimport Dependency, Instance, Provider
from ..exceptions import GetterNamespaceConflict
# @formatter:on


cdef class GetterProvider(Provider):
    """
    Provider managing constant parameters like configuration.
    """
    def __init__(self):
        self._dependency_getters = []  # type: List[DependencyGetter]

    def __repr__(self):
        return "{}(getters={!r})".format(type(self).__name__, self._dependency_getters)

    cpdef Instance provide(self, Dependency dependency):
        """
        Provide the parameter associated with the dependency_id.

        Args:
            dependency: dependency to provide.

        Returns:
            A :py:class:`~.container.Instance` wrapping the built instance for
            the dependency.
        """
        cdef:
            DependencyGetter getter
            object instance

        if isinstance(dependency.id, str):
            for getter in self._dependency_getters:
                if dependency.id.startswith(getter.namespace_):
                    try:
                        instance = getter.get(dependency.id)
                    except LookupError:
                        break
                    else:
                        return Instance(instance, singleton=getter.singleton)

    def register(self,
                 getter: Callable[[str], Any],
                 namespace: str,
                 omit_namespace: bool = False,
                 singleton: bool = True):
        """
        Register parameters with its getter.

        Args:
            getter: Function used to retrieve a requested dependency which will
                be given as an argument. If the dependency cannot be provided,
                it should raise a :py:exc:`LookupError`.
            namespace: Used to identity which getter should be used with a
                dependency, as such they have to be mutually exclusive.
            omit_namespace: Whether or the namespace should be removed from the
                dependency name which is given to the getter. Defaults to False.

        """
        if not isinstance(namespace, str):
            raise ValueError("prefix must be a string")

        for g in self._dependency_getters:
            if g.namespace_.startswith(namespace) or namespace.startswith(g.namespace_):
                raise GetterNamespaceConflict(g.namespace_, namespace)

        self._dependency_getters.append(DependencyGetter(getter=getter,
                                                         namespace=namespace,
                                                         omit_namespace=omit_namespace,
                                                         singleton=singleton))

cdef class DependencyGetter:
    cdef:
        public str namespace_
        public object singleton
        object _getter
        cbool _omit_namespace

    def __init__(self,
                 getter: Callable[[str], Any],
                 namespace: str,
                 omit_namespace: bool,
                 singleton: bool):
        self._getter = getter
        self._omit_namespace = omit_namespace
        self.namespace_ = namespace
        self.singleton = singleton

    cdef object get(self, str name):
        if self._omit_namespace:
            name = name[len(self.namespace_):]
        return self._getter(name)
