import discord
import json
import asyncio
import requests
import time
import threading
import socket
import pickle

from config import config
from Tools import getPoints

client = discord.Client()

global users
try:
    users = json.load(open("points.json"))
except:
    print("COULDNT LOAD USERSAVE.JSON!!!\n"*10)
    users = {}


try:
    showStock = json.load(open("showStock.json"))
except:
    showStock = {
        "Loco": 0
        }

def createusers():
    for member in client.get_all_members():
        if not member.id in users:
            users[member.id] = {
                "points": 0,
                "statistics": {
                    "lives": {
                        "Loco": 0
                        },
                    "commands": 0,
                    "payments": {
                        "payments": 0,
                        "points": 0
                        }
                    }
                }


def saveusers():
    json.dump(users, open("points.json", "w+"))
    

@client.event
async def on_ready():
    print("Connected as "+client.user.name)
    createusers()




@client.event
async def on_message(message):
    global users
    msg = message.content[1:].split()
    channel = message.channel
    author = message.author

    isAdmin = author.id in ("453245427542786058", "257606762998267905")

    if message.content.startswith(config["botPrefix"]):

        user = users[author.id]
        botchannel = client.get_channel("530844309470052358")
        lifebot = botchannel.server.get_member("447716887225171988")
        logchannel = client.get_channel("530846733224116224")
        lifelogchannel = client.get_channel("530846892481970179")

        if msg[0] == "loco":
            if getPoints(client) <= 0:
                await client.send_message(channel, "Sorry, the stock is empty :frowning:")
                return
            
            user["statistics"]["commands"] += 1
            if len(msg) < 2:
                await client.send_message(channel, "Usage: ``%s%s referral1 referral2 <amount>``"%(config["botPrefix"], msg[0]))
                return
            
            if user["points"] <= 0:
                await client.send_message(channel, "Sorry, you have no points left!")
                return
            
            if msg[-1].isdigit():
                amount = int(msg[-1])
                referrals = msg[1:-1]
            else:
                amount = 1
                referrals = msg[1:]

            pointsneeded = len(referrals)*amount
            if user["points"]-pointsneeded < 0:
                await client.send_message(channel, "Sorry, you don't have enough points!")
                return

            user["points"] -= pointsneeded
            generatingmsg = await client.send_message(channel, "Generating %s lives for %s..."%(amount, ", ".join(referrals)))
            commandmsg = await client.send_message(botchannel, "+loco %s %s"%(amount, ", ".join(referrals)))

            botresponse = await client.wait_for_message(channel=botchannel, author=lifebot)
            while True:
                await asyncio.sleep(1)
                botresponse = await client.get_message(botchannel, botresponse.id)
                print(botresponse.content)
                if "doesn't exist" in botresponse.content:
                    user["points"] += pointsneeded
                    await client.edit_message(generatingmsg, botresponse.content)
                    break

                elif "Generated" in botresponse.content:
                    await client.edit_message(generatingmsg, "Generated %s lives for %s!"%(amount, ", ".join(referrals)))
                    break

            saveusers()


        elif msg[0] in ("credits", "points", "point", "credit"):
            await client.send_message(channel, "You have **%s point%s** left!"%(
                user["points"],
                "" if user["points"] in (1, -1) else "s"
                ))


##        elif msg[0] == "setstock" and isAdmin:
##            msg[1] = msg[1].lower()
##            if msg[1] == "loco":
##                if msg[2].isdigit():
##                    showStock["Loco"] = int(msg[2])
##                elif msg[2].lower() == "bot":
##                    showStock["Loco"] = "bot"
##                await client.send_message(channel, "Changed!")
##                json.dump(showStock, open("showStock.json", "w+"))



        elif msg[0] == "add" and isAdmin:
            userid = "".join([x for x in msg[1] if x.isdigit()])
            users[userid]["points"] += int(msg[2])
            await client.send_message(channel, "Added %s poins to <@%s>!"%(
                msg[2],
                userid
                ))
            saveusers()



        elif msg[0] == "say" and isAdmin:
            text = message.content[5:]
            if msg[-1].startswith("<#"):
                channelid = "".join([x for x in msg[-1] if x.isdigit()])
                text = text[:-len(channelid)-4]
                channel = client.get_channel(channelid)
            await client.send_message(channel, text)



        elif msg[0] == "stock":
            await client.send_message(
                channel,
                """**Lives stock:**
■ Loco: %s"""%(
    int(getPoints(client)*4)
    )
                )


        elif msg[0] in ("buy", "purchase", "pay"):
            await client.send_message(author, "Hello %s,\nthank you for using this command!\nHow much points would you like to purchase?"%author.name)
            await client.send_message(channel, "**Okay, I sent you a DM {}!**".format(author.mention))

            channel = await client.start_private_message(author)
            amount = None
            while not amount:
                message = await client.wait_for_message(author=author)
                content = message.content.lower()
                if content.startswith(".buy"):
                    return

                if message.channel == channel:
                    if content.isdigit() and int(content):
                        amount = int(content)
                        price = amount*2

                        await client.send_message(author, "The price will be ₹%s. Is that okay?"%price)
                        message = await client.wait_for_message(author=author)
                        content = message.content.lower()
                        if content.startswith(".buy"):
                            return

                        if message.channel == channel:
                            if not "y" in content:
                                amount = None
                                await client.send_message(author, "Okay, how much points do you need?")
                    else:
                        await client.send_message(author, "This is not a valid amount of points! How much points do you want?")


            await client.send_message(author, "To confirm your payment, I need to know your PayTM phone number that I know it's you. Please type in your PayTM phone number. For example:\n1234567890\nor\n12XXXX7890")

            phonenumber = None
            while not phonenumber:
                message = await client.wait_for_message(author=author)
                content = message.content.lower()
                if content.startswith(".buy"):
                    return

                if message.channel == channel:
                    if content.startswith("+91"):
                        content = content[3:]
                    num = content[:2]+content[6:]
                    if num.isdigit() and len(num) > 4:
                        phonenumber = content
                    else:
                        await client.send_message(author, "This is not a valid phone number! Please type it again!")

            waitmessage = await client.send_message(author, "Creating your payment...")

            
            payment = requests.post(
                "http://188.68.36.239:52050/paytm/create",
                json={
                    "amount": price,
                    "number": phonenumber
                    },
                headers={"authorization": "453245427542786058|datriviagoooiithatplaysloco9832hfn"}
                ).json()
                
            if "paymentId" in payment:
                users[author.id]["payment"] = {
                    "amount": amount,
                    "toPay": price,
                    "number": phonenumber,
                    "created": time.time(),
                    "paymentId": payment["paymentId"]
                    }

            else:
                await client.edit_message(
                    waitmessage,
                    "Oh no, something went wrong!"
                    )
                return

            await client.edit_message(
                waitmessage,
                "**Please send ₹%s using the following QR code:**\n%s"%(
                    price,
                    payment["QRCode"]
                    )
                )

            await client.send_message(
                logchannel,
                "Created payment for <@%s> (%s#%s, %s): %s"%(
                    author.id,
                    author.name,
                    author.discriminator,
                    author.id,
                    users[author.id]["payment"]
                    )
                )
            saveusers()



def payment_handling():
    global users
    while not client.is_logged_in:
        time.sleep(10)

    logchannel = client.get_channel("530846733224116224")
    while True:
        for i in users:
            userId = i
            user = users[userId]
            if user.get("payment"):
                if user["payment"]["created"]+86400 < time.time():
                    del user["payment"]
                    continue
                
                response = requests.get(
                    "http://188.68.36.239:52050/paytm/check",
                    json={
                        "paymentId": user["payment"]["paymentId"]
                        },
                    headers={"authorization": "453245427542786058|datriviagoooiithatplaysloco9832hfn"}
                    ).json()

                if response.get("paid"):
                    member = None
                    for server in client.servers:
                        for m in server.members:
                            if m.id == userId:
                                member = m
                                break

                        if member:
                            break


                    amount = user["payment"]["amount"]
                    paymentDiscount = user["payment"].get("discount", 0)
                    del user["payment"]
                    user["points"] += amount

                    saveusers()
                    
                    asyncio.run_coroutine_threadsafe(
                        client.send_message(
                            m,
                            "You just got your %s points!"%amount
                            ),
                        client.loop
                        )
                    asyncio.run_coroutine_threadsafe(
                        client.send_message(
                            logchannel,
                            "<@%s> (%s#%s, %s) got **%s points** with %s discount through payment!"%(
                                m.id,
                                m.name,
                                m.discriminator,
                                m.id,
                                amount,
                                str(paymentDiscount)+"%"
                                )
                            ),
                        client.loop
                        )


        time.sleep(10)
        if not client.is_logged_in:
            return




@client.event
async def on_member_join(member):
    createusers()

@client.event
async def on_server_join(server):
    createusers()



def payment_handling_keepAlive():
    while True:
        print("starting", payment_handling)
        t = threading.Thread(target=payment_handling)
        t.start()
        t.join()
    

threading.Thread(target=payment_handling_keepAlive).start()

client.run(config["botToken"])
