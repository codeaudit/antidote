# cython: language_level=3, boundscheck=False, wraparound=False

# noinspection PyUnresolvedReferences
from .stack cimport InstantiationStack

cdef class DependencyContainer:
    cdef:
        object __weakref__
        list _providers
        dict _singletons
        object _instantiation_lock
        InstantiationStack _instantiation_stack


    cpdef object provide(self, object dependency)

cdef class Dependency:
    cdef:
        public object id

cdef class Instance:
    cdef:
        public object item
        public object singleton

cdef class Provider:
    cpdef Instance provide(self, Dependency dependency)
