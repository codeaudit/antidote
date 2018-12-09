# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
# cython: linetrace=True

cdef class InstantiationStack:
    cdef:
        list _stack
        set _dependencies

    cpdef push(self, object dependency_id)
    cpdef pop(self)
