#!/usr/bin/env python

from __future__ import print_function
import sys
import NBA

def main():
    sim_count = int(sys.argv[1])
    sim = NBA.Simulator('nba_teams.csv', 'nba_schedule.csv', 'results.csv')
    sim.simulate(sim_count, True)
    sim.print_results()


if __name__ == '__main__':
    main()
