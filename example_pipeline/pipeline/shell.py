"""Functions for running shell commands."""
import logging
import os
import shlex
import subprocess
import textwrap
from typing import List

import attr

LOG = logging.getLogger('example_pipeline')


@attr.s(slots=True, frozen=True)
class RunResult:
    """Immutable storage container for stdout, stderr and return code.

    Stores results of shell command and has functions for writing them to file.
    """

    stdout: str = attr.ib()
    stderr: str = attr.ib()
    exit_code: int = attr.ib()

    @staticmethod
    def _ensure_dir(filepath):
        """Ensure that directory exists."""
        path = os.path.dirname(filepath)
        os.makedirs(path, exist_ok=True)

    def write_stdout(self, path):
        """Write stdout to file."""
        self._ensure_dir(path)
        with open(path, 'w') as f:
            f.write(self.stdout)

    def write_stderr(self, path):
        """Write stderr to file."""
        self._ensure_dir(path)
        with open(path, 'w') as f:
            f.write(self.stderr)


def _stringify_args(arg) -> List[str]:
    """Cast cli argument as string.

    if argument is not string, int or float raise error.
    """
    if isinstance(arg, (str, int, float)):
        return str(arg)
    raise TypeError


def run_shell_cmd(args):
    """Run shell commands and return stdout and stderr."""
    args = [_stringify_args(arg) for arg in args]

    cmd = ' '.join(shlex.quote(arg) for arg in args)
    LOG.info('[running] %s' % cmd)

    proc = subprocess.Popen(args, universal_newlines=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    rv = RunResult(stdout=stdout, stderr=stderr, exit_code=proc.returncode)

    if rv.exit_code != 0:
        msg = textwrap.dedent("""
        {cmd}
        returned non-zero exit code {exit_code}
        *stdout*
        {stdout}
        *stderr*
        {stderr}
        """).format(cmd=cmd, exit_code=rv.exit_code, stdout=rv.stdout, stderr=rv.stderr)
        raise ValueError(msg)

    return rv
