# import standard modules
import asyncio
import aiohttp
import datetime
import json

# import discord modules
from discord.ext import commands

# import bot functions and classes
import includes.checks as checks


class Chain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def chain(self, ctx):
        """Toggle chain timeout notifications"""

        # return if chain not active
        if not self.bot.check_module(ctx.guild, "chain"):
            await ctx.send(":x: Chain module not activated")
            return

        # check role and channel
        channelName = self.bot.get_config(ctx.guild).get("chain").get("channel", False)
        ALLOWED_CHANNELS = [channelName] if channelName else ["chain"]
        if await checks.channels(ctx, ALLOWED_CHANNELS):
            pass
        else:
            return

        await ctx.send(":kissing_heart: Start watching")
        while True:

            # check last 5 messages for a stop
            history = await ctx.channel.history(limit=5).flatten()
            stops = [m for m in history if m.content in ["!stop"]]
            if len(stops):
                for m in stops:
                    await m.delete()
                await ctx.send(":sleeping: Stop watching")
                break

            # get key
            key = self.bot.key(ctx.guild)

            # YATA api
            url = f'https://api.torn.com/faction/?selections=chain,timestamp&key={key}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    req = await r.json()

            # handle API error
            if 'error' in req:
                await ctx.send(f':x: There is a API key problem ({req["error"]["error"]})')
                await ctx.send(':x: Stop watching...')
                return

            # get timings
            timeout = req.get("chain", dict({})).get("timeout", 0)
            cooldown = req.get("chain", dict({})).get("cooldown", 0)

            # get delay
            epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
            now = datetime.datetime.utcnow()
            nowts = (now - epoch).total_seconds()
            apits = req.get("timestamp")

            delay = int(nowts - apits)

            # add delay to
            timeout -= delay

            # if cooldown
            if cooldown > 0:
                await ctx.send(':cold_face: Chain in cooldown')
                await ctx.send(':sleeping: Stop watching...')
                return

            # if timeout
            elif timeout == 0:
                await ctx.send(':scream: Chain timed out')
                await ctx.send(':sleeping: Stop watching...')
                return

            # if warning
            elif timeout < 60:
                await ctx.send(f':scream: Chain timeout in {timeout} seconds {ctx.guild.default_role}')

            else:
                await ctx.send(f':sunglasses: I\'m still watching... chain timeout in {timeout/60:.1f} minutes')

            # sleeps
            sleep = max(30, timeout)
            print(f"API delay of {delay} seconds, timeout of {timeout}: sleeping for {sleep} seconds")
            await asyncio.sleep(sleep)