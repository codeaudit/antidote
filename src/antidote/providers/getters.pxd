# cython: language_level=3, boundscheck=False, wraparound=False
# noinspection PyUnresolvedReferences
from ..container cimport Dependency, Instance, Provider

cdef class GetterProvider(Provider):
    cdef:
        list _dependency_getters

    cpdef Instance provide(self, Dependency dependency)
