from time import time
from discord.ext import commands
import discord

class EvalCommand(commands.Cog):
    def __init__(self,client):
        self.client=client

    def resolve_variable(self, variable):
        if hasattr(variable, "__iter__"):
            var_length = len(list(variable))
            if (var_length > 100) and (not isinstance(variable, str)):
                return f"<a {type(variable).__name__} iterable with more than 100 values ({var_length})>"
            elif (not var_length):
                return f"<an empty {type(variable).__name__} iterable>"

        if (not variable) and (not isinstance(variable, bool)):
            return f"<an empty {type(variable).__name__} object>"
        return (variable if (len(f"{variable}") <= 1000) else f"<a long {type(variable).__name__} object with the length of {len(f'{variable}'):,}>")

    def prepare(self, string):
        arr = string.strip("```").replace("py\n", "").replace("python\n", "").split("\n")
        if not arr[::-1][0].replace(" ", "").startswith("return"):
            arr[len(arr) - 1] = "return " + arr[::-1][0]
        return "".join(f"\n\t{i}" for i in arr)

    @commands.command(pass_context=True, aliases=['eval',  'evaluate'])
    @commands.is_owner()
    async def _eval(self, ctx, *, code: str):
        silent = ("-s" in code)

        code = self.prepare(code.replace("-s", ""))
        args = {
            "discord": discord,
            "client" : self.client,

            "ctx": ctx
        }

        try:
            exec(f"async def func():{code}", args)
            a = time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(response, discord.Message):
                del args, code
                return
            input = code.replace("    return","")
            embed= discord.Embed(color= 0x2f3136 , title="Evaluating Data",description=f"Response time : {round(self.client.latency*1000)} ms")
            embed.add_field(name="Input",value=f"```py\n{input}```",inline=False)
            embed.add_field(name="Output :",value=f"```py\n{self.resolve_variable(response)}```").set_footer(text=f"DATA TYPE : {type(response).__name__}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=0x2f3136,title=f"Error occurred:",description=f"```\n{type(e).__name__}: {str(e)}```"))

        del args, code, silent

def setup(client):
    client.add_cog(EvalCommand(client))
