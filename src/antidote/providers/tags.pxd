# cython: language_level=3, boundscheck=False, wraparound=False
# noinspection PyUnresolvedReferences
from ..container cimport DependencyContainer, Dependency, Instance, Provider

cdef class Tag:
    cdef:
        readonly str name
        dict _attrs

cdef class Tagged(Dependency):
    cdef:
        public object filter

cdef class TagProvider(Provider):
    cdef:
        dict _tagged_dependencies
        DependencyContainer _container
