"""Functions for plotting and output generation."""

import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd

from .context import ExecutionContext


def plot_coverages(ctx: ExecutionContext, cov: pd.DataFrame) -> None:
    """Plot read coverage."""
    # Naively remove file suffix by splitting on '.' and taking the first entry
    sample_name = os.path.basename(ctx.sample_location[0]).split('.')[0]
    reference_name = os.path.basename(ctx.reference_location).split('.')[0]

    cov.plot(x='position', y='coverage')  # Plot results

    # Set title & and save fig
    plt.title(f'Read coverage on {reference_name} in {sample_name}')
    plt.savefig(ctx.output)
