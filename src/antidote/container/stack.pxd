#cython: language_level=3, boundscheck=False, wraparound=False

cdef class InstantiationStack:
    cdef:
        list _stack
        set _dependencies

    cpdef push(self, object dependency_id)
    cpdef pop(self)
