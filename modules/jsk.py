from jishaku import cog

cog.JISHAKU_RETAIN = True
cog.JISHAKU_HIDE = True

class sub_jsk(cog.Jishaku): pass

def setup(bot):
    bot.add_cog(sub_jsk(bot))
