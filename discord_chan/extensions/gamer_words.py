# Copyright 2020 io mintz <io@mintz.cc>, StarrFox, Vex

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:

# The above copyright notice, penisbird and this permission notice shall be included
# in all copies or substantial portions of the Software unmodified.

#                     _..._
#                  .-'     '-.
#                 /     _    _\
#                /':.  (o)  /__)
#               /':. .,_    |  |
#              |': ; /  \   /_/
#              /  ;  `"`"    }
#             ; ':.,         {
#            /      ;        }
#           ; '::.   ;\/\ /\ {
#          |.      ':. ;``"``\
#         / '::'::'    /      ;
#        |':::' '::'  /       |
#        \   '::' _.-`;       ;
#        /`-..--;` ;  |       |
#       ;  ;  ;  ;  ; |       |
#       ; ;  ;  ; ;  ;        /        ,--.........,
#       |; ;  ;  ;  ;/       ;       .'           -='.
#       | ;  ;  ; ; /       /       .\               '
#       |  ;   ;  /`      .\   _,=="  \             .'
#       \;  ; ; .'. _  ,_'\.\~"   //`. \          .'
#       |  ;  .___~' \ \- | |    /,\ `  \      ..'
#     ~ ; ; ;/  =="'' |`| | |       =="''\.==''
#     ~ /; ;/=""      |`| |`|   ==="`
#     ~..==`     \\   |`| / /=="`
#      ~` ~      /,\ / /= )")
#     ~ ~~         _')")
#     ~ ~   _,=~";`
#     ~  =~"|;  ;|       Penisbird
#      ~  ~ | ;  |       =========
#   ~ ~     |;|\ |
#           |/  \|

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import asyncio
import collections
import random
import re
from string import ascii_letters

import discord
import unidecode
from discord.ext import commands

GAMER_REGEX = r"(b+\s*r+\s*u+\s*h+)"
# noinspection SpellCheckingInspection
CATCHPHRASES = [
    "brrmph",
    "chips",
    "tralala",
    "moolah",
    "myohmy",
    "alrighty",
    "swine",
    "skree-haw",
    "grr-ribbit",
    "pine nut",
    "nay",
    "oh ewe",
    "mimimi",
    "wee one",
    "tu-tutu",
    "peach",
    "cheeeeese",
    "sweetie",
    "toots",
    "captain",
    "le ham",
    "nuh uh",
    "strudel",
    "glimmer",
    "zut alors",
    "I s'pose",
    "so it goes",
    "rookie",
    "slushie",
    "la baa",
    "cha",
    "moo-dude",
    "twinkles",
    "Chuuuuurp",
    "nutmeg",
    "harrumph",
    "macmoo",
    "uh-oh",
    "dood",
    "maaan",
    "yaaaawl",
    "nutcase",
    "ooh la la",
    "cardio",
    "meooo-OH",
    "nyoink",
    "crunch",
    "dawg",
    "ol' bear",
    "hoo-rah",
    "greenhorn",
    "squirt",
    "Gimme",
    "sunshine",
    "Stay fresh",
    "frappe",
    "sucker",
    "mon chou",
    "chicken",
    "mrmpht",
    "tenderfoot",
    "sweatband",
    "zzrrbbitt",
    "stuffin'",
    "deelish",
    "fuzzers",
    "honk honk",
    "ah-rooooo",
    "bowes",
    "eaglet",
    "duuude",
    "brrrrrrrrr",
    "yodelay",
    "honeybun",
    "pffffft",
    "bleh eh eh",
    "unh-hunh",
    "hoo hoo ha",
    "Ayyeeee",
    "pudgy",
    "myawn",
    "buhk buhk",
    "ohmmm",
    "bumpkin",
    "zort",
    "bingo",
    "neigh",
    "y'all",
    "whiffa",
    "ribette",
    "crisp",
    "chaps",
    "toady",
    "hulaaaa",
    "aloha",
    "wee baby",
    "vroom",
    "thumper",
    "gruff",
    "eeks",
    "capital",
    "stretch",
    "punches",
    "oh bow",
    "bud",
    "it'sa me",
    "sugarbill",
    "cheeky",
    "schnort",
    "gronk",
    "nightshade",
    "kidders",
    "picante",
    "cheeseball",
    "ol' bunny",
    "buh-kay",
    "okey-dokey",
    "baaa man",
    "WHEE",
    "squee",
    "kerPOW",
    "snappy",
    "nutty",
    "sparky",
    "snoozit",
    "fuzzball",
    "yip yip",
    "snifffff",
    "baaaffo",
    "feathers",
    "bloop",
    "splish",
    "kitty cat",
    "cubbie",
    "indeedaroo",
    "weeweewee",
    "rah rah",
    "wingo",
    "shweetie",
    "WHONK",
    "pushy",
    "yaruwane",
    "burrup",
    "child",
    "quackpth",
    "baboom",
    "snoot",
    "ruffian",
    "kitten",
    "sweet pea",
    "nya",
    "cottontail",
    "yo yo yo",
    "ah-CHOO",
    "glue stick",
    "tootie",
    "reeeeOWR",
    "pockets",
    "pompom",
    "flap flap",
    "sidekick",
    "cagey",
    "bear",
    "grooof",
    "little one",
    "tweedledee",
    "cheekers",
    "hubbub",
    "quackulous",
    "tokana",
    "snarrrl",
    "girlfriend",
    "hay-OK",
    "quacker",
    "teacup",
    "buckaroo",
    "li'l hare",
    "cacaw",
    "slacker",
    "woo-oo",
    "li'l ears",
    "ya heard",
    "rainbow",
    "beaulch",
    "groovy",
    "hot dog",
    "bully",
    "pinky",
    "chow down",
    "ridukulous",
    "aiya",
    "coo-HAH",
    "WHEE",
    "derrrrr",
    "skraaaaw",
    "check it",
    "aye aye",
    "stubble",
    "ayup yup",
    "bleeeeeck",
    "snork",
    "shortcake",
    "pronk",
    "speedy",
    "mango",
    "choo CHOO",
    "kid",
    "sparkles",
    "lambkins",
    "hurk",
    "SKREEE",
    "ne",
    "boing",
    "uni-wow",
    "po po",
    "brah",
    "GAHHHH",
    "silly",
    "Splat!",
    "yawwwn",
    "tooooot",
    "quackidee",
    "hoof hoo",
    "clucky",
    "alpha",
    "sluuuurp",
    "tarnation",
    "CHIRP",
    "dahling",
    "ducky",
    "groonch",
    "haaay",
    "niblet",
    "hello",
    "me-YOWZA",
    "yo",
    "villain",
    "nee-deep",
    "Hah",
    "moocher",
    "buh-uh-ud",
    "Indeed",
    "woo woof",
    "neighbor",
    "toasty",
    "buttercup",
    "non",
    "cud",
    "baaaby",
    "whatevs",
    "hoooonnk",
    "tadder",
    "doyoing",
    "eekers",
    "whiiifff",
    "nougat",
    "grumble",
    "tee-hee",
    "nutlet",
    "arfer",
    "cluckling",
    "quite so",
    "grrr",
    "sugar",
    "sproing",
    "yeah buddy",
    "fuzzy",
    "what what",
    "shrimp",
    "daahling",
    "Zoink",
    "grrRAH",
    "ya know",
    "guvnor",
    "cha-chomp",
    "bonbon",
    "whiskers",
    "zzzzzz",
    "mweee",
    "growf",
    "cubby",
    "baa-dabing",
    "snooooof",
    "doodle-duh",
    "snorty",
    "my pet",
    "shorty",
    "zip zoom",
    "krzzt",
    "pipsqueak",
    "no doy",
    "li'l bear",
    "snoutie",
    "ace",
    "yippee",
    "zzzook",
    "shearly",
    "paaally",
    "cuddles",
    "blurp",
    "squeaky",
    "dearie",
    "rrr-owch",
    "like whoa",
    "sugar cube",
    "bucko",
    "powderpuff",
    "rerack",
    "pound cake",
    "mew",
    "ace",
    "heeeeeyy",
    "flexin",
    "Ruff ruff",
    "schnozzle",
    "bzzert",
    "cluckling",
    "cutie",
    "babe",
    "urgh",
    "ten-hut",
    "odelay",
    "oui oui",
    "bigfoot",
    "how now",
    "purrty",
    "winger",
    "hawkeye",
    "wee one",
    "young 'un",
    "b-b-buddy",
    "hulaaaa",
    "faboom",
    "pah",
    "aaach",
    "quackle",
    "heh heh",
    "snortle",
    "mrowrr",
    "chipmunk",
    "crushy",
    "snort",
    "uh-hoo",
    "bow-WOW",
    "pthhhpth",
    "glitter",
    "karat",
    "arrrn",
    "amigo",
    "hopalong",
    "me-WOW",
    "boosh",
    "grrrolf",
    "mate",
    "lambchop",
    "li'l dude",
    "snacky",
    "punk",
    "rockin'",
    "thump",
    "moo la la",
    "squinky",
    "squeaker",
    "uff da",
    "yelp",
    "quacko",
    "munchie",
    "hipster",
    "nutmeg",
    "precisely",
    "nipper",
    "RAWR",
    "bitty",
    "snoooink",
    "g'tang",
    "purrr",
    "chicky poo",
    "bloop",
    "as if",
    "la-di-da",
    "psst",
    "snortie",
    "dagnaabit",
    "ska-WEAK",
    "laddie",
    "fribbit",
    "my dear",
    "wuh",
    "bunyip",
    "lion cub",
    "biz-aaa",
    "woof",
    "b-b-baby",
    "Highness",
    "d-d-dude",
    "pouches",
    "honk",
    "hippie",
    "beach bum",
    "li'l chick",
    "sooey",
    "bo peep",
    "otaku",
    "tsk tsk",
    "beaker",
    "honey",
    "h-h-hon",
    "snort",
    "ROOOOOWF",
    "nyet",
    "croak-kay",
    "saltlick",
    "splatastic",
    "burrrn",
    "sugar pie",
    "sulky",
    "quacko",
    "ribbit",
    "fromage",
    "lovey",
    "duckling",
    "grooomph",
    "clip-clawp",
    "chimp",
    "foxtrot",
    "chimpy",
    "cheepers",
    "chickadee",
    "snuffle",
    "me meow",
    "puh-lease",
    "cluckadoo",
    "dawayo",
    "waddler",
    "wut",
    "bawwww",
    "monch",
    "airmail",
    "jerky",
    "chuurp",
    "eat it",
    "quaa",
    "cannoli",
    "no doubt",
    "gumdrop",
    "schep",
    "Natch",
    "hopper",
    "chicklet",
    "cool cat",
    "hammie",
    "speedy",
    "ahhhhhh",
    "blih",
    "bun bun",
    "graaagh",
    "pardner",
    "sundae",
    "pal",
]


async def gather_or_cancel(*awaitables):
    """run the awaitables in the sequence concurrently. If any of them raise an exception,
    propagate the first exception raised and cancel all other awaitables.
    """
    gather_task = asyncio.gather(*awaitables)
    # noinspection PyPep8
    try:
        return await gather_task
    except asyncio.CancelledError:
        raise
    except:
        gather_task.cancel()
        raise


class GamerReplacer:
    GAMER_WORD_PARTS = frozenset("ruh")

    def __init__(self, text):
        self.start_index = -1
        self.letter_check = [False] * 4
        self.match_length = 0
        self.spaces = 0
        self.closed = False
        self.text = text

    def reset(self):
        self.start_index = -1
        self.letter_check = [False] * 4
        self.match_length = 0
        self.spaces = 0

    def replace(self):
        if self.closed:
            raise RuntimeError("This replacer is closed")

        indexes = []
        total_length = len(self.text)

        for index, char in enumerate(self.text):
            is_last_char = index + 1 == total_length
            decoded = unidecode.unidecode(char)

            # b is an end check
            if decoded.lower() in self.GAMER_WORD_PARTS:
                self.spaces = 0

            if decoded.lower() == "b":
                if self.start_index == -1:
                    self.start_index = index

                if self.start_index != -1 and sum(self.letter_check) == 4:
                    if self.spaces:
                        self.match_length -= self.spaces

                    indexes.append(
                        (
                            self.match_length,
                            self.start_index,
                            self.start_index + self.match_length,
                        )
                    )
                    self.match_length = len(char)
                    self.letter_check = [True, False, False, False]
                    self.start_index = index
                    self.spaces = 0

                else:
                    self.match_length += len(char)
                    self.letter_check[0] = True
                    self.spaces = 0

            elif decoded.lower() == "r":
                self.match_length += len(char)
                self.letter_check[1] = True

            elif decoded.lower() == "u":
                self.match_length += len(char)
                self.letter_check[2] = True

            elif decoded.lower() == "h":
                self.match_length += len(char)
                self.letter_check[3] = True

            else:
                if self.start_index != -1 and sum(self.letter_check) == 4:
                    if self.spaces:
                        self.match_length -= self.spaces

                    indexes.append(
                        (
                            self.match_length,
                            self.start_index,
                            self.start_index + self.match_length,
                        )
                    )
                    self.reset()

                else:
                    if decoded in ascii_letters:
                        self.reset()

                    else:
                        if char.isspace():
                            self.spaces += 1
                        else:
                            self.spaces = 0

                        if self.start_index != -1:
                            self.match_length += len(char)

            if self.start_index != -1 and sum(self.letter_check) == 4 and is_last_char:
                indexes.append(
                    (
                        self.match_length,
                        self.start_index,
                        self.start_index + self.match_length,
                    )
                )

        indexes = sorted(indexes, key=lambda l: l[1])

        seperated = list(self.text)
        offset = 0
        for length, start, end in indexes:
            start += offset
            end += offset - 1

            replacement = random.choice(CATCHPHRASES)
            seperated[start : end + 1] = replacement

            replaced_len = len(replacement)
            offset += replaced_len - length

        self.closed = True

        return "".join(seperated)


class GamerWords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_cache = collections.defaultdict(
            lambda: collections.defaultdict(list)
        )
        self.server_toggles = {}

        # {guild:{channel:[webhook]}}
        bot.loop.create_task(self.populate_webhook_cache())
        bot.loop.create_task(self.clear_usernames())

    @commands.group(invoke_without_command=True, aliases=["gamerwords"])
    async def gw(self, context):
        """
        Base command for gamerwords commands
        """
        await context.send_help("gamerwords")

    @gw.command()
    @commands.is_owner()
    async def toggle(self, context):
        """
        Toggle the replacer for this server
        """
        if self.server_toggles.get(context.guild.id, None) is None:
            self.server_toggles[context.guild.id] = False

        current = self.server_toggles[context.guild.id]

        if current is True:
            self.server_toggles[context.guild.id] = False
            await context.send("Toggled off")

        else:
            self.server_toggles[context.guild.id] = True
            await context.send("Toggled on")

    @staticmethod
    def has_gamer_words(string):
        string = unidecode.unidecode(string)
        match = re.search(GAMER_REGEX, string, flags=re.IGNORECASE)
        return match

    async def populate_webhook_cache(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                try:
                    for webhook in await channel.webhooks():
                        if webhook.user == guild.me:
                            self.webhook_cache[guild][webhook.channel].append(webhook)
                except discord.HTTPException:
                    continue

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        webhooks = await channel.webhooks()
        webhooks = [webhook for webhook in webhooks if webhook.user == channel.guild.me]
        self.webhook_cache[channel.guild][channel] = webhooks

    async def get_webhook(self, channel):
        try:
            webhook = self.webhook_cache[channel.guild][channel][0]
            return webhook
        except (KeyError, IndexError):
            try:
                webhook = await channel.create_webhook(name="GamerHook")
                return webhook
            except discord.HTTPException:
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.skip_if(message):
            return
        await self.handle_new_gamer_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, old_message, new_message):
        if self.skip_if(old_message):
            return
        await self.handle_new_gamer_message(new_message)

    def skip_if(self, message):
        return (
            message.author.bot
            or not message.guild
            or self.server_toggles.get(message.guild.id, None) in (None, False)
        )

    async def handle_new_gamer_message(self, message):
        text_match = self.has_gamer_words(message.content)
        file_match = any(
            self.has_gamer_words(attachment.filename)
            for attachment in message.attachments
        )
        if text_match or file_match:
            for attach in message.attachments:
                if attach.size >= getattr(
                    message.guild, "filesize_limit", 8 * 1024**2
                ):
                    await message.delete(delay=0.2)
                    return

            async def dl_attach(_attach):
                file = await _attach.to_file()
                if self.has_gamer_words(file.filename):
                    file.filename = GamerReplacer(file.filename).replace()

                return file

            # download all attachments in parallel
            files = await gather_or_cancel(*map(dl_attach, message.attachments))

            try:
                # can't use delete(delay=) because we need to return on exceptions
                await asyncio.sleep(0.2)
                await message.delete()
            except discord.HTTPException:
                return

            if not message.channel.permissions_for(message.guild.me).manage_webhooks:
                return

            webhook = await self.get_webhook(message.channel)
            if not webhook:
                return

            author = message.author

            if message.channel.permissions_for(author).mention_everyone:
                allowed_mentions = discord.AllowedMentions(everyone=True, roles=True)
            else:
                allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)

            await webhook.send(
                content=GamerReplacer(message.content).replace(),
                username=author.display_name,
                avatar_url=str(author.avatar),
                files=files,
                allowed_mentions=allowed_mentions,
            )

    async def clear_usernames(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            if guild.me is None:
                continue

            if not guild.me.guild_permissions.manage_nicknames:
                continue

            for member in guild.members:
                if member.top_role > guild.me.top_role:
                    continue

                match = self.has_gamer_words(member.display_name)
                if match:
                    new_content = GamerReplacer(member.display_name).replace()
                    try:
                        await member.edit(nick=new_content)
                    except discord.Forbidden:
                        # while iterating, we were denied Manage Nicknames
                        continue

    @commands.Cog.listener()
    async def on_member_update(self, old_member, new_member):
        if old_member.display_name == new_member.display_name:
            return
        if old_member.top_role > old_member.guild.me.top_role:
            return
        guild = old_member.guild
        if not guild.me.guild_permissions.manage_nicknames:
            return

        match = self.has_gamer_words(new_member.display_name)
        if match:
            new_content = GamerReplacer(new_member.display_name).replace()
            await new_member.edit(nick=new_content)


async def setup(bot):
    await bot.add_cog(GamerWords(bot))
