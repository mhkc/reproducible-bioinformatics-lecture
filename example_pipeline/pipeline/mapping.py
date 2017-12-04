"""Functions for mapping reads and manipulating alignments."""
import os

import pandas as pd

from .context import ExecutionContext
from .shell import run_shell_cmd


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
    sample_name = os.path.basename(ctx.sample_location[0]).split('.')[0]
    reference_name = os.path.basename(ctx.reference_location).split('.')[0]

    # Define output file
    sam_file = ctx.path(f'{sample_name}_{reference_name}.sam')

    if not os.path.isfile(sam_file):
        """
        BWA mem has no option to write output to file, instead we capture
        standard out and writes it with a seperate function.
        """
        result = run_shell_cmd(['bwa', 'mem',
                                '-t', ctx.threads,
                                indexed_ref,
                                *ctx.sample_location])
        result.write_stdout(sam_file)  # Write results to file
    return sam_file


def sort_sam(ctx, sam_file):
    """Sort file on mapping position.

    Sorting converts the file to bam format (binary-sam).
    """
    # Rename file
    sorted_file = sam_file.replace('.sam', '-sorted.bam')
    if not os.path.isfile(sorted_file):
        run_shell_cmd(['samtools', 'sort',
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
    sample_name = os.path.basename(ctx.sample_location[0]).split('.')[0]
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
