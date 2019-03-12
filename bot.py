#!/usr/bin/env python3.6
# Work with Python 3.6

import ftplib
import json
import random

import discord
from aiohttp import get
from discord.ext.commands import Bot

with open("auth.json") as data_file:
    auth = json.load(data_file)
with open("links.json") as data_file:
    data = json.load(data_file)

TOKEN = auth["token"]
HEADERS = {}
HEADERS["X-CMC_PRO_API_KEY"] = auth["cmc_headers"]
BOT_PREFIX = "!"
SERVER_ADDRESS = auth["ftp_addr"]
USERNAME = auth["ftp_user"]
PASSWORD = auth["ftp_pass"]

client = Bot(BOT_PREFIX)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def send_file(server_adress, username, password, message):
    session = ftplib.FTP(server_adress, username, password)
    file = open("announcements.txt", "a")
    file.write(message)
    file.close()
    file = open("announcements.txt", "rb")
    session.storbinary("STOR /web/snowbot/announcements.txt", file)
    file.close()
    session.quit()


@client.event
async def on_message(msg):
    # We do not want the bot to respond to Bots or Webhooks
    if msg.author.bot:
        return
    # Bot will save all the messages in #announcements channel into a text file
    if msg.content and msg.channel.id == "398660597505458187":
        message = f"Ann: {msg.content}\n"
        send_file(SERVER_ADDRESS, USERNAME, PASSWORD, message)
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

    # Bot responds to mee6 commands if in unaccepted channel
    if not msg.channel.name == "bot-commands" and (cmd == "help" or cmd == "rank" or cmd == "levels"):
        message = f"{data['mee6']}"
        await client.send_message(msg.channel, message)
        return
    # Bot runs in #bot-commands channel and private channels for everyone
    # Bot runs in all channels for specific roles
    if not (
        msg.channel.name == "bot-commands"
        or msg.channel.type == discord.ChannelType.private
        or "CoreTeam" in [role.name for role in msg.author.roles]
        or "Moderator" in [role.name for role in msg.author.roles]
        or "Adviser" in [role.name for role in msg.author.roles]
    ):
        message = f"{data['default']}"
        await client.send_message(msg.channel, message)
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
        async with get(data["blocks_info"]) as blocks_info:
            if blocks_info.status == 200:
                blocks_api = await blocks_info.json()
            else:
                print(f"{data['blocks_info']} is down")
        now = blocks_api["blocks"][0]["time"]
        if len(blocks_api["blocks"]) > 1:
            max_blocks = len(blocks_api["blocks"]) - 1
            before = blocks_api["blocks"][max_blocks]["time"]
            avg_bt = (now - before) / max_blocks
        else:
            avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        async with get(data["difficulty"]) as difficulty:
            if difficulty.status == 200:
                difficulty_api = await difficulty.json()
            else:
                print(f"{data['difficulty']} is down")
        diff = difficulty_api["difficulty"]
        async with get(data["net_hash"]) as net_hash:
            if net_hash.status == 200:
                net_hash_api = await net_hash.json()
            else:
                print(f"{data['net_hash']} is down")
        hashrate = net_hash_api["info"]["networksolps"]
        message = (
            f"• Block Height• **{last_block:,}**\n• Avg Block Time• **{round(avg_bt, 2)} s**\n• Network Hashrate• **"
            + f"{int(hashrate)/1000} kSol/s**\n• Network Difficulty• **{diff:1.3f}**"
        )
    # -------- <mn/mninfo> --------
    elif cmd == "mn" or cmd == "mninfo":
        async with get(data["blocks_info"]) as blocks_info:
            if blocks_info.status == 200:
                blocks_api = await blocks_info.json()
            else:
                print(f"{data['blocks_info']} is down")
        now = blocks_api["blocks"][0]["time"]
        if len(blocks_api["blocks"]) > 1:
            max_blocks = len(blocks_api["blocks"]) - 1
            before = blocks_api["blocks"][max_blocks]["time"]
            avg_bt = (now - before) / max_blocks
        else:
            avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        async with get(data["masternodes"]["link"]) as masternodes:
            if masternodes.status == 200:
                mn_raw = await masternodes.text()
            else:
                print(f"{data['masternodes']['link']} is down")
        mn_count = mn_raw.count("ENABLED")
        guide_link = data["masternodes"]["guide_link"]
        asgard = data["masternodes"]["asgard"]
        mn_roi = 9 * 3153600 / avg_bt / mn_count / 10
        time_first_payment = 2.6 * mn_count / 60
        message = (
            f"• Active masternodes • ** {mn_count: 1.0f} **\n• Coins Locked: **{mn_count*10000:,} XSG**\n• ROI "
            + f"• ** {mn_roi: 1.3f} % **\n• Minimum time before first payment • ** {time_first_payment: 1.2f} hours **"
            + f"\n{asgard}\n{guide_link}"
        )
    # -------- <hpow/calc> --------
    elif cmd == "hpow" or cmd == "calc":
        async with get(data["blocks_info"]) as blocks_info:
            if blocks_info.status == 200:
                blocks_api = await blocks_info.json()
            else:
                print(f"{data['blocks_info']} is down")
        now = blocks_api["blocks"][0]["time"]
        if len(blocks_api["blocks"]) > 1:
            max_blocks = len(blocks_api["blocks"]) - 1
            before = blocks_api["blocks"][max_blocks]["time"]
            avg_bt = (now - before) / max_blocks
        else:
            avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        async with get(data["cmc"]["cmc_xsg"], headers=HEADERS) as cmc_xsg:
            if cmc_xsg.status == 200:
                cmc_xsg_api = await cmc_xsg.json()
                xsg_usd_price = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["price"])
            else:
                print(f"{data['cmc']['cmc_xsg']} is down")
        async with get(data["difficulty"]) as difficulty:
            if difficulty.status == 200:
                difficulty_api = await difficulty.json()
            else:
                print(f"{data['difficulty']} is down")
        diff = difficulty_api["difficulty"]
        async with get(data["net_hash"]) as net_hash:
            if net_hash.status == 200:
                net_hash_api = await net_hash.json()
            else:
                print(f"{data['net_hash']} is down")
        hashrate = net_hash_api["info"]["networksolps"]
        if len(args) < 2:
            message = f"{data['hpow']['default']}"
            await client.send_message(msg.channel, message)
            return
        cmd1 = args[1].lower()
        if not is_number(cmd1):
            message = f"{data['hpow']['default']}"
        elif cmd1 == "0":
            message = f"{data['hpow']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['hpow']['neg']}"
        elif is_number(cmd1):
            mnr_rwd = 9.5
            cmd1 = float(cmd1)
            message = (
                f"Current network hashrate is **{int(hashrate)/1000:1.2f} KSols/s**.\nA hashrate of **{cmd1:1.0f}"
                + f" Sols/s** will get you approximately **{cmd1/hashrate*3600*mnr_rwd/avg_bt:1.2f} XSG** _(***"
                + f"{cmd1/hashrate*3600*mnr_rwd/avg_bt*xsg_usd_price:1.2f}$***)_ per **hour** and **"
                + f"{cmd1/hashrate*3600*mnr_rwd*24/avg_bt:1.2f} XSG** _(***"
                + f"{cmd1/hashrate*3600*mnr_rwd*24/avg_bt*xsg_usd_price:1.2f}$***)_ per **day** at current "
                + "network difficulty."
            )
    # -------- <mnrew/mnrewards> --------
    elif cmd == "mnrew" or cmd == "mnrewards":
        async with get(data["blocks_info"]) as blocks_info:
            if blocks_info.status == 200:
                blocks_api = await blocks_info.json()
            else:
                print(f"{data['blocks_info']} is down")
        now = blocks_api["blocks"][0]["time"]
        if len(blocks_api["blocks"]) > 1:
            max_blocks = len(blocks_api["blocks"]) - 1
            before = blocks_api["blocks"][max_blocks]["time"]
            avg_bt = (now - before) / max_blocks
        else:
            avg_bt = 60
        last_block = blocks_api["blocks"][0]["height"]
        async with get(data["cmc"]["cmc_xsg"], headers=HEADERS) as cmc_xsg:
            if cmc_xsg.status == 200:
                cmc_xsg_api = await cmc_xsg.json()
                xsg_usd_price = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["price"])
            else:
                print(f"{data['cmc']['cmc_xsg']} is down")
        async with get(data["masternodes"]["link"]) as masternodes:
            if masternodes.status == 200:
                mn_raw = await masternodes.text()
            else:
                print(f"{data['masternodes']['link']} is down")
        mn_count = mn_raw.count("ENABLED")
        mn_rwd = 9
        if len(args) < 2:
            message = (
                f"**1** Masternode will give you approximately **{3600*24/avg_bt*mn_rwd/mn_count:1.3f} XSG** _(***"
                + f"{3600*24/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$***)_ per **day**."
            )
            await client.send_message(msg.channel, message)
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
                f"**{cmd1:1.0f}** Masternode will give you approximately **{cmd1*3600*24/avg_bt*mn_rwd/mn_count:1.3f}"
                + f" XSG** _(***{cmd1*3600*24/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$***)_ per **day**."
            )
    # -------- <xsgusd> --------
    elif cmd == "xsgusd":
        async with get(data["cmc"]["cmc_xsg"], headers=HEADERS) as cmc_xsg:
            if cmc_xsg.status == 200:
                cmc_xsg_api = await cmc_xsg.json()
                xsg_usd_price = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["price"])
            else:
                print(f"{data['cmc']['cmc_xsg']} is down")
        if len(args) < 2:
            message = f"{data['xsgusd']['default']}{round(xsg_usd_price, 3)}$***._"
            await client.send_message(msg.channel, message)
            return
        cmd1 = args[1].lower()
        if not is_number(cmd1):
            message = f"{data['xsgusd']['default']}{round(xsg_usd_price, 3)}$***._"
        elif cmd1 == "0":
            message = f"{data['xsgusd']['zero']}"
        elif is_number(cmd1) and float(cmd1) < 0:
            message = f"{data['xsgusd']['neg']}"
        elif is_number(cmd1):
            message = (
                f"**{round(float(cmd1),2):,} XSG** = **{round(float(xsg_usd_price)*float(cmd1),2):,}$**\n"
                + f"{data['xsgusd']['default']}{round(xsg_usd_price, 3)}$***_"
            )
    # -------- <roadmap> --------
    elif cmd == "roadmap":
        message = f"{data['roadmap']}"
    # -------- <proof of review> --------
    elif cmd == "por":
        message = f"{data['por']}"
    # -------- <coin/coininfo> --------
    elif cmd == "coin" or cmd == "coininfo":
        async with get(data["masternodes"]["link"]) as masternodes:
            if masternodes.status == 200:
                mn_raw = await masternodes.text()
            else:
                print(f"{data['masternodes']['link']} is down")
        mn_count = mn_raw.count("ENABLED")
        async with get(data["cmc"]["cmc_xsg"], headers=HEADERS) as cmc_xsg:
            if cmc_xsg.status == 200:
                cmc_xsg_api = await cmc_xsg.json()
                xsg_usd_price = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["price"])
                xsg_24vol = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["volume_24h"])
                xsg_mcap = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["market_cap"])
                xsg_circ_supply = float(cmc_xsg_api["data"]["XSG"]["circulating_supply"])
                xsg_24change = float(cmc_xsg_api["data"]["XSG"]["quote"]["USD"]["percent_change_24h"])
            else:
                print(f"{data['cmc']['cmc_xsg']} is down")
        async with get(data["cmc"]["cmc_btc"], headers=HEADERS) as cmc_btc:
            if cmc_btc.status == 200:
                cmc_btc_api = await cmc_btc.json()
                btc_usd_price = float(cmc_btc_api["data"]["BTC"]["quote"]["USD"]["price"])
            else:
                print(f"{data['cmc']['cmc_btc']} is down")
        message = (
            f"• Current Price•**{xsg_usd_price/btc_usd_price:22.8f} BTC ** | **{xsg_usd_price:8.4f}$**\n• 24h Volume •"
            + f"**{xsg_24vol/btc_usd_price:19.3f} BTC ** | **{xsg_24vol:10,.2f}$**\n• Market Cap•**{xsg_mcap:22,.0f}$**"
            + f"\n• Circulating Supply• **{xsg_circ_supply:12,.0f} XSG **\n• Locked Coins•            **"
            + f"{mn_count*10000:,} XSG **\n• 24h Change•**{xsg_24change:19.2f} % **"
        )
    # -------- <about> --------
    elif cmd == "about":
        message = "\n".join(data["about"])
    # -------- <whenmoon> --------
    elif cmd == "whenmoon":
        message = random.choice(data["whenmoon"])
    # -------- <members(CoreTeam only)> --------
    elif (
        cmd == "members"
        and msg.channel.type != discord.ChannelType.private
        and "CoreTeam" in [role.name for role in msg.author.roles]
    ):
        members = msg.author.server.member_count
        message = f"Current number of members: {members}"

    else:
        message = f"{data['unknown']}"

    await client.send_message(msg.channel, message)


@client.event
async def on_member_join(mbr):
    message = f"{data['welcome']}"
    await client.send_message(mbr, message)


@client.event
async def on_ready():
    print(f"Logged in as: {client.user.name} {{{client.user.id}}}")


client.run(TOKEN)
