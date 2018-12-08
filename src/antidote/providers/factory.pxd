# cython: language_level=3, boundscheck=False, wraparound=False
# noinspection PyUnresolvedReferences
from ..container cimport Dependency, Instance, Provider

cdef class FactoryProvider(Provider):
    cdef:
        dict _factories

    cpdef Instance provide(self, Dependency dependency)

cdef class Build(Dependency):
    cdef:
        public tuple args
        public dict kwargs
