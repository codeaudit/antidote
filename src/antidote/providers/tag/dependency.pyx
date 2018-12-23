# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
# cython: linetrace=True

# @formatter:off
# noinspection PyUnresolvedReferences
from ...container cimport Dependency, DependencyContainer, Instance, Provider
# @formatter:on

cdef class Tag:
    def __init__(self, str name, **attrs):
        self.name = name
        self._attrs = attrs

    def __repr__(self):
        return "{}(name={!r}, **attrs={!r})".format(type(self).__name__,
                                                    self.id,
                                                    self._attrs)

    def __getattr__(self, item):
        return self._attrs.get(item)

cdef class Tagged(Dependency):
    def __init__(self, str name):
        super().__init__(name)

    def __repr__(self):
        return "{}(name={!r})".format(type(self).__name__, self.id)

    @property
    def name(self) -> str:
        return self.id

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, object other):
        return object.__eq__(self, other)
