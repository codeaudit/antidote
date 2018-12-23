# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
# cython: linetrace=True
# noinspection PyUnresolvedReferences
from ..container cimport Dependency, Instance, Provider

cdef class ResourceProvider(Provider):
    cdef:
        public dict _priority_sorted_getters_by_namespace

    cpdef Instance provide(self, Dependency dependency)
