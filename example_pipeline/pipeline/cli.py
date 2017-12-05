"""Handles command line interface for the pipeline."""
import click
import logging

from .context import ExecutionContext
from .mapping import calc_read_coverage, index_reference, mapp_reads, sort_sam
from .plot import plot_coverages

@click.command()
@click.option('-q', '--fastq-file', type=click.Path(exists=True), multiple=True)
@click.option('-f', '--fasta-file', type=click.Path(exists=True))
@click.option('-t', '--threads', type=int, default=1,
              help='Number of threads [Default: 1]')
@click.option('-q', '--quiet', is_flag=True,
              help='Suppress logging output.')
@click.argument('output', default='read_coverage.png')
def cli(fastq_file, fasta_file, threads, quiet, output):
    """Plot number of reads mapping to a given gene in fasta format."""

    logging.basicConfig(level=logging.ERROR if quiet else logging.INFO)

    # Check input files
    if len(fastq_file) is 0 and fasta_file is None:
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
