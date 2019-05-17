from discord.ext import commands, tasks
import discord
import datetime
from extras import utils
import random
import humanize

#Checks for commands
async def is_nubby_or_owner(ctx):
    return await ctx.bot.is_owner(ctx.author) or ctx.author.id == 176796254821548033

def is_above_mod(ctx):
    mod_role = ctx.bot.get_guild(390607785437691916).get_role(396797202779078657)
    return ctx.author.top_role.position >= mod_role.position

def above_mod(member):
    mod_role = member.guild.get_role(396797202779078657)
    return member.top_role.position >= mod_role.position

class nubby(commands.Cog):
    """
    Set of commands and events for Nubby's guild
    """

    def __init__(self, bot):
        self.bot = bot
        self.guild = bot.get_guild(390607785437691916)
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
        self.command_channel = self.bot.get_channel(442823830902145034)
        self.check_twoweeks.start()
        self.verify_role = self.guild.get_role(578777612701401090)
        self.verify_chat = self.bot.get_channel(578771669288615936)
        self.verify_logs = self.bot.get_channel(578771629312704513)
        self.member_role = self.guild.get_role(439723301238210560)
        self.verify_dm_msgs = {} #member.id: message
        self.verify_off = False

    async def cog_check(self, ctx):
        return ctx.guild == self.guild

    async def verify(self, member):
        await member.add_roles(self.verify_role)
        await self.verify_logs.send(utils.block(f"Verify process started for {member.name} created: {member.created_at.strftime('%c')} ({humanize.naturaltime(member.created_at)})"))
        try:
            await member.send(f"Hello and welcome to Nubby's spoiler discord\nIn order to join the rest of the discord you must first verify by sending `{hash(member)}` here")
        except:
            self.verify_dm_msgs[member.id] = await self.verify_chat.send(f"Hey {member.mention} can you turn on dms so I can verify you; send `ready` to start the process")
            await self.verify_logs.send(utils.block(f"{member.name} had dms off so I sent them a message in #{self.verify_chat.name}"))

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.verify_off:
            return
        nub_g = self.guild.get_member(message.author.id)
        if not nub_g or not self.verify_role in nub_g.roles:
            return
        if message.channel == self.verify_chat and message.content.lower() == "ready" and nub_g.id in self.verify_dm_msgs.keys():
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
                self.verify_dm_msgs[nub_g.id] = await self.verify_chat.send(f"{nub_g.mention} you still have dms off; use this picture and send `ready` after finishing {help_link}")
        if message.content == str(hash(nub_g)) and not message.guild or message.content == str(hash(nub_g)) and message.channel == self.verify_chat:
            await nub_g.add_roles(self.member_role)
            await nub_g.remove_roles(self.verify_role)
            try:
                await message.delete()
            except:
                pass
            await self.verify_logs.send(utils.block(f"Verified {nub_g.name} after {humanize.naturaltime(nub_g.joined_at)} ({nub_g.joined_at.strftime('%c')})"))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild != self.guild:
            return
        await self.verify(member)

    @commands.command()
    async def cool(self, ctx, member: discord.Member = None):
        if not member:
            member = self.guild.get_member(204600313485852672)
        await ctx.send(f"Thanks {member.display_name}, very cool!")

    @commands.command()
    async def laval(self, ctx):
        await ctx.send(random.choice(self.laval_quotes))

    async def get_twoweeks(self):
        target_roles = [self.guild.get_role(i) for i in [501092781473792020, 439723470667120640]]
        processed = [] #Returned positive
        for member in self.guild.members:
            checks = [
                member.bot,
                target_roles[0] in member.roles and target_roles[1] in member.roles,
                self.verify_role in member.roles,
                not member.joined_at + datetime.timedelta(weeks=2) < datetime.datetime.utcnow()
            ]
            if any(checks):
                continue
            processed.append(member)
        return processed

    @tasks.loop(hours=1)
    async def check_twoweeks(self):
        processed = await self.get_twoweeks()
        if processed:
            await self.command_channel.send(f"@here there are/is {len(processed)} without required roles use dc!twoweeks to add them")

    @commands.command(name="verify")
    @commands.check(is_above_mod)
    async def verify_command(self, ctx, mode: bool = None):
        """
        Toggles the current verify state
        """
        if mode is None:
            if not self.verify_off:
                return await ctx.send("Verify is currently on")
            return await ctx.send("Verify is currentrly off")
        if mode:
            self.verify_off = True
            return await ctx.send("Turned verify off")
        self.verify_off = False
        await ctx.send("Turned verify on")

    @commands.command()
    @commands.check(is_above_mod)
    async def twoweeks(self, ctx):
        target_roles = [self.guild.get_role(i) for i in [501092781473792020, 439723470667120640]]
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

def setup(bot):
    bot.add_cog(nubby(bot))
