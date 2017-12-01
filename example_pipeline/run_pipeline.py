#!/usr/bin/env python
"""Command line interface for example pipeline."""

import logging
import os
import shlex
import subprocess
import tempfile
import textwrap
from typing import List

import attr
import click
import matplotlib.pyplot as plt
import pandas as pd

_DEFAULT_DIRECTORY = os.path.join(tempfile.gettempdir(), 'example_pipeline')
LOG = logging.getLogger('example_pipeline')


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


def index_reference(ctx: ExecutionContext) -> str:
    """Index reference gene with BWA index."""
    reference_name = os.path.basename(ctx.reference_location)
    index_path = ctx.path('indexed_sequence', reference_name)

    # Check if file has already been indexed
    if not os.path.isfile(index_path):
        # Symlink input file to output dir to control where the indexes are stored
        os.symlink(ctx.reference_location, index_path)
        # index input file
        run_shell_cmd(['bwa', 'index', index_path])

    return index_path


def mapp_reads(ctx, indexed_ref):
    """Map reads against a reference sequence using BWA."""
    # Naively remove file suffix by splitting on '.' and taking the first entry
    sample_name = os.path.basename(ctx.sample_location).split('.')[0]
    reference_name = os.path.basename(ctx.reference_location).split('.')[0]
    # Define output file
    sam_file = ctx.path(f'{sample_name}_{reference_name}.sam')

    if not os.path.isfile(sam_file):
        """
        BWA mem has no option to write output to file, instead we capture standard out
        and writes it with a seperate function.
        """
        result = run_shell_cmd(['bwa', 'mem',
                                '-t', ctx.threads,
                                indexed_ref,
                                ctx.sample_location])
        result.write_stdout(sam_file)  # Write results to file
    return sam_file


def sort_sam(ctx, sam_file):
    """Sort file on mapping position.

    Sorting converts the file to bam format (binary-sam)."""

    # Rename file
    sorted_file = sam_file.replace('.sam', '-sorted.bam')
    if not os.path.isfile(sorted_file):
        result = run_shell_cmd(['samtools', 'sort',
                                '--threads', ctx.threads,  # Set number of threads
                                '-o', sorted_file,  # Set output file
                                sam_file])
    return sorted_file


def parse_read_cov(cov_file):
    """Parse read coverage from samtools depth output.

    samtools depth output is tab delimitered and has 3 columns;
    1: Name of reference sequence
    2: Position in reference, 1-based
    3: Read coverage at position
    """
    return pd.read_csv(cov_file, delimiter='\t',
                       names=['seq_name', 'position', 'coverage'])


def calc_read_coverage(ctx, aln_file):
    """Calculate read coverage per base in reference file."""
    # Naively remove file suffix by splitting on '.' and taking the first entry
    sample_name = os.path.basename(ctx.sample_location).split('.')[0]
    reference_name = os.path.basename(ctx.reference_location).split('.')[0]
    # Define output file
    coverage_file = ctx.path(f'{sample_name}_{reference_name}_cov.txt')

    # Check if file already exists
    if not os.path.isfile(coverage_file):
        result = run_shell_cmd(['samtools', 'depth',
                                '-a',
                                '--reference', ctx.reference_location,
                                aln_file])
        result.write_stdout(coverage_file)

    # Parse samtools depth output
    return parse_read_cov(coverage_file)


def plot_coverages(ctx: ExecutionContext, cov: pd.DataFrame) -> None:
    """Plot read coverage."""
    # Naively remove file suffix by splitting on '.' and taking the first entry
    sample_name = os.path.basename(ctx.sample_location).split('.')[0]
    reference_name = os.path.basename(ctx.reference_location).split('.')[0]

    cov.plot(x='position', y='coverage')  # Plot results

    # Set title & and save fig
    plt.title(f'Read coverage on {reference_name} in {sample_name}')
    plt.savefig(ctx.output)


@click.command()
@click.option('-q', '--fastq_file', type=click.Path(exists=True))
@click.option('-f', '--fasta_file', type=click.Path(exists=True))
@click.option('-t', '--threads', type=int, default=1,
              help='Number of threads [Default: 1]')
@click.argument('output', default='read_coverage.png')
def cli(fastq_file, fasta_file, threads, output):
    """Plot number of reads mapping to a given gene in fasta format."""
    # Check input files
    if fastq_file is None and fasta_file is None:
        raise click.UsageError('You must specify both a fasta and fastq file')

    # Store execution parameters in a immutable container
    context = ExecutionContext(sample_location=fastq_file,
                               reference_location=fasta_file,
                               threads=threads, output=output)

    # step 1: index the reference sequence
    index_path = index_reference(context)

    # step 2: mapp reads to reference sequence and sort the output on position
    aln_file = mapp_reads(context, index_path)
    sorted_aln_file = sort_sam(context, aln_file)

    # step 3: calculate read coverage on reference sequence
    read_coverage = calc_read_coverage(context, sorted_aln_file)

    # step 4: plot read coverage
    plot_coverages(context, read_coverage)


if __name__ == '__main__':
    cli()  # Run command line interface function
