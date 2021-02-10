#!/usr/bin/env python3
# Work with Python 3.7+

import logging
import json
import random
from datetime import datetime, timedelta

import asyncio
import aiohttp
import discord
import pytz


logging.basicConfig(format="%(asctime)s | %(levelname)s:%(name)s:%(message)s",
                    filename='heimdall.log', level=logging.INFO)
logging.info('----- Started -----')

with open("auth.json") as data_file:
    auth = json.load(data_file)
with open("links.json") as data_file:
    data = json.load(data_file)
with open("params.json") as data_file:
    params = json.load(data_file)
with open("market.json") as data_file:
    markets = json.load(data_file)

TOKEN = auth["token"]
HEADERS = {}
HEADERS["X-CMC_PRO_API_KEY"] = auth["cmc_headers"]
BOT_PREFIX = "!"
TICKER = "TENT"

intents = discord.Intents(messages=True, guilds=True)
intents.reactions = True
intents.members = True
intents.emojis = True
intents.presences = True
intents.typing = False

client = discord.Client(intents=intents)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def save_diary_file(message):
    with open("dev-diary.json") as data_file:
        listed = json.load(data_file)
    listed.append(message)
    file = open("dev-diary.json", "w")
    file.write(json.dumps(listed, indent=2, sort_keys=True, default=str))
    file.close()


def calculate_supply(block_height):
    if block_height < 8_000:
        return 80_000

    epochs, remainder = divmod(block_height - 1, 2102400)
    previous_epochs_total_reward = sum(2102400 * (20 / (2 ** epoch)) for epoch in range(epochs))
    current_epoch_reward = 20 / (2 ** epochs)
    current_total_reward = (remainder + 1) * current_epoch_reward
    return previous_epochs_total_reward + current_total_reward - 79_980


async def price_update_channel():
    await client.wait_until_ready()
    channel = client.get_channel(592633967346188307)
    while not client.is_closed():
        async with aiohttp.ClientSession() as session:
            async with session.get(data["stex"]) as stex_data:
                if stex_data.status == 200:
                    stex_api = await stex_data.json(content_type=None)
                    price_in_sats = pow(10, 8) * float(stex_api["data"]["last"])
                    channel_name = f"tent-{price_in_sats:.0f}-sats"
                else:
                    print(f"{data['rates']} is down")
                    channel_name = "tent-unknown-sats"
        await channel.edit(name=channel_name)
        await asyncio.sleep(300)  # task runs every 5 minutes


async def report_not_reporting():
    await client.wait_until_ready()
    channel = client.get_channel(747732496350838806)
    while not client.is_closed():
        fetchMessage = await channel.history(limit=50).find(lambda m: m.author.id == 747733342899798017)
        if fetchMessage is not None:
            message_time = fetchMessage.created_at
            utc_time_now = datetime.utcnow()
            if message_time + timedelta(hours=1, minutes=15) < utc_time_now:
                message = (
                    f"<@246215587464740864><@359782573066551320><@283899213845233664><@398885783395893258>\n"
                    + f"\nLast report time: {message_time}\nTime now: {utc_time_now}\nHave not seen a report in "
                    + f"last 2 minutes!!!\n\n**CHECK IF THE SERVER IS BURNING!!!!**")
                await channel.send(message)
        await asyncio.sleep(240)  # task runs every 4 minutes


@client.event
async def on_message(msg):
    # Bot will save all the messages in #dev-diary channel into a text file
    if msg.channel.id == 757921991201128500:

        dictionar = {}
        dictionar["author"] = msg.author.name
        dictionar["created_at"] = msg.created_at
        dictionar["content"] = msg.content
        for i in range(len(msg.embeds)):
            key = "embed_" + str(i)
            dictionar[key] = msg.embeds[i].to_dict()
        message = dictionar
        save_diary_file(message)
        return
    # Bot will keep #asgard-reporting channel clean &
    # will keep only last report of each server
    if msg.channel.id == 747732496350838806:
        list_of_messages = []
        async for x in msg.channel.history():
            if msg.author.bot:
                list_of_messages.append(x)
                if len(list_of_messages) > 3:
                    list_of_messages = list_of_messages[3:]
                    await msg.channel.delete_messages(list_of_messages)
        return
    # We do not want the bot to respond to Bots or Webhooks
    if msg.author.bot:
        return
    # We want the bot to not answer to messages that have no content
    # (example only attachment messages)
    # Bot checks BOT_PREFIX
    if not msg.content or msg.content[0] != BOT_PREFIX:
        return
    # Bot ignore all system messages
    if msg.type is not discord.MessageType.default:
        return

    args = msg.content[1:].split()
    cmd = args[0].lower()

    # Bot runs in #bot-commands channel and private channels for everyone
    # Bot runs in all channels for specific roles
    if not (
        isinstance(msg.channel, discord.DMChannel)
        or msg.channel.name == "bot-commands"
        or "CoreTeam" in [role.name for role in msg.author.roles]
        or "Moderator" in [role.name for role in msg.author.roles]
        or "Ambassador" in [role.name for role in msg.author.roles]
    ):
        message = f"{data['default']}"
        await msg.channel.send(message)
        return

    # Bot responds to mee6 commands if in unaccepted channel
    if not (isinstance(msg.channel, discord.DMChannel) or msg.channel.name == "bot-commands") and (
        cmd == "help" or cmd == "rank" or cmd == "levels"
    ):
        message = f"{data['mee6']}"
        await msg.channel.send(message)
        return
    # ---- <ignored commands in bot-commands> ----
    if cmd == "help" or cmd == "rank" or cmd == "levels" or cmd == "tip":
        return
    # -------- <commands> --------
    elif cmd == "commands":
        message = "\n".join(data["commands"])
    # -------- <links> --------
    elif cmd == "links":
        message = "\n".join(data["links"])
    # -------- <net/netinfo> --------
    elif cmd == "net" or cmd == "netinfo":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["blocks_info"]) as blocks_info:
                if blocks_info.status == 200:
                    blocks_api = await blocks_info.json()
                else:
                    print(f"{data['blocks_info']} is down")
        avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        async with aiohttp.ClientSession() as session:
            async with session.get(data["difficulty"]) as difficulty:
                if difficulty.status == 200:
                    difficulty_api = await difficulty.json()
                else:
                    print(f"{data['difficulty']} is down")
        diff = difficulty_api["difficulty"]
        async with aiohttp.ClientSession() as session:
            async with session.get(data["net_hash"]) as net_hash:
                if net_hash.status == 200:
                    net_hash_api = await net_hash.json()
                else:
                    print(f"{data['net_hash']} is down")
        version = params["daemon_ver"]
        hashrate = net_hash_api["info"]["networksolps"]
        message = (
            f"• Version • **{version}**\n• Block Height • **{last_block:,}**\n• Avg Block Time • **{round(avg_bt, 2)}"
            + f" s**\n• Network Hashrate • **{int(hashrate)/1000} kSol/s**\n• Network Difficulty • **{diff:1.3f}**"
        )
    # -------- <mn/mninfo> --------
    elif cmd == "mn" or cmd == "mninfo":
        avg_bt = 60
        async with aiohttp.ClientSession() as session:
            async with session.get(data["masternodes"]["link"]) as masternodes:
                if masternodes.status == 200:
                    mn_raw = await masternodes.text()
                else:
                    print(f"{data['masternodes']['link']} is down")
        if len(args) < 2:
            mn_count = mn_raw.count("ENABLED")
            if mn_count == 0:
                mn_count = params["mn_count"]
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(data["asgard_managed"]) as asgard_mns:
                        asgard_managed = await asgard_mns.text()
                except Exception:
                    asgard_managed = 0
                    print(f"{data['asgard_managed']} is down")
            mn_rwd = params["mn_rwd"]
            guide_link = data["masternodes"]["guide_link"]
            asgard = data["masternodes"]["asgard"]
            asgard_vid = data["masternodes"]["asgard_vid"]
            mn_roi = mn_rwd * 3153600 / avg_bt / mn_count / 10
            time_first_payment = 2.6 * mn_count / 60
            message = (
                f"• Active masternodes • **{mn_count: 1.0f}** (_**{asgard_managed}** managed by **Asgard**_)\n• "
                + f"Coins Locked • **{mn_count*10000:,} {TICKER}**\n• ROI "
                + f"• **{mn_roi: 1.3f} % **\n• Minimum time before first payment • **{time_first_payment: 1.2f} hours**"
                + f"\n• One masternode will give you approximately **{3600*24/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** per"
                + f" **day**\n{asgard}\n{asgard_vid}\n{guide_link}"
            )
            await msg.channel.send(message)
            return
        cmd1 = args[1]
        mn_list = eval(mn_raw)
        if any(d["addr"] == cmd1 for d in mn_list):
            for i in range(len(mn_list)):
                if mn_list[i]["addr"].lower() == cmd1.lower():
                    address = mn_list[i]["addr"]
                    status = mn_list[i]["status"]
                    rank = mn_list[i]["rank"]
                    lastseen = datetime.fromtimestamp(mn_list[i]["lastseen"]).strftime("%d-%m-%Y %H:%M:%S")
                    activetime = mn_list[i]["activetime"]
                    days = activetime // (24 * 3600)
                    activetime = activetime % (24 * 3600)
                    hours = activetime // 3600
                    activetime %= 3600
                    minutes = activetime // 60
                    activetime %= 60
                    seconds = activetime
                    lastpaid = datetime.fromtimestamp(mn_list[i]["lastpaid"]).strftime("%d-%m-%Y %H:%M:%S")
                    message = (
                        f"• Address • **{address}**\n• Status • **{status}**\n• Rank • **{rank}**\n• Last seen • **"
                        + f"{lastseen}**\n• Active time • **{days} days {hours}h:{minutes}m:{seconds}s**\n• Last paid"
                        + f" • **{lastpaid}**"
                    )
                    await msg.channel.send(message)
                    return
        else:
            message = "Masternode not found! Please check it in your wallet."
    # -------- <hpow/calc> --------
    elif cmd == "hpow" or cmd == "calc":
        avg_bt = 60
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["difficulty"]) as difficulty:
                if difficulty.status == 200:
                    difficulty_api = await difficulty.json()
                else:
                    print(f"{data['difficulty']} is down")
        diff = difficulty_api["difficulty"]
        async with aiohttp.ClientSession() as session:
            async with session.get(data["net_hash"]) as net_hash:
                if net_hash.status == 200:
                    net_hash_api = await net_hash.json()
                else:
                    print(f"{data['net_hash']} is down")
        hashrate = net_hash_api["info"]["networksolps"]
        if len(args) < 2:
            message = f"{data['hpow']['default']}"
            await msg.channel.send(message)
            return
        cmd1 = args[1].lower()
        if cmd1 == "infinity" or cmd1 == "infinite" or cmd1 == "inf":
            message = f"{data['hpow']['infinity']}"
        elif not is_number(cmd1):
            message = f"{data['hpow']['default']}"
        elif cmd1 == "0":
            message = f"{data['hpow']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['hpow']['neg']}"
        elif is_number(cmd1):
            mnr_rwd = params["mnr_rwd"]
            cmd1 = float(cmd1)
            message = (
                f"Current network hashrate is **{int(hashrate)/1000:1.2f} KSols/s**.\nA hashrate of **{cmd1:1.0f}"
                + f" Sols/s** will get you approximately **{cmd1/hashrate*3600*mnr_rwd/avg_bt:1.2f} {TICKER}** _(***"
                + f"{cmd1/hashrate*3600*mnr_rwd/avg_bt*tent_usd_price:1.2f}$***)_ per **hour** and **"
                + f"{cmd1/hashrate*3600*mnr_rwd*24/avg_bt:1.2f} {TICKER}** _(***"
                + f"{cmd1/hashrate*3600*mnr_rwd*24/avg_bt*tent_usd_price:1.2f}$***)_ per **day** at current "
                + "network difficulty."
            )
    # -------- <mnrew/mnrewards> --------
    elif cmd == "mnrew" or cmd == "mnrewards":
        avg_bt = 60
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["masternodes"]["link"]) as masternodes:
                if masternodes.status == 200:
                    mn_raw = await masternodes.text()
                else:
                    print(f"{data['masternodes']['link']} is down")
        mn_count = mn_raw.count("ENABLED")
        if mn_count == 0:
            mn_count = params["mn_count"]
        mn_rwd = params["mn_rwd"]
        if len(args) < 2:
            message = (
                f"**1** Masternode will give you approximately:"
                + f"\n**{3600*24/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{3600*24/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **day**"
                + f"\n**{3600*24*7/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{3600*24*7/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **week**"
                + f"\n**{3600*24*30/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{3600*24*30/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **month**"
                + f"\n**{3600*24*365/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{3600*24*365/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **year**"
            )
            await msg.channel.send(message)
            return
        cmd1 = args[1].lower()
        if not is_number(cmd1):
            message = f"{data['mnrewards']['default']}"
        elif cmd1 == "0":
            message = f"{data['mnrewards']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['mnrewards']['neg']}"
        elif is_number(cmd1):
            cmd1 = float(cmd1)
            message = (
                f"**{cmd1:1.0f}** Masternode will give you approximately:"
                + f"\n**{cmd1*3600*24/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{cmd1*3600*24/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **day**"
                + f"\n**{cmd1*3600*24*7/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{cmd1*3600*24*7/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **week**"
                + f"\n**{cmd1*3600*24*30/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{cmd1*3600*24*30/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **month**"
                + f"\n**{cmd1*3600*24*365/avg_bt*mn_rwd/mn_count:1.3f} {TICKER}** _(***"
                + f"{cmd1*3600*24*365/avg_bt*mn_rwd/mn_count*tent_usd_price:1.3f}$***)_ per **year**"
            )
    # -------- <tentusd> --------
    elif cmd == "tentusd":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        if len(args) < 2:
            message = f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$***._"
            await msg.channel.send(message)
            return
        cmd1 = args[1].lower()
        if not is_number(cmd1):
            message = f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$***._"
        elif cmd1 == "0":
            message = f"{data['tentusd']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['tentusd']['neg']}"
        elif is_number(cmd1):
            message = (
                f"**{round(float(cmd1),2):,} {TICKER}** = **{round(float(tent_usd_price)*float(cmd1),2):,}$**\n"
                + f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$***_"
            )
    # -------- <usdtent> --------
    elif cmd == "usdtent":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        if len(args) < 2:
            message = f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$***._"
            await msg.channel.send(message)
            return
        cmd1 = args[1].lower()
        if not is_number(cmd1):
            message = f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$***._"
        elif cmd1 == "0":
            message = f"{data['tentusd']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['tentusd']['neg']}"
        elif is_number(cmd1):
            message = (
                f"**{round(float(cmd1),2):,}$** = **{round(float(cmd1)/float(tent_usd_price),2):,} {TICKER}**\n"
                + f"{data['tentusd']['default']}{round(tent_usd_price, 3)}$**_"
            )
    # -------- <roadmap> --------
    elif cmd == "roadmap":
        message = f"{data['roadmap']}"
    # -------- <proof of review> --------
    # elif cmd == "por":
    #    message = f"{data['por']}"
    # -------- <market [stats]> --------
    elif cmd == "market":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_btc"], headers=HEADERS) as cmc_btc:
                if cmc_btc.status == 200:
                    cmc_btc_api = await cmc_btc.json()
                    btc_usd_price = float(cmc_btc_api["data"]["BTC"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_btc']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_eth"], headers=HEADERS) as cmc_eth:
                if cmc_eth.status == 200:
                    cmc_eth_api = await cmc_eth.json()
                    eth_usd_price = float(cmc_eth_api["data"]["ETH"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_btc']} is down")
        message_list = []
        message_list.append("**TENT** is listed on the following exchanges:")
        for a in range(len(markets)):
            message_list.append(f"{a+1}. <{markets[a]['link']}>")
        message_list.append("\n_Use `!market info` for stats of the markets_")
        if len(args) < 2 or args[1].lower() != "info":
            message = "\n".join(message_list)
        else:
            vol_total = 0
            for a in range(len(markets)):
                if markets[a]["link"] == "https://app.stex.com/en/trade/pair/BTC/TENT":
                    async with aiohttp.ClientSession() as session:
                        async with session.get(markets[a]["api"]) as api:
                            if api.status == 200:
                                markets_api = await api.json()
                                markets[a]["volume_24h"] = tent_usd_price * float(markets_api["data"]["volumeQuote"])
                                usd_price = btc_usd_price * float(markets_api["data"]["last"])
                                markets[a]["price"] = usd_price
                            else:
                                print(f"{markets[a]['api']} is down")
                    vol_total = vol_total + float(markets[a]["volume_24h"])
                elif markets[a]["link"] == "https://mercatox.com/exchange/XSG/BTC":
                    async with aiohttp.ClientSession() as session:
                        async with session.get(markets[a]["api"]) as api:
                            if api.status == 200:
                                markets_api = await api.json(content_type="text/html")
                                markets[a]["volume_24h"] = tent_usd_price * float(
                                    markets_api["pairs"]["TENT_BTC"]["baseVolume"]
                                )
                                usd_price = btc_usd_price * float(markets_api["pairs"]["TENT_BTC"]["last"])
                                markets[a]["price"] = usd_price
                            else:
                                print(f"{markets[a]['api']} is down")
                    vol_total = vol_total + float(markets[a]["volume_24h"])
                elif markets[a]["link"] == "https://mercatox.com/exchange/XSG/ETH":
                    async with aiohttp.ClientSession() as session:
                        async with session.get(markets[a]["api"]) as api:
                            if api.status == 200:
                                markets_api = await api.json(content_type="text/html")
                                markets[a]["volume_24h"] = tent_usd_price * float(
                                    markets_api["pairs"]["TENT_ETH"]["baseVolume"]
                                )
                                usd_price = eth_usd_price * float(markets_api["pairs"]["TENT_ETH"]["last"])
                                markets[a]["price"] = usd_price
                            else:
                                print(f"{markets[a]['api']} is down")
                    vol_total = vol_total + float(markets[a]["volume_24h"])
            max_source = 0
            for a in range(len(markets)):
                markets[a]["vol_percent"] = float(markets[a]["volume_24h"]) / vol_total * 100
                max_source = max(6, max_source, len(markets[a]["source"]))
            markets.sort(key=lambda x: x["volume_24h"], reverse=True)
            with open("market.json", "w") as file:
                json.dump(markets, file, indent=2)
            message = """
```
+--+-------{a}-+-----------+-------------+----------+---------+
| #| Source{0} | Pair      |   Vol (24h) |    Price | Vol (%) |
+--+-------{a}-+-----------+-------------+----------+---------+
{markets}
+--+-------{a}-+-----------+-------------+----------+---------+
```
""".format(
                " " * (max_source - 6),
                a="-" * (max_source - 6),
                markets="\n".join(
                    "|{:>2d}| {:<{max_source}} | {:<9} | {:>10.2f}$ | {:>7.3f}$ | {:>6.2f}% |".format(
                        i + 1,
                        markets[i]["source"],
                        markets[i]["pair"],
                        markets[i]["volume_24h"],
                        markets[i]["price"],
                        markets[i]["vol_percent"],
                        max_source=max_source,
                    )
                    for i in range(len(markets))
                ),
            )
    # -------- <halving> --------
    elif cmd == "halving":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["blocks_info"]) as blocks_info:
                if blocks_info.status == 200:
                    blocks_api = await blocks_info.json()
                else:
                    print(f"{data['blocks_info']} is down")
        avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        halving_time = (2102400 - last_block) * avg_bt / 86400
        message = (
            f"The next halving will be in approximately **{halving_time:1.2f}** days (**{halving_time/365:1.3f}"
            + f"** years).\nThe block reward after the halving will be **10** {TICKER}."
        )
    # -------- <fork> --------
    elif cmd == "fork":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["blocks_info"]) as blocks_info:
                if blocks_info.status == 200:
                    blocks_api = await blocks_info.json()
                else:
                    print(f"{data['blocks_info']} is down")
        avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        fork = params["fork"]
        fork_block = params["fork_block"]
        version = params["daemon_ver"]
        if fork_block <= last_block:
            message = "There is not any known planned fork. We are good :heart_eyes:"
        else:
            fork_time = (fork_block - last_block) * avg_bt / 3600
            if fork:
                message = (
                    f"The next planned fork is at block **{fork_block:1,.0f}** so all nodes must be updated "
                    + f"to **ver.{version}**.\nThis is approximately in **"
                    + f"{fork_time:1.2f}** hours (**{fork_time/24:1.3f}** days)."
                )
            else:
                message = (
                    f"There is no planned fork but nodes must be updated to **ver.{version}** till block **"
                    + f"{fork_block:1,.0f}**.\nThis is approximately in **"
                    + f"{fork_time:1.2f}** hours (**{fork_time/24:1.3f}** days)."
                )
    # -------- <coin/coininfo> --------
    elif cmd == "coin" or cmd == "coininfo":
        async with aiohttp.ClientSession() as session:
            async with session.get(data["masternodes"]["link"]) as masternodes:
                if masternodes.status == 200:
                    mn_raw = await masternodes.text()
                else:
                    print(f"{data['masternodes']['link']} is down")
        mn_count = mn_raw.count("ENABLED")
        if mn_count == 0:
            mn_count = params["mn_count"]
        locked_coins = mn_count * 10000
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_tent"], headers=HEADERS) as cmc_tent:
                if cmc_tent.status == 200:
                    cmc_tent_api = await cmc_tent.json()
                    tent_usd_price = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["price"])
                    tent_24vol = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["volume_24h"])
                    tent_24change = float(cmc_tent_api["data"]["TENT"]["quote"]["USD"]["percent_change_24h"])
                else:
                    print(f"{data['cmc']['cmc_tent']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["cmc"]["cmc_btc"], headers=HEADERS) as cmc_btc:
                if cmc_btc.status == 200:
                    cmc_btc_api = await cmc_btc.json()
                    btc_usd_price = float(cmc_btc_api["data"]["BTC"]["quote"]["USD"]["price"])
                else:
                    print(f"{data['cmc']['cmc_btc']} is down")
        async with aiohttp.ClientSession() as session:
            async with session.get(data["blocks_info"]) as blocks_info:
                if blocks_info.status == 200:
                    blocks_api = await blocks_info.json()
                    last_block = blocks_api["blocks"][0]["height"]
                    tent_circ_supply = calculate_supply(last_block)
                    tent_mcap = tent_circ_supply * tent_usd_price
                else:
                    print(f"{data['blocks_info']} is down")
        locked_proc = locked_coins / tent_circ_supply * 100
        message = (
            f"• Current Price • **{tent_usd_price/btc_usd_price:1.8f} BTC ** | **{tent_usd_price:1.4f}$**\n• 24h Volume •"
            + f" **{tent_24vol/btc_usd_price:1.3f} BTC ** | **{tent_24vol:1,.2f}$**\n• Market Cap • **{tent_mcap:1,.0f}$**"
            + f"\n• Circulating Supply • **{tent_circ_supply:1,.0f} {TICKER} **\n• Total Supply • **"
            + f"84,096,000 {TICKER} **\n• Locked Coins • **{locked_coins:,} {TICKER} ({locked_proc:.2f}%)**\n• 24h Change • **"
            + f"{tent_24change:1.2f} % **"
        )
    # -------- <about> --------
    elif cmd == "about":
        message = "\n".join(data["about"])
    # -------- <whenmoon> --------
    elif cmd == "whenmoon":
        message = random.choice(data["whenmoon"])
    # -------- <team> --------
    elif cmd == "team":
        message_list = ["TENT team members with local time and the languages they support:"]
        for i in range(len(data["team"])):
            tz = pytz.timezone(data["team"][i]["time"])
            local_hour = datetime.now(tz).strftime("%H:%M")
            member_name = data["team"][i]["name"]
            covered_language = data["team"][i]["language"]
            member = f"• {member_name} • {local_hour} - **{covered_language}**"
            message_list.append(member)
        message = "\n".join(message_list)
    # -------- <translators> --------
    elif cmd == "translators":
        message_list = [
            "This is our translation team. If you notice something is not right in a"
            + " translation please contact the person in charge:"
        ]
        for i in range(len(data["translators"])):
            member_name = data["translators"][i]["name"]
            covered_language = data["translators"][i]["language"]
            member = f"• **{covered_language}** • {member_name}"
            message_list.append(member)
        message = "\n".join(message_list)
    # -------- <joingames> --------
    elif cmd == "joingames" and isinstance(msg.channel, discord.TextChannel):
        if "Player" not in [role.name for role in msg.author.guild.roles]:
            message = f"{data['no_role']}"
        elif "Player" in [role.name for role in msg.author.roles]:
            return
        else:
            role = discord.utils.get(msg.author.guild.roles, name="Player")
            await msg.author.add_roles(role)
            emoji = discord.utils.get(msg.author.guild.emojis, name="heimdall")
            if emoji:
                await msg.add_reaction(emoji)
            else:
                message = "Server do not have :heimdall: emoji."
                await msg.channel.send(message)
            return
    # -------- <leavegames> --------
    elif cmd == "leavegames" and isinstance(msg.channel, discord.TextChannel):
        if "Player" not in [role.name for role in msg.author.roles]:
            return
        else:
            role = discord.utils.get(msg.author.guild.roles, name="Player")
            await msg.author.remove_roles(role)
            emoji = discord.utils.get(msg.author.guild.emojis, name="heimdall")
            if emoji:
                await msg.add_reaction(emoji)
            else:
                message = "Server do not have :heimdall: emoji."
                await msg.channel.send(message)
            return
    # -------- <members(CoreTeam only)> --------
    elif (
        cmd == "members"
        and isinstance(msg.channel, discord.TextChannel)
        and "CoreTeam" in [role.name for role in msg.author.roles]
    ):
        members = msg.author.guild.member_count
        message = f"Current number of members: {members}"
    # -------- <ban(CoreTeam only)> --------
    elif (
        cmd == "ban"
        and isinstance(msg.channel, discord.TextChannel)
        and "CoreTeam" in [role.name for role in msg.author.roles]
    ):
        if len(args) < 2:
            message = (
                f"Input a substring of users to ban, like `!ban TENT` will ban all users containing"
                + f" `TENT` in their names (_fuction is case-sensitive_)."
            )
            await msg.channel.send(message)
            return
        cmd1 = args[1]
        member = discord.utils.find(lambda m: cmd1 in m.name, msg.channel.guild.members)
        if member is None:
            count = 0
        else:
            count = 1
        while not (member is None):
            await msg.channel.guild.ban(member)
            member = discord.utils.find(lambda m: cmd1 in m.name, msg.channel.guild.members)
            if not (member is None):
                count += 1
        message = f"Banned {count} members! Nice!"
    # -------- <del(Amitabha only)> --------
    elif (
        cmd == "del"
        and isinstance(msg.channel, discord.TextChannel)
        and msg.author.id == 359782573066551320
    ):
        if len(args) < 2:
            message = "Enter the number of messages to delete"
            await msg.channel.send(message)
            return
        cmd1 = args[1]
        deleted = await msg.channel.purge(limit=int(cmd1))
        message = f"Deleted {len(deleted)} message(s)"

    else:
        message = f"{data['unknown']}"

    await msg.channel.send(message)


@client.event
async def on_raw_reaction_add(payload):
    guild = client.get_guild(398513312696107008)
    role = guild.get_role(693175238720094318)
    mbr = guild.get_member(payload.user_id)

    if (payload.message_id == 764746968516919307 and payload.emoji.name == "xsg"):
        await mbr.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    guild = client.get_guild(398513312696107008)
    role = guild.get_role(693175238720094318)
    mbr = guild.get_member(payload.user_id)

    if (payload.message_id == 764746968516919307 and payload.emoji.name == "xsg"):
        await mbr.remove_roles(role)


@client.event
async def on_member_join(mbr):
    for ban_word in data["banned_words"]:
        if mbr.guild.get_member(mbr.id) is not None and ban_word in mbr.name:
            await mbr.ban()
            logging.warning(f'Banned {mbr.name} with id: {mbr.id}')
            return
    message = f"{data['welcome']}"
    await mbr.send(message)


@client.event
async def on_member_update(before, after):
    # Bot ignore all members that have MEMBER_ID in ignored_ids list
    if after.id in data["ignored_ids"]:
        return
    for ban_word in data["banned_words"]:
        if after.guild.get_member(after.id) is not None and ban_word in after.name:
            await after.ban()
            logging.warning(f'Banned {after.name} with id: {after.id}')
            return


@client.event
async def on_ready():
    print(f"Logged in as: {client.user.name} {{{client.user.id}}}")

client.loop.create_task(price_update_channel())
client.loop.create_task(report_not_reporting())
client.run(TOKEN)
logging.info('----- Finished -----')
