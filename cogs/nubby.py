from discord.ext import commands, tasks
import discord

import datetime
import random
import humanize
import typing

from extras import utils

async def is_nubby_or_owner(ctx):
    return await ctx.bot.is_owner(ctx.author) or ctx.author.id == 176796254821548033

def is_above_mod():
    def pred(ctx):
        mod_role = ctx.bot.get_guild(390607785437691916).get_role(396797202779078657)
        return ctx.author.top_role.position >= mod_role.position
    return commands.check(pred)

def above_mod(member):
    mod_role = member.guild.get_role(396797202779078657)
    return member.top_role.position >= mod_role.position

bool_dict = {
    "true": True,
    "on": True,
    "1": True,
    "false": False,
    "off": False,
    "0": False
}

class nubby(commands.Cog):
    """
    Set of commands and events for Nubby's guild
    """

    def __init__(self, bot):
        self.bot = bot
        self.laval_quotes = [
            "I'm not in the mood for your bull shit. Purchase a razor and slit your throat for all I care. Waste of carbon anyways.",
            "Well... I would be lying if I didn't have a hatred towards lesser beings that purposes intends to remain a lesser being.",
            "Non sense, I'm perfectly fine and civil like a gentleman.",
            "leave my fursuit out of this!",
            "I cOuLD bE pLaYiNg AnImAL CoVe",
            "I wasn't talking to you Aaron, you could be raped and left for dead on the road and I still wouldn't bat an eye",
            "Too be honest, I've had more toxic talk on barrens chat in World of Warcraft and these haters would be called pussys for their epic fail attempted of bashing.",
            "Since most of you dumb shits didn't even bother watching the producer's video; that flat out told you these updates were coming and they didn't put these on test realms so people like nubby wouldn't data mine it so there's something to look forward too; you just spewed your bull shit as usual.",
            "You miserable ungrateful piss ants! How dare you insects go after me!",
            "Laval Prideland here, you guys know nothing. Contrary to what Justin says, I am much smarter than him, and possibly all of you here. I have every move that any of you can make against me mapped, predicted, and destroyed. Simpletons. Surely you believe I am a close friend of sir Decius? He shows me everything including the new mobile games that Kingsisle is making. I am not here for the riffraff of the Discords, I am only here for my holy lord, Nubby. I deeply hope he will show me the secrets of datamining and the Kingsisle games. In fact, I am the only one here who has a chance of getting that. None of you trolls know anything about me or the ethereal secrets of Wizard101. I applaud your arrogance and cunning, but certainly, you know of my wittiness? Any joke that you make me the butt of, will be reversed right back on you. Don't even bother, you will only be outwitted and humiliated in front of the good people of the Kingsisle community. As you ridicule me, I will ridicule you back in a thousand different ways that you cannot even comprehend. And no, I do not accept acts of sexual nature, to any of the female humans here who admire me, as I am celibate. Again, I must warn you, back down before you make fools out of yourselves against the minotaur of Kingsisle Entertainment, me. I will show no mercy on idiots such as the likes of you."
        ]
        self.check_twoweeks.start()
        self.verify_dm_msgs = {} #member.id: message
        guild = self.bot.get_guild(390607785437691916)
        self.guild_settings = {
            "guild": 390607785437691916,
            "strike_noperm": True,
            "twoweeks_check": True,
            "commands_channel": bot.get_channel(442823830902145034),
            "member_role": guild.get_role(439723301238210560),
            "first_strike": guild.get_role(579370927389802499),
            "second_strike": guild.get_role(579370927943450626),
            "third_strike": guild.get_role(579370928987963396)
        }
        self.verify_settings = {
            "on": False,
            "block_verify": False,
            "kick_under_one_hour": False,
            "role": guild.get_role(578777612701401090),
            "chat": bot.get_channel(578771669288615936),
            "logs": bot.get_channel(578771629312704513)
        }

    async def cog_check(self, ctx):
        return ctx.guild.id == self.guild_settings["guild"]

    def cog_unload(self):
        self.check_twoweeks.cancel()

    async def verify(self, member):
        if self.verify_settings["kick_under_one_hour"] and member.created_at > datetime.datetime.utcnow() - datetime.timedelta(hours=1):
            await member.kick(reason="Made less than an hour ago")
            return await self.verify_settings["logs"].send(utils.block(f"{member} ({member.id}) kicked for being made less than an hour ago"))
        if not self.verify_settings["on"]:
            return await member.add_roles(self.guild_settings["member_role"])
        await member.add_roles(self.verify_settings["role"])
        await self.verify_settings["logs"].send(utils.block(f"Verify process started for {member} ({member.id}) created: {member.created_at.strftime('%c')} ({humanize.naturaltime(member.created_at)})"))
        try:
            await member.send(f"Hello and welcome to Nubby's spoiler discord\nIn order to join the rest of the discord you must first verify by sending `{hash(member)}` here")
        except:
            self.verify_dm_msgs[member.id] = await self.verify_settings["chat"].send(f"Hey {member.mention} can you turn on dms so I can verify you; send `ready` to start the process")
            await self.verify_settings["logs"].send(utils.block(f"{member} ({member.id}) had dms off so I sent them a message in #{self.verify_settings['chat'].name}"))

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.verify_settings["block_verify"]:
            return
        nub_g = self.bot.get_guild(self.guild_settings["guild"]).get_member(message.author.id)
        if not nub_g or not self.verify_settings["role"] in nub_g.roles:
            return
        if message.channel == self.verify_settings["chat"] and message.content.lower() == "ready" and nub_g.id in self.verify_dm_msgs.keys():
            if nub_g.is_on_mobile():
                help_link = "https://cdn.discordapp.com/attachments/439732172598018049/578809194560356362/3.png"
            else:
                help_link = "https://cdn.discordapp.com/attachments/439732172598018049/578799171260252181/unknown.png"
            try:
                await self.verify_dm_msgs[nub_g.id].delete()
                await message.delete()
            except:
                pass
            try:
                await nub_g.send(f"Hello and welcome to Nubby's spoiler discord\nIn order to join the rest of the discord you must first verify by sending `{hash(nub_g)}` here")
            except:
                self.verify_dm_msgs[nub_g.id] = await self.verify_settings["chat"].send(f"{nub_g.mention} you still have dms off; use this picture and send `ready` after finishing {help_link}")
        if message.content == str(hash(nub_g)) and not message.guild or message.content == str(hash(nub_g)) and message.channel == self.verify_settings["chat"]:
            await nub_g.add_roles(self.guild_settings["member_role"])
            await nub_g.remove_roles(self.verify_settings["role"])
            try:
                await message.delete()
            except:
                pass
            await self.verify_settings["logs"].send(utils.block(f"Verified {nub_g} ({nub_g.id}) after {humanize.naturaltime(nub_g.joined_at).replace(' ago', '')} ({nub_g.joined_at.strftime('%c')})"))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.guild_settings["guild"]:
            return
        await self.verify(member)

    @commands.command()
    async def cool(self, ctx, member: discord.Member = None):
        await ctx.send(f"Thanks {member.display_name if member else 'Laval'}, very cool!")

    @commands.command()
    async def laval(self, ctx):
        await ctx.send(random.choice(self.laval_quotes))

    async def get_twoweeks(self):
        guild = self.bot.get_guild(self.guild_settings["guild"])
        target_roles = [guild.get_role(i) for i in [501092781473792020, 439723470667120640]]
        processed = [] #Returned positive
        for member in guild.members:
            checks = [
                member.bot,
                target_roles[0] in member.roles and target_roles[1] in member.roles,
                self.verify_settings["role"] in member.roles,
                not member.joined_at + datetime.timedelta(weeks=2) < datetime.datetime.utcnow()
            ]
            if self.guild_settings["strike_noperm"]:
                checks.append(self.guild_settings["first_strike"] in member.roles or self.guild_settings["second_strike"] in member.roles or self.guild_settings["third_strike"] in member.roles)
            if any(checks):
                continue
            processed.append(member)
        return processed

    @tasks.loop(hours=1)
    async def check_twoweeks(self):
        if not self.guild_settings["twoweeks_check"]:
            return
        processed = await self.get_twoweeks()
        if processed:
            await self.guild_settings["commands_channel"].send(f"@here there are/is {len(processed)} without required roles use dc!twoweeks to add them")

    @commands.command(name="verify")
    @is_above_mod()
    async def manual_verify(self, ctx, *members: discord.Member):
        """
        Manually verify someone or a group of people

        Ex of multi verify:
        verify @StarrFox @justin @nubby
        """
        for target in members:
            await target.remove_roles(self.verify_settings["role"])
            await target.add_roles(self.guild_settings["member_role"])
        await ctx.send(f"Verified {len(members)} members")

    @commands.command()
    @is_above_mod()
    async def raid(self, ctx, value: bool = True):
        """
        Shortcut to settings block_verify True/False
        """
        self.verify_settings["block_verify"] = value
        await ctx.send("changed")

    @commands.group()
    @is_above_mod()
    async def settings(self, ctx, item: typing.Optional[str] = None, value: str = None):
        """
        View and change settings for verify and guild
        """
        guild = self.bot.get_guild(self.guild_settings["guild"])
        if item is None and value is None:
            def thrower(target: dict):
                result = ""
                for k, i in target.items():
                    if not isinstance(i, bool):
                        result += f"{k}: {i.name} ({i.id})\n"
                    else:
                        result += f"{k}: {i}\n"
                return result
            return await ctx.send(utils.block(thrower(self.verify_settings) + thrower(self.guild_settings)))
        def try_dict(base: dict):
            if not item in base.keys():
                return False
            if isinstance(base[item], discord.TextChannel):
                test_none = self.bot.get_channel(int(value))
                if test_none is None:
                    return False
                base[item] = test_none
                return True
            elif isinstance(base[item], discord.Role):
                test_none = guild.get_role(int(value))
                if test_none is None:
                    return False
                base[item] = test_none
                return True
            elif isinstance(base[item], bool):
                if not value.lower() in bool_dict.keys():
                    return False
                base[item] = bool_dict[value.lower()]
                return True
            elif isinstance(base[item], discord.Guild):
                test_none = self.bot.get_guild(int(value))
                if test_none is None:
                    return False
                base[item] = test_none
                return True
        guild_test = try_dict(self.guild_settings)
        if guild_test:
            return await ctx.send("Changed")
        verify_test = try_dict(self.verify_settings)
        if verify_test:
            return await ctx.send("Changed")
        await ctx.send("Invalid item or value")

    @commands.command()
    @is_above_mod()
    async def twoweeks(self, ctx):
        guild = self.bot.get_guild(self.guild_settings["guild"])
        target_roles = [guild.get_role(i) for i in [501092781473792020, 439723470667120640]]
        processed = await self.get_twoweeks()
        if not processed:
            return await ctx.send("Everything is balanced, as it should be.")
        msg = "Members that need the roles:\n"+"\n".join([i.name for i in processed])
        await utils.paginate(msg, ctx)
        target_msg = await ctx.send("React with \N{HEAVY PLUS SIGN} to add their roles, one by one #Nubbyfied")
        await target_msg.add_reaction("\N{HEAVY PLUS SIGN}")
        while len(processed) != 0:
            def check(r, u):
                checks = [
                    above_mod(u),
                    not u.bot,
                    r.message.id == target_msg.id,
                    str(r) == "\N{HEAVY PLUS SIGN}"
                ]
                return all(checks)
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=300)
                target = processed[-1]
                for role in target_roles:
                    await target.add_roles(role)
                async for user in reaction.users():
                    if user.id != self.bot.user.id:
                        await reaction.remove(user)
                await ctx.send(f"Added {target.name}'s roles")
                processed.remove(target)
            except:
                await ctx.send("Timed out")
                return
        await ctx.send("All roles added")

    @commands.command(hidden=True)
    async def british(self, ctx):
        await ctx.message.delete()
        await ctx.send(ctx.guild.owner.mention, delete_after=1)

    @commands.command(hidden=True)
    async def justin(self, ctx):
        await ctx.message.delete()
        await ctx.send("<@!395395617167245322>", delete_after=1)

def setup(bot):
    bot.add_cog(nubby(bot))
