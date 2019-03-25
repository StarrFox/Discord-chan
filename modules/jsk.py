from jishaku.exception_handling import *

#emojis
task = "thonk:536720018545573928"
done = "glowcheck:536720140025200641"
syntax_error = "glowanix:536720254022320167"
timeout_error = "error:539157627385413633"
error = "glowanix:536720254022320167"

class reactor_sub(ReplResponseReactor):

    async def __aenter__(self):
        self.handle = self.loop.create_task(do_after_sleep(1, attempt_add_reaction, self.message, task))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.cancel()
        if not exc_val:
            await attempt_add_reaction(self.message, done)
            return
        self.raised = True
        if isinstance(exc_val, (asyncio.TimeoutError, subprocess.TimeoutExpired)):
            await attempt_add_reaction(self.message, timeout_error)
        elif isinstance(exc_val, SyntaxError):
            await attempt_add_reaction(self.message, syntax_error)
        else:
            await attempt_add_reaction(self.message, error)

cog.ReplResponseReactor = reactor_sub
cog.JISHAKU_RETAIN = True
cog.JISHAKU_HIDE = True

#This allows us to reload the cog
class sub_jsk(cog.Jishaku): pass

def setup(bot):
    bot.add_cog(sub_jsk(bot))
