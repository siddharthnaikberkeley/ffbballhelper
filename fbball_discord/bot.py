import os

import discord

import espn_basketball_scraper


TOKEN = 'NzkyODQzNjM0NzAxMzY5Mzc0.X-jnLA.Kj77PxtRlDqRS55Uym5U-tWyXRU'


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


fantasy_owner_name_to_discord_username = {'Ben Block' : 'benjamin',
                                          'Sean Fitzpatrick' : 'coolcat',
                                          'Sunny Sharma' : 'basedreptile',
                                          'Kiran Naik' : 'sid331',
                                          'Wray Manning' : 'manwray',
                                          'James Cho' : 'girlsarecool'
                                      }

discord_name_to_id = {}

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print("about to do some scraping")
    msgs = espn_basketball_scraper.get_fantasy_bball_data()
    print(msgs)
    for guild in client.guilds:
      print(guild)
      server = guild
      channels = server.channels
      members = server.members
      for member in members:
        discord_name_to_id[member.name] = member.id
      for channel in channels:
        if channel.name == 'dook' or channel.name == 'sports':
          print('here')
          x = 0
          while x < len(msgs):
            if msgs[x][0] == '@':
              full_name = msgs[x][1:]
              discord_name = fantasy_owner_name_to_discord_username.get(full_name, None)
              if discord_name:
                id = discord_name_to_id.get(discord_name, None)
                if id:
                  await channel.send('<@{}>'.format(id) + ' ' + msgs[x+1])
                  x += 2
                  continue
              await channel.send(full_name + ' ' + msgs[x+1])
              x += 2
            else:
              await channel.send(msgs[x])
              x += 1



#client.run(TOKEN)
#client.close()

print(espn_basketball_scraper.get_fantasy_bball_data())