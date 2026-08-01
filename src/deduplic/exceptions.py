"""
Custom exceptions and warnings for the Deduplic package.

This module defines the hierarchy of domain-specific errors and warnings
used across all layers of the library.
"""


# 1. BASE CLASSES

class DeduplicError(Exception):
    """
    Base exception for all errors raised directly by the Deduplic library.
    
    Any custom exception in this package inherits from this class, allowing
    users to catch all package-specific errors using:
        `except DeduplicError:`
    """
    pass


class DeduplicWarning(UserWarning):
    """
    Base warning for all non-fatal anomalies reported by the Deduplic library.
    
    Users can filter or capture package warnings using Python's standard
    `warnings` module.
    """
    pass


# 2. SPECIFIC ERRORS

class DedupAdapterError(DeduplicError, ValueError):
    """
    Raised when input data cannot be normalized, loaded, or adapted.
    
    Inherits from ValueError for compatibility with standard validation logic.
    """
    pass


class DeduplicConfigError(DeduplicError, ValueError):
    """
    Raised when an invalid configuration or setting value is provided.
    """
    pass


class ClusterSafetyError(DeduplicError, RuntimeError):
    """
    Raised when a graph cluster or matrix exceeds safety/memory limits.
    
    Inherits from RuntimeError to signal execution boundaries.
    """
    pass

class DeduplicFileNotFoundError(DeduplicError, FileNotFoundError):
    """Raised when a required project or corpus file does not exist."""
    pass

class DeduplicIndexError(DeduplicError, IndexError):
    """Raised when a required project or corpus file does not exist."""
    pass


# 3. SPECIFIC WARNINGS

class CorruptDataWarning(DeduplicWarning):
    """
    Emitted when corrupt, invalid, or non-conforming entries are skipped
    during data processing without stopping the pipeline.
    """
    pass