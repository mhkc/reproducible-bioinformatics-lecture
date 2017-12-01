#!/usr/bin/env python
"""Entry point for the pipeline.

Calls upon the command line interface modules where the execution starts
"""

from pipeline.cli import cli

if __name__ == '__main__':
    cli()  # Run command line interface function
