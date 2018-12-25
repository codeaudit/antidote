# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
from antidote.core.container cimport DependencyContainer, DependencyInstance, DependencyProvider

cdef class Tag:
    cdef:
        readonly str name
        readonly dict _attrs

cdef class Tagged:
    cdef:
        readonly str name

# cdef class TaggedDependency:
#     cdef:
#         DependencyContainer _container
#         list _dependencies
#         list _tags
#         object _lock
