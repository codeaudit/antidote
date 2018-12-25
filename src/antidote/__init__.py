import pkg_resources as _pkg_resources

from .core import DependencyContainer, DependencyInstance, DependencyProvider
from .exceptions import (AntidoteError, DependencyCycleError,
                         DependencyInstantiationError, DependencyNotFoundError,
                         DependencyNotProvidableError, DuplicateDependencyError)
from .helpers import (attrib, context, factory, new_container, provider, register,
                      resource)
from .injection import inject, wire
from .providers import FactoryProvider, ResourceProvider, TagProvider
from .providers.factory import Build
from .providers.tag import Tag, Tagged, TaggedDependencies

try:
    __version__ = _pkg_resources.get_distribution(__name__).version
except _pkg_resources.DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass

__all__ = [
    'Build',
    'inject',
    'DependencyInstance',
    'DependencyContainer',
    'AntidoteError',
    'DependencyNotProvidableError',
    'DependencyNotFoundError',
    'DuplicateDependencyError',
    'DependencyCycleError',
    'DependencyInstantiationError',
    'Dependency',
    'FactoryProvider',
    'ResourceProvider',
    'Tag',
    'Tagged',
    'TaggedDependencies',
    'TagProvider',
    'register',
    'factory',
    'resource',
    'provider',
    'attrib',
    'context'
]

global_container = new_container()
