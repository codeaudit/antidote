# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
from typing import Any, Callable, Dict, Tuple

# @formatter:off
from cpython.dict cimport PyDict_GetItem
from cpython.ref cimport PyObject

from antidote.core.container cimport DependencyInstance, DependencyProvider
from ..exceptions import DuplicateDependencyError
# @formatter:on

cdef class Build:
    def __init__(self, *args, **kwargs):
        if not args:
            raise TypeError("At least the dependency and one additional argument "
                            "are mandatory.")

        self.wrapped = args[0]
        self.args = args[1:]  # type: Tuple
        self.kwargs = kwargs  # type: Dict

        if not self.args and not self.kwargs:
            raise TypeError("Without additional arguments, Build must not be used.")

    def __repr__(self):
        return "{}(id={!r}, args={!r}, kwargs={!r})".format(type(self).__name__,
                                                            self.wrapped,
                                                            self.args,
                                                            self.kwargs)

    __str__ = __repr__

    def __hash__(self):
        try:
            # Try most precise hash first
            return hash((self.wrapped, self.args, tuple(self.kwargs.items())))
        except TypeError:
            # If type error, return the best error-free hash possible
            return hash((self.wrapped, len(self.args), tuple(self.kwargs.keys())))

    def __eq__(self, object other):
        return isinstance(other, Build) \
               and (self.wrapped is other.wrapped or self.wrapped == other.wrapped) \
               and self.args == other.args \
               and self.kwargs == self.kwargs

cdef class FactoryProvider(DependencyProvider):
    bound_types = (Build,)

    def __init__(self):
        self._factories = dict()  # type: Dict[Any, Factory]

    def __repr__(self):
        return "{}(factories={!r})".format(type(self).__name__,
                                           tuple(self._factories.keys()))

    cpdef DependencyInstance provide(self, object dependency):
        cdef:
            Factory factory
            Build build
            PyObject*ptr
            object instance

        if isinstance(dependency, Build):
            build = <Build> dependency
            ptr = PyDict_GetItem(self._factories, build.wrapped)
            if ptr != NULL:
                factory = <Factory> ptr
                if factory.takes_dependency:
                    instance = factory(build.wrapped, *build.args, **build.kwargs)
                else:
                    instance = factory(*build.args, **build.kwargs)
            else:
                return
        else:
            ptr = PyDict_GetItem(self._factories, dependency)
            if ptr != NULL:
                factory = <Factory> ptr
                if factory.takes_dependency:
                    instance = factory(dependency)
                else:
                    instance = factory()
            else:
                return

        return DependencyInstance.__new__(DependencyInstance,
                                          instance,
                                          factory.singleton)

    def register(self,
                 dependency: Any,
                 factory: Callable,
                 bint singleton: bool = True,
                 bint takes_dependency: bool = False):
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

cdef class Factory:
    cdef:
        readonly object func
        readonly bint singleton
        readonly bint takes_dependency

    def __init__(self, func: Callable, singleton: bool, takes_dependency: bool):
        self.func = func
        self.singleton = singleton
        self.takes_dependency = takes_dependency

    def __repr__(self):
        return "{}(func={!r}, singleton={!r}, takes_dependency={!r})".format(
            type(self).__name__,
            self.func,
            self.singleton,
            self.takes_dependency
        )

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
