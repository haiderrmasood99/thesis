#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import os
import sys
from datetime import datetime

def read_season(simulation):
    '''Read season output file for harvested crop, harvest time, plant time, and yield
    '''
    file_name = 'output/' + simulation + '/season.dat'

    if not os.path.exists(file_name):
        print("%s season output file (%s) does not exist." % (simulation, file_name))
        sys.exit(0)

    harvest_time = []
    crop = []
    grain_yield = []
    forage_yield = []

    with open(file_name) as file:
        # Skip header lines
        next(file)
        next(file)

        for line in file:
            harvest_time.append(datetime.strptime(line.split()[0], '%Y-%m-%d'))
            crop.append(line.split()[1])
            grain_yield.append(float(line.split()[5]))
            forage_yield.append(float(line.split()[6]))

    return (np.array(harvest_time), np.array(crop), np.array(grain_yield), np.array(forage_yield))


def main(simulation):
    '''Plot Cycles crop yield time series
    '''
    # Set default font size
    matplotlib.rcParams.update({'font.size': 14})

    # Read Cycles output files
    (harvest_time, crops, grain_yield, forage_yield) = read_season(simulation)

    # Get a list of crops
    _crops = np.unique(crops)

    # Plot yield time series
    _, ax = plt.subplots(figsize=(12,8))

    sim_colors = []

    for c in _crops:
        # Plot grain yield
        _line, = plt.plot(harvest_time[(crops == c) & (grain_yield > 0)], grain_yield[(crops == c) & (grain_yield > 0)],
            'd',
            alpha=0.8,
            ms=8,
        )

        # Save color used for legend
        sim_colors.append(_line.get_color())

        # Plot forage yield
        plt.plot(harvest_time[(crops == c) & (forage_yield > 0)], forage_yield[(crops == c) & (forage_yield > 0)],
            'o',
            color=sim_colors[-1],
            alpha=0.8,
            ms=8
        )

    # Set Y label
    ax.set_ylabel('Crop yield (Mg ha$^{-1}$)', fontsize=18)

    # Set title (simulation name)
    ax.set_title(simulation, fontsize=20)

    # Add grids
    ax.set_axisbelow(True)
    plt.grid(True, color="#93a1a1", alpha=0.2)

    # Add legend: colors for different crops and shapes for grain or forage
    lh = []
    lh.append(mlines.Line2D([], [],
        linestyle='',
        marker='d',
        label='Grain',
        mfc='None',
        color='k',
        ms=10,
    ))
    lh.append(mlines.Line2D([], [],
        linestyle='',
        marker='o',
        label='Forage',
        mfc='None',
        color='k',
        ms=10,
    ))

    for i, c in enumerate(_crops):
        lh.append(mlines.Line2D([], [],
            linestyle='None',
            marker='s',
            label=c,
            color=sim_colors[i],
            alpha=0.8,
            ms=10,
        ))

    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Add legend to figure
    ax.legend(handles=lh,
        fontsize=14,
        handletextpad=0,
        bbox_to_anchor=(1.05, 0.5),
        loc='center left',
        fancybox=True,
        shadow=True,
    )

    plt.show()


if __name__ == '__main__':
    # Check number of command line arguments
    if (len(sys.argv) != 2):
        sys.exit("Name of simulation needs to be defined. Usage: python3 plot_season.py SIMULATION")

    main(sys.argv[1])
