"""Handles context information containers."""
import os
import tempfile

import attr

_DEFAULT_DIRECTORY = os.path.join(tempfile.gettempdir(), 'example_pipeline')


@attr.s(slots=True, frozen=True)
class ExecutionContext:
    """Immutable storage of execution context and parameters."""

    # Execution parameters
    reference_location: str = attr.ib(convert=os.path.realpath)
    sample_location: str = attr.ib(convert=os.path.realpath)
    output: str = attr.ib(convert=os.path.realpath)
    threads: int = attr.ib()

    # Computed attributes
    directory: str = attr.ib(default=_DEFAULT_DIRECTORY, init=False)

    def path(self, *local_path: str) -> str:
        """Make directory tree from a given path and return full path."""
        filepath = os.path.join(self.directory, *local_path)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        return filepath
