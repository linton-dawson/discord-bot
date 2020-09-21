#Third party imports
import discord
import tmdbv3api 
import rarbgapi
from rotten_tomatoes_client import RottenTomatoesClient
import chessdotcom 

#sys imports
import regex as re
import random
import os
from dotenv import load_dotenv
import io
import aiohttp
import requests
import string

load_dotenv()

DISC_TOKEN = os.getenv('DISCORD_TOKEN')
TMDB_TOKEN = os.getenv('TMDB_API_KEY')

#API instantiation
client = discord.Client()
movie = tmdbv3api.Movie()
person = tmdbv3api.Person()
rbapi = rarbgapi.RarbgAPI()

#magnet link shortener url for post method
mgnet = "http://mgnet.me/api/create"

#function which gets the magnet link from rarbg and shortens it using mgnet.me api
def getID(title) :
    tmp = title
    title = ''
    for i in tmp:
        if i in string.punctuation :
            continue
        title += i
    tmp = title
    title = ''
    for i in tmp :
        if i == ' ':
            if title.endswith('.') :
                continue
            title += '.'
        else :
            title += i
#    print(title)
    try :
        tmp = rbapi.search(search_string = title)
        maglink = tmp[0].download
        link = requests.post(mgnet,params={'m' : maglink, 'format' : 'text'})
        return link.text
    except :
        return "Iska magnet link nahi mila sorry :("


#function which structures the message to be send and gets the shortened magnet link
def to_send(title,rel_date) :
    rel_date = rel_date[:4]
    final_title = getID(title + ' ' + rel_date)
    return final_title


#below regex formatting function taken from https://stackoverflow.com/a/38832133. Trims the biography# to one sentence
def format_string(input_string):
    keywords = set(['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Rev.', 'Capt.', 'Lt.-Col.', 
            'Col.', 'Lt.-Cmdr.', 'The Hon.', 'Cmdr.', 'Flt. Lt.', 'Brgdr.', 'Wng. Cmdr.', 
            'Group Capt.' ,'Rt.', 'Maj.-Gen.', 'Rear Admrl.', 'Esq.', 'Mx', 'Adv', 'Jr.'] )
    regexes = '|'.join(keywords)  # Combine all keywords into a regex.
    split_list = re.split(regexes, input_string)  # Split on keys.
    removed = re.findall(regexes, input_string)  # Find removed keys.
    newly_joined = split_list + removed  # Interleave removed and split.
    newly_joined[::2] = split_list
    newly_joined[1::2] = removed
    space_regex = '\.\s*'

    for index, section in enumerate(newly_joined):
        if '.' in section and section not in removed:
            newly_joined[index] = re.sub(space_regex, '.\n', section)
    return ''.join(newly_joined).strip()


#console notif for the user
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


#main bot working here
@client.event
async def on_message(msg) :
    if msg.author == client.user :
        return

#calling name (bhendi)
    if msg.content.startswith('bhendi') or msg.content.startswith('Bhendi'):
        userip = msg.content

        #movie recommendation
        if 'rec' in userip :
            movie_name = userip[userip.index('rec') + 4 :]
            search = movie.search(movie_name)
            mov_id = 0
            for res in search :
                mov_id = res.id
                break
            try:
                recommend = movie.similar(movie_id = mov_id)
                if recommend :
                    await msg.channel.send('__PEHLE 10 ICH DIKHAATA__')
                    for r in range(0,min(len(recommend),10)) :
                        title = '**' + recommend[r].title + '**\n'
                        title += to_send(recommend[r].title,recommend[r].release_date)
                        await msg.channel.send(title)
                else :
                    await msg.channel.send('KYA TUTUL PUTUL ! Acchese type kar...')
            except :
                await msg.channel.send('Kuch to bhi locha ho gaya')


        #get details of a celebrity 
        if 'whois' in userip :
            person_name = userip[userip.index('whois') + 6 :]
            search_res = person.search(person_name,1)
            for celeb in search_res :
                pid = person.details(celeb.id)
                bio = pid.biography
                biolist = format_string(bio)
                biolist = biolist[:biolist.find('.')+1]
                name = '**' + pid.name + '**'
                await msg.channel.send(name)
                if(biolist) :
                    await msg.channel.send(biolist)
                else :
                    await msg.channel.send('Mereko nahi pata')


        #get popularity of a movie
        if 'howis' in userip :
            movie_name = userip[userip.index('howis') + 6 :]
            try :
                movie_raw = RottenTomatoesClient.search(term =movie_name,limit = 1)
                movie_json = movie_raw['movies']
                movie_detail = movie_json[0]
                final_detail = 'Release year: ' + str(movie_detail['year'])
                cast = movie_detail['subline']
                cast = cast[:-1]
                final_detail += '\nStarring: ' + cast
                final_detail += '\nMeter Class: ' + movie_detail['meterClass'] + '\nMeter Score: ' + str(movie_detail['meterScore'])
                print(final_detail)
                await msg.channel.send(final_detail)
            except :
                await msg.channel.send("Pehle mereko yeh samjha ki ... isko samjhana kya hai. Type kar firse kutrya !")


        #display movie poster
        if 'poster' in userip :
            baseURL = 'https://image.tmdb.org/t/p/w500'
            movie_name = userip[userip.index('poster') + 7 :]
            search = movie.search(movie_name)
            search[0].poster_path = baseURL + search[0].poster_path
            async with aiohttp.ClientSession() as session :
                async with session.get(search[0].poster_path) as resp :
                    if resp.status != 200 :
                        return await msg.channel.send('Poster nahi mila, sorry.')
                    data = io.BytesIO(await resp.read())
                    await msg.channel.send(file = discord.File(data,'cool_img.png'))

        #display popular movies
        if 'popular' in userip :
            popular = movie.popular()
            await msg.channel.send('**POPULAR MOVIES**')
            for mov in popular :
                title = mov.title + '\n'
                title += to_send(mov.title,mov.release_date)
                await msg.channel.send(title)
        
        #get magnet links
        if 'magnet' in userip :
            movie_name = userip[userip.index('magnet') + 7 :]
            search = movie.search(movie_name)
            movie_magnet = search[0].title + '\n'
            movie_magnet += to_send(search[0].title,search[0].release_date)
            await msg.channel.send(movie_magnet)


        #send love
        if 'gib-pyaar' in userip :
            msg1 = 'Hey ' + msg.mentions[0].mention.format(msg) + '. I love you <3'
            await msg.channel.send(msg1)
       

        #chess get ratings and record 
        if 'chess' in userip :
            player_name = userip[userip.index('chess') + 6 :]
            try :
                player_data = chessdotcom.get_player_stats(player_name)
                send_string = 'chess.com details for **' + player_name + '** :-\n'
                keylist = list(player_data.keys())
                for key in keylist :
                    if key == "fide" :
                        break
                    game_type = key
                    tmp = game_type
                    game_type = game_type.replace('_',' ')
                    game_type = game_type.capitalize()
                    recent = player_data[key]
                    ans = recent['last']['rating']
                    trec = recent['record']
                    send_string += '__' + game_type + '__ : ' + str(ans) + ' (' + str(trec['win']) + 'W--' + str(trec['loss']) + 'L--' + str(trec['draw']) + 'D)\n'
                await msg.channel.send(send_string)
            except :
                await msg.channel.send("Username as absent as Fischer in Game 2...")

        #help
        if 'help' in userip :
            await msg.channel.send("Help Docs under construction")
client.run(DISC_TOKEN)
