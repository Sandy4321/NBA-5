from __future__ import division, print_function
import random
import operator
import csv
import datetime
from dateutil import parser
from numpy import median, mean

class Simulator:
    def __init__(self, simulation_count, team_file, schedule_file):
        self.simulation_count = simulation_count
        self.team_file = team_file
        self.schedule_file = schedule_file
        self.seasons = []
        self.league = League()
        self.load_files()
        self.team_wins = {team: [] for team in self.league.teams.keys()}
        self.team_playoffs = {team: 0 for team in self.league.teams.keys()}
        self.team_playoff_seed = {team: [] for team in self.league.teams.keys()}

    def load_files(self):
        with open(self.team_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = Team(row)
                self.league.add_team(team)
        with open(self.schedule_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                home = self.league.teams[row['home_team']]
                road = self.league.teams[row['road_team']]
                home_score = 0 if row['home_score'] == '' else int(row['home_score'])
                road_score = 0 if row['road_score'] == '' else int(row['road_score'])
                game = Game(parser.parse(row['date']), home, road, home_score, road_score)
                self.league.schedule.append(game)

    def simulate(self):
        for season_index in range(self.simulation_count):
            season = Season(self.league, season_index)
            season.simulate()
            self.seasons.append(season)
            playoffs = {conf: season.playoff_seeds(conf) for conf in League.DIVISIONS.keys()}
            for team in self.league.teams.keys():
                self.team_wins[team].append(self.league.teams[team].wins)
                if season.made_playoffs(team):
                    self.team_playoffs[team] += 1
                self.team_playoff_seed[team].append(season.playoff_seed(team))

    def print_results(self):
        for conference in League.DIVISIONS.keys():
            teams = sorted([team for team in self.league.teams.keys()], key=lambda x: sum(self.team_wins[x]), reverse=True)
            print('\n======================================================================================')
            print(conference.title())
            print('======================================================================================')
            print('Team\t\t\t  W\t  L\tPct\t Min\t Med\t Avg\t Max\tPO Pct')
            print('--------------------------------------------------------------------------------------')
            for team_name in teams:
                if self.league.teams[team_name].conference == conference:
                    start_wins = self.league.teams[team_name].starting_wins
                    start_losses = self.league.teams[team_name].starting_losses
                    win_pct = sum(self.team_wins[team_name])/(self.simulation_count * 82)
                    min_wins = min(self.team_wins[team_name])
                    med_wins = median(self.team_wins[team_name])
                    avg_wins = mean(self.team_wins[team_name])
                    max_wins = max(self.team_wins[team_name])
                    po_pct = self.team_playoffs[team_name]/self.simulation_count
                    print('{0: <25}{1: >3}\t{2: >3}\t{3:.3f}\t{4: >3}\t{5: .1f}\t{6: .1f}\t{7: >3}\t{8:.3f}'
                        .format(team_name, start_wins, start_losses, win_pct, min_wins, med_wins, avg_wins, max_wins, po_pct))
            print('======================================================================================\n\n')


class League:
    DIVISIONS = {'east': ['southeast', 'atlantic', 'central'], 'west': ['northwest', 'pacific', 'southwest']}

    def __init__(self):
        self.schedule = []
        self.teams = {}
        self.divisions = {conf: {div: [] for div in League.DIVISIONS[conf]}
                         for conf in League.DIVISIONS.keys()}

    def add_team(self, team):
        self.teams[team.name] = team
        self.divisions[team.conference][team.division].append(team)


class Season:
    def __init__(self, league, index):
        self.league = league
        self.index = index

    def simulate(self, start_date=None):
        nba = self.league
        for team in nba.teams:
            nba.teams[team].reset_record()
        for game in nba.schedule:
            if start_date is None or game.date >= start_date:
                game.simulate(self.index, True)

    def standings(self, conference, division=None):
        if division is None:
            teams = reduce(operator.add, 
                           [self.league.divisions[conference][division] 
                            for division in self.league.divisions[conference].keys()])
        else:
            teams = self.league.divisions[conference][division]
        return sorted(teams, reverse=True)

    def division_winner(self, division):
        conference = 'west' if division in League.DIVISIONS['west'] else 'east'
        return self.standings(conference, division)[0]

    def print_standings(self):
        for conference in League.DIVISIONS.keys():
            print('\n=============================================')
            print(conference.title())
            print('=============================================')
            for division in League.DIVISIONS[conference]:
                print('\n{}'.format(division.title()))
                print('---------------------------------------------')
                print('Team\t\t\t  W\t L\tPct')
                print('---------------------------------------------')
                for team in self.standings(conference, division):
                    win_pct = team.wins/(team.wins + team.losses)
                    print('{0: <25}{1: >3}\t{2: >3}\t{3:.3f}'.format(team.name, str(team.wins), str(team.losses), win_pct))
        print('=============================================\n\n')

    def playoff_seeds(self, conference):
        division_winners = [self.standings(conference, division)[0] for division in League.DIVISIONS[conference]]
        next_best = max([team for team in self.standings(conference) if team not in division_winners])
        top_four = sorted(division_winners + [next_best], reverse=True)
        the_rest = [team for team in self.standings(conference) if team not in top_four]
        seeded_teams = top_four + the_rest
        return dict(zip(range(1, 16), seeded_teams))

    def playoff_seed(self, team_name):
        conf = self.league.teams[team_name].conference
        playoff_seeds = self.playoff_seeds(conf)
        for index in playoff_seeds.keys():
            if playoff_seeds[index].name == team_name:
                return index
        return 16

    def made_playoffs(self, team_name):
        return (self.playoff_seed(team_name) <= 8)

    def print_playoffs(self):
        for conference in League.DIVISIONS.keys():
            print('\n=====================================================')
            print(conference.title())
            print('-----------------------------------------------------')
            print('Seed\tTeam\t\t\t  W\t L\tPct')
            print('-----------------------------------------------------')
            playoffs = self.playoff_seeds(conference)
            for seed in playoffs:
                team = playoffs[seed]
                win_pct = team.wins/(team.wins + team.losses)
                print('{0: >4}\t{1: <25}{2: >3}\t{3: >3}\t{4:.3f}'.format(seed, team.name, str(team.wins), str(team.losses), win_pct))
                if seed == 8:
                    print('-----------------------------------------------------')
            print('=====================================================\n')


class Game:
    def __init__(self, date, home, road, home_score=0, road_score=0):
        self.date = date
        self.home = home
        self.road = road
        self.home_score = home_score
        self.road_score = road_score
        self.simulated = False

    def simulate(self, season_index, update_standings=True):
        road_wa = self.road.wins_against[self.home.conference][self.home.division]
        home_wa = self.home.wins_against[self.road.conference][self.road.division]
        road_la = self.road.losses_against[self.home.conference][self.home.division]
        home_la = self.home.losses_against[self.road.conference][self.road.division]
        if self.home.name not in road_wa:
            road_wa[self.home.name] = 0
        if self.home.name not in road_la:
            road_la[self.home.name] = 0
        if self.road.name not in home_wa:
            home_wa[self.road.name] = 0
        if self.road.name not in home_la:
            home_la[self.road.name] = 0
        if self.home_score > self.road_score:
            winner = self.home
            loser = self.road
        elif self.road_score > self.home_score:
            winner = self.road
            loser = self.home
        else:
            if random.random() <= self.home.win_prob_versus(self.road, 'home'):
                winner = self.home
                loser = self.road
            else:
                winner = self.road
                loser = self.home
        if update_standings:
            winner.wins_against[loser.conference][loser.division][loser.name] += 1
            winner.wins += 1
            loser.losses_against[winner.conference][winner.division][winner.name] += 1
            loser.losses += 1
        return winner


class Team:
    EXP = 10.25
    HFA = 0.014
    side = ['off', 'def']
    site = ['home', 'road', 'neutral']
    
    @staticmethod
    def log5(a, b):
        return (a - a * b) / (a + b - 2 * a * b)

    @staticmethod
    def homefield_factor(side, site):
        if side not in Team.side:
            raise ValueError('Invalid side type: {}'.format(side))
        if site == 'neutral':
            return 1
        elif ((side[:3].lower() == 'off' and site.lower() == 'home')
             or (side[:3].lower() == 'def' and site.lower() == 'road')):
            return 1 + Team.HFA
        else:
            return 1 - Team.HFA

    def __init__(self, args):
        self.name = args['name']
        self.abbreviation = args['abbreviation']
        self.conference = args['conference']
        self.division = args['division']
        self.starting_wins = args['wins']
        self.starting_losses = args['losses']
        self.reset_record()
        self.eff = {'off' : float(args['offeff']), 'def' : float(args['defeff'])}

    def __lt__(self, other):
        # season record
        if self.wins < other.wins:
            return True
        elif self.wins > other.wins:
            return False
        # if equal, tiebreaker
        # head-to-head
        if self.win_pct_vs(other) < other.win_pct_vs(self):
            return True
        elif self.win_pct_vs(other) > other.win_pct_vs(self):
            return False
        # conference win percentage
        if self.conference == other.conference:
            if self.conf_win_pct() < other.conf_win_pct():
                return True
            elif self.conf_win_pct > other.conf_win_pct():
                return False
        # instead of implementing remaining tiebreakers, choose team with better pythagorean.
        if self.pythagorean() < other.pythagorean():
            return True
        elif self.pythagorean() > other.pythagorean():
            return False
        else:
            # if pythagorean expectations at a neutral site are equal, choose one team at random.
            return random.random() <= 0.5

    def efficiency(self, side, site='neutral'):
        if site not in Team.site:
            raise ValueError('Invalid site type: {}'.format(site))
        if side not in Team.side:
            raise ValueError('Invalid side type: {}'.format(side))
        return self.eff[side] * Team.homefield_factor(side, site)

    def pythagorean(self, site='neutral'):
        if site not in Team.site:
            raise ValueError('Invalid site type: {}'.format(site))
        return self.efficiency('off', site) ** Team.EXP / (self.efficiency('off', site) ** Team.EXP + self.efficiency('def', site) ** Team.EXP)

    def win_prob_versus(self, opponent, site='neutral'):
        if site not in Team.site:
            raise ValueError('Invalid site type: {}'.format(site))
        return Team.log5(self.pythagorean(site), opponent.pythagorean(site))

    def reset_record(self):
        self.wins = 0
        self.losses = 0
        self.playoff_seed = 15
        self.wins_against = {conf: {div: {} for div in League.DIVISIONS[conf]} for conf in League.DIVISIONS}
        self.losses_against = {conf: {div: {} for div in League.DIVISIONS[conf]} for conf in League.DIVISIONS}

    def conf_win_pct(self):
        # TODO: make this a list comprehension
        w = 0
        l = 0
        for division in League.DIVISIONS[self.conference]:
            for team in self.wins_against[self.conference][division]:
                w += self.wins_against[self.conference][division][team]
            for team in self.losses_against[self.conference][division]:
                l += self.losses_against[self.conference][division][team]
        return w/(w + l)

    def win_pct_vs(self, opponent):
        if opponent.name not in self.wins_against[opponent.conference][opponent.division]:
            wins = 0
        else:
            wins = self.wins_against[opponent.conference][opponent.division][opponent.name]
        if self.name not in opponent.wins_against[self.conference][self.division]:
            losses = 0
        else:
            losses = opponent.wins_against[self.conference][self.division][self.name]
        return wins / (wins + losses)