# if a new file is created just import it here
from settings import *
import wrapper
import discord
from discord.ext import commands

if token is '':
    token = input('Token in settings.py is empty, enter token here or in settings.py. Token: ')

current_books = {}
last_100_books = []
# not a settings

class Book:
    def __init__(self, ctx, tags=None):
        if len(tags) == 0:
            tags = None
        print('new book created in #', ctx.message.channel.name, 'with tags:', tags)
        self.page = 0
        self.results = wrapper.fecth_quote(tags)
        self.search = tags

        self.text, self.pagelen = wrapper.book_renderer(self.search, self.results, self.page)

    async def start_book(self, context):
        self.msg = await context.send(self.text)
        if self.pagelen:
            await self.msg.add_reaction(left_turn)
            await self.msg.add_reaction(right_turn)

    async def flip(self, flip=1):
        # 1 - next, -1 - previous
        if self.pagelen:
            self.page += flip
            if self.page >= self.pagelen:
                self.page = 0
            if self.page < 0:
                self.page = self.pagelen - 1
            self.text, self.pagelen = wrapper.book_renderer(self.search, self.results, self.page)
            await self.msg.clear_reactions()
            await self.msg.add_reaction(left_turn)
            await self.msg.add_reaction(right_turn)

            await self.msg.edit(content=self.text, delete_after=book_timeout)

    async def close(self):
        await self.msg.delete()

@client.command(aliases=['delete_quote'])
async def delete(ctx, *args):
  try:
    if args[0] == 'id':
       wrapper.quote_del(args[1])
  except Exception as e:
    print("failed to delete msg. stack:", e)
    return
  finally:
    print ("deleted msg from db, msgID:", *args)

@client.event
async def on_ready():
    print(log_on_boot)
    game = discord.Game(activity)
    await client.change_presence(status=discord.Status.online, activity=game)

@client.command(aliases=['SBFAQhelp'])
async def SBhelp(ctx):
  await ctx.send(faqhelp)

# how the person brings up the message
@client.command(aliases=['quote'])
async def book_spawn(ctx, *args): # <--- Uhhhh
    # needs to be turned into a book
    book_obj = Book(ctx, args)
    await book_obj.start_book(ctx)
    current_books[book_obj.msg.id] = book_obj
    last_100_books.append(book_obj.msg.id)
    if len(last_100_books) > 100:
        current_books[last_100_books[0]].close()
        current_books[last_100_books[0]] = None
        last_100_books.pop(0)


@client.event
async def on_reaction_add(reaction, channel):
    if reaction.emoji == quote_emoji:
        roles = [i.name for i in reaction.message.author.roles]
        if FBdev in roles or quotemod in roles:
            print('emoji added')
            print('"%s" quote by user "%s" with id @%s' % (
                reaction.message.content, reaction.message.author, reaction.message.author.id))
            if wrapper.add_quote(reaction.message):
                await channel.send('logged!')
        else:
            return

    if reaction.message.id in current_books.keys():
        who_reacted = await reaction.users().flatten()
        roles_who_reacted = []
        for i in [i.roles for i in who_reacted]:
            roles_who_reacted.extend(i)
        isusr = len(who_reacted) > 1
        if reaction.emoji == left_turn and isusr:
            print('flip left')
            await current_books[reaction.message.id].flip(-1)
        elif reaction.emoji == right_turn and isusr:
            print('flip right')
            await current_books[reaction.message.id].flip(1)


@client.command(aliases=['get'])
async def id(ctx, *args):
    try:
        if args[0] == 'id':
            try:
                cur_quote = wrapper.fetch_ID(args[1])[0]
            except:
                raise ValueError
            author, text = cur_quote[1], cur_quote[0].replace('\n', '\t')
            date, jumplink = cur_quote[4][:16], cur_quote[5]

            quote_hud = """> <o>=============<%s>=============<o>
> **%s** - %s
> jumplink: %s""" % (date, author, text, jumplink)

            txt = """you requested message with ID %s. Here's your message.\n%s""" % (id, quote_hud)
            await ctx.send(txt)
        else:
            raise ValueError
    except Exception as e:
        if type(e) == ValueError or len(args) == 0:
            await ctx.send('failed to understand the command. Double check your request and try again.')
        else:
            print(e, 'cur_quote:', cur_quote)

try:
    client.run(key)
except Exception as e:
    print('failed to start the bot. reason:', e)

