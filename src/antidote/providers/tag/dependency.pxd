# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False

cdef class Tag:
    cdef:
        readonly str name
        readonly dict _attrs

cdef class Tagged:
    cdef:
        readonly str name
