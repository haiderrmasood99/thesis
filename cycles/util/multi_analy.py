#!/usr/bin/env python3

import sys
from datetime import datetime

def read_multi(fn):
    '''Read multi-mode input file

    Read Cycles multi-mode input file to get a list of simulations and find overlapping simulation years
    '''

    path = 'input/' + fn

    sim_name = []
    _start_years = []
    _end_years = []

    # Read names of simulations and start and end years
    with open(path) as file:
        # Skip header line
        next(file)
        for line in file:
            sim_name.append(line.split()[0])
            _start_years.append(int(line.split()[2]))
            _end_years.append(int(line.split()[3]))

    # Find overlapping years from simulations
    start_year = max(_start_years)
    end_year = min(_end_years)

    return sim_name, start_year, end_year


def read_output(sim, fn, column, start_year, end_year):
    '''Read the one column from specified output file for all simulations
    '''

    # Cycles output files with three header lines. Others have two.
    three_header_lines=(
        'annualSoilProfileC.dat',
        'annualSOM.dat',
        'environ.dat',
        'soilLayersCN.dat',
        'water.dat',
        )

    path = 'output/' + sim + '/' + fn

    sim_time = []
    output_values = []

    with open(path) as file:
        # Skip header lines
        if fn in three_header_lines:
            next(file)
            next(file)
            next(file)
        else:
            next(file)
            next(file)

        # Read time and output values
        for line in file:
            if fn[:6] == 'annual':
                # Annual output
                _sim_time = datetime.strptime(line.split()[0], '%Y')
            else:
                # Daily output
                _sim_time = datetime.strptime(line.split()[0], '%Y-%m-%d')

            if (_sim_time >= datetime(start_year, 1, 1) and
                _sim_time <= datetime(end_year, 1, 1)):
                sim_time.append(line.split()[0])
                output_values.append(line.split()[column - 1])

    return sim_time, output_values


def main(multi_fn, output_fn, column):
    # Read multi-mode control file
    sim_names, start_year, end_year = read_multi(multi_fn)

    # Check if there are overlapping years among simulations
    if start_year > end_year:
        sys.exit('No overlapping years among simulations.')

    # Read output files from multi-simulations
    sim_time = []
    output_values = []
    for sim in sim_names:
        sim_time, _output_values = read_output(sim, output_fn, column, start_year, end_year)
        output_values.append(_output_values)

    # Open output file and write header line
    with open('multi-' + output_fn, 'w') as fp:
        fp.write('%-10s' % 'TIME')
        [fp.write('\t%-15s' % sim) for sim in sim_names]
        fp.write('\n')

        # Write output from multi-simulations to output file
        for k in range(len(output_values[0])):
            fp.write('%-10s' % sim_time[k])
            [fp.write('\t%-15s' % output_values[i][k]) for i in range(len(output_values))]
            fp.write('\n')


if __name__ == "__main__":
    # Check number of command line arguments
    if len(sys.argv) != 4:
        sys.exit('Command line argument error!\n'
                 'Usage: multi_analy.py [multi-mode file name] [output file name] [column index]')

    # Parse command line arguments
    multi_fn = sys.argv[1]
    output_fn = sys.argv[2]
    column = int(sys.argv[3])

    if output_fn == 'season.dat':
        sys.exit('Error: This script does not support season output. Please use a different output file.')

    main(multi_fn, output_fn, column)
