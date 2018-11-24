from pkg_resources import DistributionNotFound, get_distribution

from .container import Dependency, DependencyContainer, Instance
from .exceptions import (AntidoteError, DependencyCycleError, DependencyDuplicateError,
                         DependencyInstantiationError, DependencyNotFoundError,
                         DependencyNotProvidableError)
from .manager import DependencyManager
from .injection import inject
from .providers import FactoryProvider, GetterProvider, Provider, TagProvider
from .providers.factories import Build
from .providers.tags import Tag, Tagged, TaggedDependencies

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass

__all__ = [
    'Build',
    'inject',
    'Instance',
    'DependencyContainer',
    'DependencyManager',
    'AntidoteError',
    'DependencyNotProvidableError',
    'DependencyNotFoundError',
    'DependencyDuplicateError',
    'DependencyCycleError',
    'DependencyInstantiationError',
    'Dependency',
    'FactoryProvider',
    'GetterProvider',
    'Tag',
    'Tagged',
    'TaggedDependencies',
    'TagProvider',
    'antidote'
]

antidote = DependencyManager()
