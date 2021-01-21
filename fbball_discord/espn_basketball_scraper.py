import requests
import json
from collections import defaultdict
from time import sleep
import argparse



def get_fantasy_bball_data():
  teams = 'https://fantasy.espn.com/apis/v3/games/fba/seasons/2021/segments/0/leagues/31038451?rosterForTeamId=1&view=mDraftDetail&view=mLiveScoring&view=mMatchupScore&view=mPendingTransactions&view=mPositionalRatings&view=mRoster&view=mSettings&view=mTeam&view=modular&view=mNav'
  schedule = 'https://fantasy.espn.com/apis/v3/games/fba/seasons/2021?view=proTeamSchedules_wl'

  specific_team_roster = 'https://fantasy.espn.com/apis/v3/games/fba/seasons/2021/segments/0/leagues/31038451?rosterForTeamId={}&view=mRoster'

  try:
    resp = requests.get(teams)
  except Exception as e:
    print("cant get teams and fantasy league info check link {}".format(teams))
    raise e

  try:
    data = json.loads(resp.content)
  except Exception as e:
    print("response from api endpoint is not json")
    raise e

  try:
    resp = requests.get(schedule)
  except Exception as e:
    print(" schedule link is not a thing anymore")
    raise e

  try:
    nba_schedule = json.loads(resp.content)
  except Exception as e:
    print("schedule response is not a json")
    raise e


  try:
    members = data['members']
    players = {}
    for x in members:
      players[x["id"]] = x.get("firstName",str(None)) + ' ' + x.get("lastName",str(None))

    teams = data['teams']
    lineups = data['schedule']
    scoringPeriod = data['scoringPeriodId']

    proteams = nba_schedule['settings']['proTeams']
    id_to_sched = {}
    for x in proteams:
      if x['abbrev'] != 'FA':
        id_to_sched[x['id']] = x['proGamesByScoringPeriod']
#lineupslotID - roster
# 0- pg
# 1 - sg
# 2 - sf
# 3- pf
# 4 -C
# 5 - G
# 6 - F
# 11 - UTIL
# 12 - Bench
# 13 - IR
    teams_with_roster = {}
    for x in teams:
      name = x['location'] + ' ' + x['nickname']
      teams_with_roster[x['id']] = {
        'name' : name,
        'owner' : players[x['primaryOwner']],
      }

    rosters = {}
    for x in teams_with_roster:
      url = specific_team_roster.format(x)
      resp = requests.get(url)
      data = json.loads(resp.content)
      realdata = data['teams']
      lineup = defaultdict(list)
      rost = None
      for y in realdata:
        if y['id'] == x:
          rost = y['roster']
          break

      for z in rost['entries']:
        player_name = z['playerPoolEntry']['player']['fullName']
        lineup_slot = z['lineupSlotId']
        pro_team = z['playerPoolEntry']['player']['proTeamId']
        eligible_slots = z['playerPoolEntry']['player']['eligibleSlots']
        eligible_slots.remove(13)
        injury_status = z['playerPoolEntry']['player']['injuryStatus']
        player_id = z['playerId']
        player_struct = {
          'name': player_name,
          'lineup_slot': lineup_slot,
          'pro_team': pro_team,
          'eligible_slots' : eligible_slots,
          'injury_status' : injury_status,
          'Id' : player_id
        }
        lineup[lineup_slot].append(player_struct)
      rosters[x] = lineup

    for x in rosters:
      teams_with_roster[x]['lineup'] = rosters[x]

  except Exception as e:
    print("problems with data parsing or mangling")
    raise e




  reminders = defaultdict(list)
  potentially_out = defaultdict(list)
  off_IR = {}
  for z in teams_with_roster:
    lineup = teams_with_roster[z]['lineup']
    lineup_slots_taken = []
    for t in lineup:
      if t == 12:
        continue
      if t == 13:
        player = lineup[t][0]
        if player['injury_status'] == 'ACTIVE':
          pro_team = player['pro_team']
          pro_team_sched = id_to_sched[pro_team]
          if pro_team_sched.get(str(scoringPeriod), None):
            off_IR[teams_with_roster[z]['owner']] = player['name']
      player = lineup[t]
      for u in player:
        pro_team = u['pro_team']
        pro_team_sched = id_to_sched[pro_team]
        print(pro_team_sched)
        if pro_team_sched.get(str(scoringPeriod), None) and t not in [12, 13]:
          if u['injury_status'] == 'OUT':
            potentially_out[teams_with_roster[z]['owner']].append([u['name'], u['injury_status']])
          else:
            lineup_slots_taken.append(t)

    num_utils = lineup_slots_taken.count(11)
    if num_utils != 3:
      while 11 in lineup_slots_taken:
        lineup_slots_taken.remove(11)
    bench = lineup[12]
    for q in bench:
      pro_team = q['pro_team']
      pro_team_sched = id_to_sched[pro_team]
      if pro_team_sched.get(str(scoringPeriod),None):
        if q['injury_status'] in ['ACTIVE', 'DAY_TO_DAY']:
          for p in q['eligible_slots']:
            if p == 12 or (6 < p < 11):
              continue
            if p not in lineup_slots_taken:
              reminders[teams_with_roster[z]['owner']].append(q['name'])
              break



  owner_table = {'Wray Manning' : '@Wray Manning',
                 'Uday Allday' : 'Kevin Peterson',
                 'Kiran Naik' : '@Sid Naik',
                 'Ben Block' : '@Ben Block',
                 'Steffan Skorstad' : 'Steffan Skorstad',
                 'Sunny Sharma' : '@Sunny Sharma',
                 'Sean Fitzpatrick' : '@Sean Fitzpatrick',
                 'James Cho' : '@James Cho'
                 }
  msgs = []
  if reminders:
    for x in reminders:
      if owner_table[x][0] == '@':
        msgs.append(owner_table[x])
        msgs.append('has a player/players ({}) on his bench who is playing today please move them into your starting lineup'.format(', '.join(reminders[x])))
      else:
        msgs.append(
          '{} has a player/players ({}) on his bench who is playing today please move them into your starting lineup'.format(owner_table[x], ', '.join(reminders[x])))
  if potentially_out:
    for x in potentially_out:
      if owner_table[x][0] == '@':
        msgs.append(owner_table[x])
        msgs.append('has a player/players ({}) in the starting lineup who are potentially out for today'.format(str(potentially_out[x])))
      else:
        msgs.append(
          '{} has a player/players ({}) in the starting lineup who are potentially out for today'.format(owner_table[x], str(potentially_out[x])))
  if off_IR:
    for x in off_IR:
      if owner_table[x][0] == '@':
        msgs.append(owner_table[x])
        msgs.append('has a player/players ({}) on the IR who is Active and playing, feel free to move them off IR'.format(off_IR[x]))
      else:
        msgs.append(
          '{} has a player/players ({}) on the IR who is Active and playing, feel free to move them off IR'.format(owner_table[x], off_IR[x]))


  return msgs
