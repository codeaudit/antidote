# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
import threading
from typing import List

# @formatter:off
from cpython.ref cimport PyObject
from cpython.dict cimport PyDict_GetItem, PyDict_SetItem

# noinspection PyUnresolvedReferences
from .stack cimport InstantiationStack
# @formatter:on
from ..exceptions import (DependencyCycleError, DependencyInstantiationError)

cdef class DependencyContainer:
    def __init__(self):
        self._providers = list()  # type: List[Provider]
        self._singletons = dict()
        self._instantiation_lock = threading.RLock()
        self._instantiation_stack = InstantiationStack()

    @property
    def providers(self):
        return {type(p): p for p in self._providers}

    @property
    def singletons(self):
        return self._singletons.copy()

    def register_provider(self, provider):
        if not isinstance(provider, Provider):
            raise ValueError("Not a provider")

        self._providers.append(provider)

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

    def __setitem__(self, dependency_id, dependency):
        """
        Set a dependency in the cache.
        """
        with self._instantiation_lock:
            self._singletons[dependency_id] = dependency

    def __delitem__(self, dependency_id):
        """
        Delete a dependency in the cache.
        """
        with self._instantiation_lock:
            del self._singletons[dependency_id]

    def update(self, *args, **kwargs):
        """
        Update the cached dependencies.
        """
        with self._instantiation_lock:
            self._singletons.update(*args, **kwargs)

    def __getitem__(self, dependency):
        return self.provide(dependency)

    cpdef object provide(self, object dependency):
        """
        Low level API for Cython functions.
        """
        cdef:
            Instance instance
            Provider provider
            PyObject* result

        result = PyDict_GetItem(self._singletons, dependency)
        if result != NULL:
            return <object>result

        self._instantiation_lock.acquire()
        try:
            self._instantiation_stack.push(dependency)
            result = PyDict_GetItem(self._singletons, dependency)
            if result != NULL:
                return <object>result

            for provider in self._providers:
                instance = provider.provide(
                    dependency
                    if isinstance(dependency, Dependency) else
                    Dependency(dependency)
                )
                if instance is not None:
                    if instance.singleton:
                        self._singletons[dependency] = instance.item

                    return instance.item


        except DependencyCycleError:
            raise

        except Exception as e:
            raise DependencyInstantiationError(dependency) from e

        finally:
            self._instantiation_stack.pop()
            self._instantiation_lock.release()


cdef class Dependency:
    def __init__(self, id):
        assert id is not None
        assert not isinstance(id, Dependency)
        self.id = id

    def __repr__(self):
        return "{}(id={!r})".format(type(self).__name__, self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return (self.id == other
                or (isinstance(other, Dependency) and self.id == other.id))

cdef class Instance:
    """
    Simple wrapper which has to be used by providers when returning an
    instance of a dependency.

    This enables the container to know if the returned dependency needs to
    be cached or not (singleton).
    """
    def __init__(self, item, singleton: bool = False):  # pragma: no cover
        self.item = item
        self.singleton = singleton

    def __repr__(self):
        return "{}(item={!r}, singleton={!r})".format(type(self).__name__, self.item,
                                                      self.singleton)

cdef class Provider:
    cpdef Instance provide(self, Dependency dependency):
        raise NotImplementedError()
