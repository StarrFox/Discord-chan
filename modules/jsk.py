import jishaku

jishaku.cog.JISHAKU_RETAIN = True
jishaku.cog.JISHAKU_HIDE = True

def setup(bot):
    bot.add_cog(jishaku.cog.Jishaku(bot))
