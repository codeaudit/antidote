# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False

cdef class Tag:
    def __init__(self, str name, **attrs):
        self.name = name
        self._attrs = attrs

    def __repr__(self):
        return "{}(name={!r}, **attrs={!r})".format(type(self).__name__,
                                                    self.name,
                                                    self._attrs)

    def __getattr__(self, item):
        return self._attrs.get(item)

cdef class Tagged:
    def __init__(self, str name):
        self.name = name

    def __repr__(self):
        return "{}(name={!r})".format(type(self).__name__, self.name)
