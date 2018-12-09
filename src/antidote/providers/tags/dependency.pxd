# cython: language_level=3, boundscheck=False, wraparound=False
# noinspection PyUnresolvedReferences
from ...container cimport Dependency, DependencyContainer, Instance, Provider

cdef class Tag:
    cdef:
        readonly str name
        readonly dict _attrs

cdef class Tagged(Dependency):
    cdef:
        public object filter
