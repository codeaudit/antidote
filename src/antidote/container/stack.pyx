# cython: language_level=3, boundscheck=False, wraparound=False
from contextlib import contextmanager

from ..exceptions import DependencyCycleError

cdef class InstantiationStack:
    """
    Stores the stack of dependency instantiation to detect and prevent cycles
    by raising DependencyCycleError.

    Used in the DependencyContainer.

    This class is not thread-safe by itself.
    """
    def __init__(self):
        self._stack = list()
        self._dependencies = set()

    @contextmanager
    def instantiating(self, dependency_id):
        """
        Context Manager which has to be used when instantiating the
        dependency to keep track of the dependency path.

        When a cycle is detected, a DependencyCycleError is raised.
        """
        self.push(dependency_id)
        try:
            yield
        finally:
            self.pop()

    cpdef push(self, object dependency_id):
        cdef list stack
        if dependency_id in self._dependencies:
            stack = self._stack + [dependency_id]
            raise DependencyCycleError(stack)

        self._stack.append(dependency_id)
        self._dependencies.add(dependency_id)

    cpdef pop(self):
        self._dependencies.remove(self._stack.pop())
