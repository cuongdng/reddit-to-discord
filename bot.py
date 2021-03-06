import discord
from discord import colour
from discord import embeds
from discord import message
from discord import activity
from discord.channel import DMChannel
from discord.enums import ActivityType
from discord.ext import commands
from discord.ext.commands import Bot
import asyncpraw #Python Reddit API Wrapper
from configparser import ConfigParser
import asyncpg

config = ConfigParser()
config.read('config.cfg')

bot_owner = int(config['Discord']['owner_id']) #Addition controls for admin


client = discord.Client()
reddit = asyncpraw.Reddit(client_id=config['Reddit']['client_id'],
                          client_secret=config['Reddit']['client_secret'],
                          user_agent=config['Reddit']['user_agent'],
                          password=config['Reddit']['password'],
                          username=config['Reddit']['username'])

async def create_db_pool():
   client.pg_con = await asyncpg.create_pool(database=config['postgreSQL']['database'],
                                             user=config['postgreSQL']['user'],
                                             password=config['postgreSQL']['password'],
                                             host=config['postgreSQL']['host'])

# async def show_activity():
#    await client.change_presence(activity=discord.Activity(type=activity.CustomActivity(name='test')))

## Import database from PostgreSQL as dictionary
# async def db_to_dict():
#    global keyword
#    db = await client.pg_con.fetch("SELECT * FROM subreddit")
#    for i in db:
#       keyword.update({dict(i)['keyword'] : dict(i)['subreddit']})
#    print('Connected to Database')
   

## Check a subreddit exists or not
async def sub_exists(sub_name):
   exists = True
   try:
      await reddit.subreddit(sub_name, fetch=True)
   except:
      exists = False
   return exists

async def get_image_reddit(sub_name):
   global reddit
   sub = await reddit.subreddit(sub_name)
   random_post = await sub.random()
   if random_post.url.startswith('https://www.reddit.com/gallery'):
      post_galleries = random_post
      gallery = []
      for i in post_galleries.media_metadata.items():
         url = i[1]['p'][0]['u']
         url = url.split("?")[0].replace("preview", 'i')
         gallery.append(url)
      return gallery

   output = []
   output.append(random_post.url)
   return output


@client.event
async def on_ready():
   print('We have logged in as {0.user}'.format(client))
   await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
         
# LOGGING SEND TO HOST SERVER
         
# @client.event
# async def on_guild_join(guild):
#    main_logging = client.get_channel(host_server_id)
#     ## send to main logging channel
#    await main_logging.send("Joined **" + guild.name + "**\nID: " + str(guild.id) + "\nMembers: " + str(guild.member_count)) 
   
# @client.event
# async def on_guild_remove(guild):
#    main_logging = client.get_channel(host_server_id)
#    await main_logging.send("~~Removed~~ from **" + guild.name + "**")
#    await client.pg_con.execute("UPDATE subreddit SET guild_list = array_remove(guild_list, $1) WHERE $1 = ANY(guild_list);", guild.id)
 # END LOGGING   
   
   
@client.event
async def on_message(message):
   
   if message.author == client.user:
      return
   
   # I'm going to use this code for resist NSFW content, but maybe some people doesn't use Jinx for NSFW.
   # if not message.channel.nsfw:
   #    await message.add_reaction('???')
   #    await message.channel.send(content = 'H??y g???i Jinx trong k??nh NSFW!', delete_after=2)
   #    return
   
   # activity_logging = client.get_channel(924953727771742220)
   
   if not isinstance(message.channel, DMChannel):
      guild_id = message.guild.id
   else:
      guild_id = 924953726794465301 ##Hard code, guild id of HQ Server
      
   tmp_dict = {}
   tmp_db = await client.pg_con.fetch("SELECT subreddit, keyword FROM subreddit WHERE $1 = ANY (guild_list)", guild_id)
   for i in tmp_db:
         tmp_dict.update({dict(i)['keyword'] : dict(i)['subreddit']})
   
   liked_emoji = '????'
   agreed_emoji = '???'
   refuse_emoji = '???'
   warning_emoji = '??????'
   
   ###=====================================================================
   ### BELOW ARE FUNCTION FOR BOT OWNER                                  ==
   ###=====================================================================
   
   if message.content.startswith('.rmall'):
      if message.author.id == bot_owner:
         keyword_to_remove = message.content.split(' ')[1]
         await client.pg_con.execute("DELETE FROM subreddit WHERE keyword = $1", keyword_to_remove)
         await message.add_reaction(agreed_emoji)
      return
   
   if message.content.startswith('.rmlist'):
      if message.author.id == bot_owner:
         guild_id_to_remove = int(message.content.split(' ')[1])
         await client.pg_con.execute("UPDATE subreddit SET guild_list = array_remove(guild_list, $1) WHERE $1 = ANY(guild_list);", guild_id_to_remove)
         await message.add_reaction(agreed_emoji)
      return
         
   if message.content.startswith('.sendall'):
      if message.author.id == bot_owner:
         for guild in client.guilds:
            for _channel in guild.text_channels:
               try:
                  await _channel.send(message.content[9:])
                  await message.add_reaction(agreed_emoji)
               except Exception:
                  continue
               else:
                  break
      return
   
   
   if message.content == '.dashboard':
      if message.author.id == bot_owner:
         await message.add_reaction(agreed_emoji)
         await message.channel.send('Hello sir, here is the dashboard. Below is the current list of server that I\'m joining:')
         for guild in client.guilds:
            await message.channel.send(guild.name + ' | ' + str(guild.id))
      return
            
   global keyword
   msg = message.content
   msg = msg.lower()
   
   ###=====================================================================
   ### BELOW ARE FUNCTION FOR USER                                       ==
   ###=====================================================================
   
   ## Add subreddit
   if msg.startswith('.add'):
      try:
         sub_to_add = msg.split(' ')[1].lower()
         command_to_add = msg.split(' ')[2].lower()
      except:
         await message.add_reaction(refuse_emoji)
         await message.channel.send("Sai c?? ph??p. `.add <subreddit> <keyword>`")
         return
      if not sub_to_add in tmp_dict.values():
         sub_check = await sub_exists(sub_to_add)
         if sub_check:
            for key, value in tmp_dict.items():
               if command_to_add == key:
                  await message.add_reaction(warning_emoji)    
                  await message.channel.send("T??? kho?? b???n ch???n ???? ???????c d??ng cho Subreddit: `" + value + "` | Keyword you selected have been used for this Subreddit: `" + value + "`")
                  return
            ## tmp_dict.update({command_to_add : sub_to_add}) ## Do I need this line?
            
            response = await client.pg_con.fetchrow("SELECT keyword FROM subreddit WHERE subreddit = $1;", sub_to_add)
            if response is None:
               await message.add_reaction(agreed_emoji)
            else:
               if response['keyword'] == command_to_add:
                  await message.add_reaction(agreed_emoji)
               else:  
                  await message.add_reaction(warning_emoji)
                  await message.channel.send("Subreddit n??y ???? ???????c th??m t???i database t???ng v???i keyword: `" + response['keyword'] + "`, h??y d??ng keyword n??y ????? g???i.")
            await client.pg_con.execute("INSERT INTO subreddit VALUES ($1, $2, $3) ON CONFLICT ON CONSTRAINT subreddit_cn DO UPDATE SET guild_list = array(SELECT DISTINCT unnest(subreddit.guild_list || EXCLUDED.guild_list));", sub_to_add, command_to_add, {guild_id})
            # if message.author.id != bot_owner:
            #        await activity_logging.send('**'+ message.author.name + '** has use: *' + msg + '*')
         else:
            await message.add_reaction(refuse_emoji)
            await message.channel.send("Subreddit n??y kh??ng t???n t???i | This subreddit doesn't exist")
      else:
         await message.add_reaction(warning_emoji)
         for key, value in tmp_dict.items():
            if sub_to_add == value:
               await message.channel.send("Subreddit n??y ???? t???n t???i trong list v???i t??? kho?? `" + key + "` | This subreddit already exists with the keyword `" + key + "`")
               break
      return
   
   ## Remove subreddit
   if msg.startswith('.rm'):
      command_to_remove = msg.split(' ')[1]
      if command_to_remove in tmp_dict:
         await message.add_reaction(agreed_emoji)
         await client.pg_con.execute("UPDATE subreddit SET guild_list = array_remove(guild_list, $1) WHERE keyword = $2;", guild_id, command_to_remove)
         await client.pg_con.execute("DELETE FROM subreddit WHERE guild_list = '{}';")
         # if message.author.id != bot_owner:
         #       await activity_logging.send('**'+ message.author.name + '** has use: *' + msg + '*')
      else:
         await message.add_reaction(refuse_emoji)
         await message.channel.send("T??? kho?? n??y kh??ng t???n t???i | This keyword doesn't exist")
      return

   ## Show list of keyword
   if msg == '.list':
      await message.add_reaction(liked_emoji)
      list_embed = discord.Embed(colour = 0xAA99FF, title='Subreddit List', description='**Keyword** - Subreddit\nD??ng c??c **keyword** ????? g???i Jinx')
      await message.channel.send(embed = list_embed)
      
      string = "\n".join('**{}** - {}'.format(k, v) for k, v in tmp_dict.items())
       
      string_length = len(string)
      if string_length == 0:
         return
      if string_length < 2000:
         await message.channel.send(string)
      else:
         max_index = 2000
         index = 0
         while index < (string_length - max_index):
            while (string[max_index] != '\n'):
                   max_index = max_index - 1
            posted_string = string[index:max_index]
            await message.channel.send(posted_string)
            index = index + max_index
         posted_string = string[index:]   
         await message.channel.send(posted_string)
      # if message.author.id != bot_owner:
      #          await activity_logging.send('**'+ message.author.name + '** has use: *' + msg + '*')
      return
   
   ## About bot
   if msg == '.about':
      await message.add_reaction(liked_emoji)
      about_embed = discord.Embed(title='?????? About Jinx ??????', description='Jinx c?? kh??? n??ng l???y ng???u nhi??n m???t (ho???c nhi???u) b???c ???nh, gif, video link,... t??? m???t Subreddit c?? tr??n Reddit', colour=0xAA99FF)
      about_embed.add_field(name='???? L???i nh???n nh???', value='Cu???c s???ng l?? v???y, c?? r???t nhi???u chuy???n x???y ra kh??ng nh?? ch??ng ta mong mu???n. Jinx c??ng v???y, c?? ????i khi s??? c???n kho???ng v??i gi??y ????? Jinx c?? th??? ph???n h???i b???n. Ho???c th???m ch?? Jinx s??? kh??ng ph???n h???i, m??nh v???n ??ang trong qu?? tr??nh c???i ti???n kh??? n??ng c???a Jinx. Thong th??? nh??!', inline=False)
      about_embed.add_field(name='???? Tip1??????', value='????? Jinx ph??t huy h???t s???c m???nh v?? ??em l???i nh???ng ??i???u tuy???t nh???t cho b???n, h??y t??m hi???u v??? Reddit')
      about_embed.add_field(name='???? Tip2??????', value='N???u b???n g???i nh???ng n???i dung NSFW, h??y g???i trong k??nh chat c?? g???n NSFW, ??i???u n??y s??? ?????m b???o an to??n cho server c???a b???n')
      about_embed.set_footer(text='Li??n h???: cuongdn.sun@gmail.com - Phi??n b???n c???p nh???t 21/1/2022')
      await message.channel.send(embed = about_embed)
      # if message.author.id != bot_owner:
      #       await activity_logging.send('**'+ message.author.name + '** has use: *' + msg + '*')
      return
         
   if msg == '.help':
      await message.add_reaction(liked_emoji)
      help_embed = discord.Embed(title='?????? Help ??????', description='Danh s??ch l???nh v?? m???t s??? th???c m???c b???n c?? th??? g???p', colour=0xAA99FF)
      help_embed.add_field(name='.about', value='T??m hi???u v??? Jinx', inline=False)
      help_embed.add_field(name='.list', value='Hi???n th??? to??n b??? c??c keyword v?? t??n Subreddit t????ng ???ng t???i server c???a b???n', inline=False)
      help_embed.add_field(name='.add <subreddit> <keyword>', value='Th??m m???t keyword m???i v??o list \nV?? d???: Th??m Subreddit: Memes_Of_The_Dank v???i t??? kho?? dankmeme:\n *.add Meme_Of_The_Dank dankmeme*', inline=False)
      help_embed.add_field(name='.addnsfw', value='Add list NSFW', inline=False)
      help_embed.add_field(name='.rm <keyword>', value='Xo?? m???t keyword kh???i list \nV?? d???: Mu???n xo?? keyword dankmeme: *.rm dankmeme*', inline=False)
      help_embed.add_field(name='===========', value='M???t s??? c??u h???i th?????ng g???p', inline=True)
      help_embed.add_field(name='Keyword l?? g???', value='Ch??? ????n gi???n l?? m???t c??ch g???i kh??c cho c??c l???nh b???n d??ng ????? g???i Jinx. Nh???ng keyword n??y ???????c d??ng ????? g???i c??c n???i dung t????ng ???ng v???i c??c Subreddit.', inline=False)
      help_embed.add_field(name='Subreddit l?? g???', value='C??c m???c n???i dung ???????c chia theo nh???ng l??nh v???c kh??c nhau c???a Reddit. ????? hi???u r?? h??n, b???n h??y t??m hi???u v??? Reddit.', inline=False)
      help_embed.add_field(name='M??nh c?? th??? tu??? ?? th??m v?? xo?? danh s??ch keyword kh??ng?', value='C??, b???n h??y s??? d???ng l???nh .add v?? .remove', inline=False)
      help_embed.add_field(name='Khi mu???n g???i n???i dung t??? Subreddit n??o ????, m??nh ph???i l??m g???', value='B???n ch??? c???n chat keyword t????ng ???ng v???i Subreddit mu???n g???i. Keyword kh??ng c???n b???t ?????u b???ng d???u "."', inline=False)
      help_embed.add_field(name='V???y "." ???????c s??? d???ng khi n??o?', value='"." l?? ti???n t??? ???????c d??ng khi b???n mu???n g???i c??c l???nh c?? b???n c???a Jinx, ???? ???????c n??u ?????y ????? ph??a tr??n.', inline=False)
      help_embed.add_field(name='T???i sao trong m???t l???n g???i, c?? l??c Jinx ch??? g???i v??? m???t ???nh nh??ng c?? l??c l???i r???t nhi???u ???nh?', value='Do ?????nh d???ng b??i ????ng g???c m?? Jinx l???y ???????c, ???? c?? th??? l?? m???t post v???i m???t b???c ???nh ????n, ho???c m???t gallery v???i nhi???u ???nh.', inline=False)
      help_embed.add_field(name='????i khi Jinx l???y v??? nh???ng n???i dung tr??ng l???p v???i nh???ng l???n g???i tr?????c', value='T???t nhi??n r???i, ng???u nhi??n m??!', inline=False)
      await message.channel.send(embed = help_embed)
      # if message.author.id != bot_owner:
      #       await activity_logging.send('**'+ message.author.name + '** has use: *' + msg + '*')
      return
         
   ## Send image
   if msg in tmp_dict.keys():
      try:
         img_url = await get_image_reddit(tmp_dict[msg])
         for i in img_url:
               await message.channel.send(i)
         await message.add_reaction(liked_emoji)
         # if message.author.id != bot_owner:
         #       await activity_logging.send('**'+ message.author.name + '** has call: *' + msg + '*')
      except:
         await message.add_reaction(refuse_emoji)
         await message.channel.send("Do m???t s??? ch??nh s??ch c???a Subreddit n??y, Jinx kh??ng th??? l???y d??? li???u | Due to this Subreddit's policy, Jinx can't get data")
      return
      
# client.loop.run_until_complete(show_activity())
client.loop.run_until_complete(create_db_pool())
client.run(config['Discord']['discord_token'])
