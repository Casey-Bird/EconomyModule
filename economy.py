import discord
import discord.utils
import asyncio
import mysql.connector
import os
import random
import json
import time
import re
from discord_components import DiscordComponents, Interaction, Button, ButtonStyle, Select, SelectOption

from discord.ext import commands

earned_w_skill = 1
buy_tax = 1.03
buy_tax_percent = "3%"
sell_tax = 1
sell_tax_percent = "0%"
test_cooldown = []

# This file can't be copy-pasted as I had to remove some lines of code.

class EconomyModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    
    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Balance/Profile Creation & Management
    @commands.command(aliases=['bal', 'bank', 'wallet', 'profile', 'wal', 'prof'])
    async def _balance(self, ctx):
        # Initialization data
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        title, t_color = await get_title(self, user, ctx, database)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Display balance creation
        profile_button = Button(style = ButtonStyle.blue, label = "Profile", custom_id = "profile")
        skills_button = Button(style = ButtonStyle.blue, label = "Skills", custom_id = "skills")
        title_button = Button(style = ButtonStyle.blue, label = "Title", custom_id = "title")
        back_button = Button(style = ButtonStyle.gray, label = "Back", custom_id = "back_button")

        title_select = await get_title_options(user, database)

        skills_select = Select(placeholder = "Select Skill Tree", 
        options = [
            SelectOption(label = "Doctor", value = "doctor"),
            SelectOption(label = "Police", value = "police"),
            SelectOption(label = "Marine Biologist", value = "biologist"),
            SelectOption(label = "Mechanic", value = "mechanic"),
            SelectOption(label = "Journalist", value = "journalist")
            ])

        balance_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Profile", description = f'{title}', color = t_color)
        balance_embed.add_field(name = 'Wallet', value = f'{self.bot.get_emoji(877620442712653824)} {bank_data[0]:,}', inline = False)
        balance_embed.add_field(name = 'Bank', value = f'{self.bot.get_emoji(877620442712653824)} {bank_data[1]:,}', inline = False)
        balance_embed.set_thumbnail(url = f'{ctx.message.author.avatar_url}')
        await check_status(ctx, balance_embed, status_list, stats_data)

        def check(interaction):
            if ctx.author == interaction.user:
                return True
            else:
                return False

        message = await ctx.send(
            embed = balance_embed,
            components = [
                [skills_button, title_button]
            ]
        )
        
        while True:
            try:
                interaction = await self.bot.wait_for("button_click", check = check, timeout = 30)
                selection = interaction.component.label
                
                if selection == "Profile":
                    await message.edit(
                        embed = balance_embed,
                        components = [
                            [skills_button, title_button]
                        ]
                        )
                
                if selection == "Title":
                    while True:
                        title_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Title", description = f"{title}", color = t_color)
                        title_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        await message.edit(
                            embed = title_embed,
                            components = [title_select]
                            )
                        await interaction.respond(type=6)
                        
                        try:
                            title_interaction = await self.bot.wait_for("select_option", timeout = 15)
                            title_selection = title_interaction.values[0]

                            await try_title_change(self, ctx, user, database, title_selection)
                            
                            title, t_color = await get_title(self, user, ctx, database)
                            await message.edit(embed = title_embed, components = [[title_select],[profile_button, skills_button]])
                            await title_interaction.respond(type=6)

                        except asyncio.TimeoutError:
                            await message.edit(
                                embed = balance_embed,
                                components = []
                                )
                            await interaction.respond(type=6)
                            break
                
                if selection == "Skills":
                    while True:
                        user_tree = await get_user_tree(database, user)

                        s_selection, s_amount, s_title = await get_skill_data(user, database)
                        skills_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Skill", description = f"{title}", color = t_color)
                        skills_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        skills_embed.add_field(name = f"{s_selection}", value = f"**({s_title})\n({s_amount})**", inline = False)
                    
                        await message.edit(
                            embed = skills_embed,
                            components = [
                                [skills_select]
                            ]
                            )
                        await interaction.respond(type=6)

                        try:
                            skills_interaction = await self.bot.wait_for("select_option", timeout = 15)
                            skills_selection = skills_interaction.values[0]

                            if skills_selection == "mechanic":
                                await change_job(user, database, "Doctor")
                                await message.edit(embed = skills_embed, components = [[title_select],[profile_button, skills_button]])
                                await skills_interaction.respond(type=6)

                            if skills_selection == "police":
                                await change_job(user, database, "Police")
                                await message.edit(embed = skills_embed, components = [[title_select],[profile_button, skills_button]])
                                await skills_interaction.respond(type=6)

                            if skills_selection == "biologist":
                                await change_job(user, database, "Biologist")
                                await message.edit(embed = skills_embed, components = [[title_select],[profile_button, skills_button]])
                                await skills_interaction.respond(type=6)

                            if skills_selection == "mechanic":
                                await change_job(user, database, "Mechanic")
                                await message.edit(embed = skills_embed, components = [[title_select],[profile_button, skills_button]])
                                await skills_interaction.respond(type=6)

                            if skills_selection == "journalist":
                                await change_job(user, database, "Journalist")
                                await message.edit(embed = skills_embed, components = [[title_select],[profile_button, skills_button]])
                                await skills_interaction.respond(type=6)


                        except asyncio.TimeoutError:
                            await message.edit(
                                embed = balance_embed,
                                components = []
                                )
                            await interaction.respond(type=6)
                            break

            
            except asyncio.TimeoutError:
                await message.edit(
                    embed = balance_embed,
                    components = []
                    )
                break

    @commands.command(aliases=['dep', 'deposit'])
    async def _deposit(self, ctx, amount = None):
        # Initialization data
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Status handler / main code block
        await apply_status(user, database, ctx, status_list)
        
        if "Stunned" in status_list:
            pass
        else: # Not stunned
            
            if amount == None:
                await ctx.send("None amount selected")
            if amount == "all":
                max_deposit = bank_data[0]
                await update_money(user, database, 'wallet', -max_deposit)
                await update_money(user, database, 'bank', max_deposit)
                
                deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Deposit", description = f'{self.bot.get_emoji(877620442712653824)} {max_deposit:,} was deposited into your bank.', color = discord.Color.green())
                deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                
                await ctx.send(embed = deposit_embed)
            else:
                max_deposit = bank_data[0]
                amount = int(amount)

                if amount <= max_deposit: # Deposit works
                    await update_money(user, database, 'wallet', -amount)
                    await update_money(user, database, 'bank', amount)
                    
                    deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Deposit", description = f'{self.bot.get_emoji(877620442712653824)} {amount:,} was deposited into your bank.', color = discord.Color.green())
                    deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                
                elif amount > max_deposit: # Amount was too much
                    
                    deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Deposit", description = f'You do not have that much to deposit!', color = discord.Color.green())
                    deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)   

                else:
                    pass
                
                await ctx.send(embed = deposit_embed)

    @commands.command(aliases=['with', 'withdraw'])
    async def _withdraw(self, ctx, amount = None):
        # Initialization data
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Status handler / main code block
        await apply_status(user, database, ctx, status_list)
        
        if "Stunned" in status_list:
            pass
        else: # Not stunned
            
            if amount == None:
                await ctx.send("None amount selected")
            if amount == "all":
                max_withdraw = bank_data[1]
                await update_money(user, database, 'bank', -max_withdraw)
                await update_money(user, database, 'wallet', max_withdraw)
                
                deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Withdraw", description = f'{self.bot.get_emoji(877620442712653824)} {max_withdraw:,} was withdrawn from your bank.', color = discord.Color.green())
                deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                
                await ctx.send(embed = deposit_embed)
            else:
                max_withdraw = bank_data[1]
                amount = int(amount)

                if amount <= max_withdraw: # Deposit works
                    await update_money(user, database, 'bank', -amount)
                    await update_money(user, database, 'wallet', amount)
                    
                    deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Withdraw", description = f'{self.bot.get_emoji(877620442712653824)} {amount:,} was withdrawn from your bank.', color = discord.Color.green())
                    deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                
                elif amount > max_withdraw: # Amount was too much
                    
                    deposit_embed = discord.Embed(title = f"{ctx.message.author.display_name}'s Withdraw", description = f'You do not have that much to withdraw!', color = discord.Color.green())
                    deposit_embed.set_thumbnail(url = ctx.message.author.avatar_url)   
                
                else:
                    pass
                
                await ctx.send(embed = deposit_embed)

    @commands.command(aliases=['add-money'])
    async def _add_money(self, ctx, member: discord.Member, amount):
        # Initialization data
        cuser = ctx.message.author.id
        user = member.id
        username = await self.bot.fetch_user(user)
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        admin_check = await check_botadmin(cuser, ctx)
        # # # # # # # # # # # # # # # # # # # # # # # # # #

        if admin_check == True:
            amount = int(amount)
            await update_money(user, database, 'bank', amount)

            await ctx.send(f"{member.mention}, you recieved {self.bot.get_emoji(877620442712653824)} {amount:,} gems!")

    @commands.command(aliases=['remove-money'])
    async def _remove_money(self, ctx, member: discord.Member, amount):
        # Initialization data
        cuser = ctx.message.author.id
        user = member.id
        username = await self.bot.fetch_user(user)
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        admin_check = await check_botadmin(cuser, ctx)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        
        if admin_check == True:
            amount = int(amount)
            await update_money(user, database, 'bank', -amount)

            await ctx.send(f"{member.mention}, you lost {self.bot.get_emoji(877620442712653824)} {amount:,} gems!")

    @commands.command(aliases=['kill']) # Todo
    async def _kill(self, ctx, member: discord.Member):
        # Initialization data
        cuser = ctx.message.author.id
        user = member.id
        username = await self.bot.fetch_user(user)
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        admin_check = await check_botadmin(cuser, ctx)
        # # # # # # # # # # # # # # # # # # # # # # # # # #

        if admin_check == True:
            pass

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Inventory Creation & Management
    @commands.command(aliases=['inv', 'inve', 'inven', 'invent', 'invento', 'inventor', 'inventory'])
    async def _inventory(self, ctx, member = None, page = 1):
        mentioned = ctx.message.mentions
        if len(mentioned) > 0:
            member = mentioned[0]
            user = member.id
            username = await self.bot.fetch_user(user)
        else:
            if member is not None:
                if int(member) > 1:     
                    page = member
            user = ctx.message.author.id
            username = ctx.message.author

        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        user_items = await get_user_inventory_list(user, database)
        items = await get_itemlist()
        title, t_color = await get_title(self, user, ctx, database)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        inventory_embed = discord.Embed(title = f"{username.display_name}'s Inventory", description = f"{title}", color = t_color)
        inventory_embed.set_thumbnail(url = username.avatar_url)
        
        if int(page) == 1:
            i = 0
            while i < 10:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1
        
        if int(page) == 2:
            i = 10
            while i < 20:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1

        if int(page) == 3:
            i = 20
            while i < 30:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1

        if int(page) == 4:
            i = 30
            while i < 40:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1

        if int(page) == 5:
            i = 40
            while i < 50:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1

        if int(page) == 6:
            i = 50
            while i < 60:
                try:
                    user_item = user_items[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]

                    item_amount = await fetch_item(user, database, user_item)

                    inventory_embed.add_field(name = f'{self.bot.get_emoji(emoji)} {item_name} ({item_amount}) {self.bot.get_emoji(rarity)}', value = f'{item_description}', inline = False)
                except:
                    pass

                i += 1

        await ctx.send(embed = inventory_embed)

    @commands.command(aliases = ['trade'])
    async def _trade(self, ctx, member: discord.Member, *args):
        user = ctx.message.author.id
        username = ctx.message.author
        member_user = member.id
        member_username = await self.bot.fetch_user(member_user)
        await create_economy(username, user)
        await create_economy(member_username, member_user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        user_items = await get_user_inventory_list(user, database)
        items = await get_itemlist()
        title, t_color = await get_title(self, user, ctx, database)
        m_title, m_t_color = await get_title(self, member_user, ctx, database)
        await apply_status(user, database, ctx, status_list)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        item1_quantity, item1_name, item2_quantity, item2_name = await dissect_for_trade(ctx, args)
        key1 = await get_item_key(item1_name)
        key2 = await get_item_key(item2_name)

        if key1 == "Failed":
            pass
        else:
            # (database, user1, user2, item1_quantity, item1_name, item2_quantity, item2_name)
            offer1, offer2 = await get_offer_info(database, user, member_user, item1_quantity, item1_name, item2_quantity, item2_name)

            if offer1 == "quantity_error":
                await ctx.send("Either you or they don't have enough of that item!")
            else:
                emoji1 = items[key1]["emoji"]
                i1_name = items[key1]["name"]
                i2_name = items[key2]["name"]
                emoji2 = items[key2]["emoji"]
                
                trade_embed = discord.Embed(title = f"{ctx.message.author.display_name} | **Trading** | {member.display_name}", description = f"{title}", color = t_color)
                trade_embed.add_field(name = f"{ctx.message.author.display_name} **Offer:**", value = f"{self.bot.get_emoji(emoji1)} {i1_name} - ({item1_quantity})", inline = False)
                trade_embed.add_field(name = f"{member_username.display_name} **For:**", value = f"{self.bot.get_emoji(emoji2)} {i2_name} - ({item2_quantity})", inline = False)


                def check(interaction):
                    if ctx.author == interaction.user:
                        return True
                    elif member_username == interaction.user:
                        return True
                    else:
                        return False
                
                accept_button = Button(style = ButtonStyle.green, label = "Accept", custom_id = "accept")
                decline_button = Button(style = ButtonStyle.red, label = "Decline", custom_id = "decline")
                cancel_button = Button(style = ButtonStyle.gray, label = "Cancel", custom_id = "cancel")
                
                message = await ctx.send(
                    embed = trade_embed,
                    components = [
                        [accept_button, decline_button, cancel_button]
                    ]
                )


                interaction = await self.bot.wait_for("button_click", check = check)
                
                try:
                    selection = interaction.component.label
                    
                    if selection == "Accept" and interaction.user == member_username:
                        accept_embed = discord.Embed(title = "Trade Accepted!", description = f'{member.display_name} accepted the trade!\n{m_title}', color = discord.Color.green())
                        accept_embed.set_thumbnail(url = member_username.avatar_url)
                        await message.edit(embed = accept_embed, components = [])
                        await interaction.respond(type=6)

                        await update_item(database, user, item2_quantity, key2, "add")
                        await update_item(database, member_user, item1_quantity, key1, "add")
                        await update_item(database, user, item1_quantity, key1, "remove")
                        await update_item(database, member_user, item2_quantity, key2, "remove")

                        log_channel = self.bot.get_channel(878943595955093505)
                        await log_channel.send(f"({user}, {username}) traded {item1_quantity} {item1_name} for {item2_quantity} {item2_name} to ({member_user}, {member_username})")

                    
                    if selection == "Decline":
                        decline_embed = discord.Embed(title = "Trade Declined!", description = "The trade was declined!", color = discord.Color.red())
                        await message.edit(embed = decline_embed)
                        await interaction.respond(type=6)
                    
                    if selection == "Cancel":
                        cancel_embed = discord.Embed(title = 'Canceled', description = 'The trade was canceled!', color = discord.Color.red())
                        await message.edit(embed = cancel_embed)
                        await interaction.respond(type=6)
                
                except TimeoutError:
                    timeout_embed = discord.Embed("Trade timed out!")
                    await message.edit(embed = timout_embed, components = [])
                
    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Jobs Management
    @commands.command(aliases = ['work', 'job'])
    async def _work(self, ctx):
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        title, t_color = await get_title(self, user, ctx, database)
        await apply_status(user, database, ctx, status_list)
        # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Skills page Name, Title, Current work title and skill points, image = skill tree image, 

        # check_work and return embed? what about component options?
        # checks skill and uses skill amount to determine embed 
        await work_user(self, ctx, database, user, stats_data, title, t_color)

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Shops
    @commands.command(aliases=['shop', 'store'])
    async def _shop(self, ctx, page = 1):
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        items = await get_itemlist()
        shopables = await get_shop(items)
        # # # # # # # # # # # # # # # # # # # # # # # # # #

        gem_emoji = self.bot.get_emoji(877620442712653824)
        embed = discord.Embed(title = "Item Shop", color = discord.Color.from_rgb(254, 254, 254))
        embed.set_thumbnail(url = 'https://i.imgur.com/E2AWhOt.png')
        embed.set_footer(text = f'Type "m.buy [amount] [item] to buy stuff!"', icon_url = "https://i.imgur.com/E2AWhOt.png")
        
        if page == 1:
            i = 0
            while i < 10:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 2:
            i = 10
            while i < 20:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 3:
            i = 20
            while i < 30:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 4:
            i = 30
            while i < 40:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 5:
            i = 40
            while i < 50:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 6:
            i = 50
            while i < 60:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1

        if page == 7:
            i = 60
            while i < 70:
                try:
                    user_item = shopables[i]
                    
                    item_name = items[user_item]["name"]
                    item_description = items[user_item]["description"]
                    emoji = items[user_item]["emoji"]
                    rarity = items[user_item]["rarity"]
                    store_value = items[user_item]["store_value"]

                    embed.add_field(name = f'**{gem_emoji} {items[user_item]["store_value"]} -** {self.bot.get_emoji(items[user_item]["emoji"])} {items[user_item]["name"]} {self.bot.get_emoji(rarity)}', value = f'{items[user_item]["description"]}', inline = False)
                except:
                    pass

                i += 1


        await ctx.send(embed = embed)

    @commands.command(aliases = ['buy', 'b'])
    async def _buy(self, ctx, *args):
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        items = await get_itemlist()
        title, t_color = await get_title(self, user, ctx, database)
        item_amount, item_name = await dissect_for_shop(ctx, args)
        await apply_status(user, database, ctx, status_list)
        key = await get_item_key(item_name)

        if "Stunned" in status_list:
            pass
        else:
            if key == "Failed":
                await ctx.send("Something went wrong with your command!")
            else:
                item_value = items[key]["store_value"]
                buy_amount = (float(item_amount) * float(item_value)) * buy_tax
                emoji = items[key]["emoji"]
                name = items[key]["name"]
                gem_gif = self.bot.get_emoji(877620442712653824)
                confirm_button = Button(label = "Confirm", style = ButtonStyle.green, custom_id = "buy_confirm")
                decline_button = Button(label = "Decline", style = ButtonStyle.red, custom_id = "buy_decline")

                if items[key]["buyable"] == "True":
                    if bank_data[0] >= buy_amount:
                        confirm_embed = discord.Embed(title = f"{username.display_name} Confirm your buy order:", description = f"{title}", color = t_color)
                        confirm_embed.set_thumbnail(url = username.avatar_url)
                        confirm_embed.add_field(name = f"You are about to buy:\n **({item_amount})** {self.bot.get_emoji(emoji)} {name}", value = f"For: {gem_gif} {round(buy_amount)} gems")
                        confirm_embed.add_field(name = f"Current Tax:", value = f"**({buy_tax_percent})**")

                        message = await ctx.send(
                            embed = confirm_embed,
                            components = [[confirm_button, decline_button]]
                        )

                        def check(interaction):
                            if ctx.author == interaction.user:
                                return True
                            else:
                                return False
                        
                        try:
                            interaction = await self.bot.wait_for("button_click", check = check, timeout = 30)
                            selection = interaction.component.label

                            if selection == "Confirm": # Perform trade
                                confirm_trade = discord.Embed(title = f'{username.display_name}, purchase succeeded!', color = discord.Color.green())
                                await update_money(user, database, 'wallet', -buy_amount)
                                await update_item(database, user, item_amount, key, "add")

                                await message.edit(embed = confirm_trade, components = [])
                            
                            if selection == "Decline":
                                decline_embed = discord.Embed(title = f"{username.display_name}, you declined the buy order!", color = discord.Color.red())
                                await message.edit(embed = decline_embed, components = [])
                                await interaction.respond(type=6)


                        except asyncio.TimeoutError:
                            timeout_embed = discord.Embed(title = f"{ctx.message.author.display_name}, your buy order timed out!")
                            await message.edit(embed = timeout_embed, components = [])
                            await interaction.respond(type=6)
                    
                    else: # Doesnt have enough money
                        await ctx.send(f"{username.mention}, you dont have enough in your wallet! You need {gem_gif} {round(buy_amount)} gems")
                        # show current buy tax and required value
                else:
                    await ctx.send("That item cannot be purchased!")

    @commands.command(aliases = ['sell', 's'])
    async def _sell(self, ctx, *args):
        user = ctx.message.author.id
        username = ctx.message.author
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        status_list = await get_status_affected(user, database)
        items = await get_itemlist()
        title, t_color = await get_title(self, user, ctx, database)
        item_amount, item_name = await dissect_for_shop(ctx, args)
        key = await get_item_key(item_name)
        await apply_status(user, database, ctx, status_list)

        if "Stunned" in status_list:
            pass
        else:
            if key == "Failed":
                await ctx.send("Something went wrong with your command!")
            else:
                item_value = items[key]["store_value"]
                sell_amount = (float(item_amount) * float(item_value)) * sell_tax
                emoji = items[key]["emoji"]
                name = items[key]["name"]
                gem_gif = self.bot.get_emoji(877620442712653824)
                confirm_button = Button(label = "Confirm", style = ButtonStyle.green, custom_id = "sell_confirm")
                decline_button = Button(label = "Decline", style = ButtonStyle.red, custom_id = "sell_decline")
                user_item_amount = await fetch_item(user, database, key)

                if items[key]["sellable"] == "True":
                    if int(user_item_amount) >= int(item_amount):
                        confirm_embed = discord.Embed(title = f"{username.display_name} Confirm your sell order:", description = f"{title}", color = t_color)
                        confirm_embed.set_thumbnail(url = username.avatar_url)
                        confirm_embed.add_field(name = f"You are about to sell:\n **({item_amount})** {self.bot.get_emoji(emoji)} {name}", value = f"For: {gem_gif} {round(sell_amount)} gems")
                        confirm_embed.add_field(name = f"Current Tax:", value = f"**({sell_tax_percent})**")

                        message = await ctx.send(
                            embed = confirm_embed,
                            components = [[confirm_button, decline_button]]
                        )

                        def check(interaction):
                            if ctx.author == interaction.user:
                                return True
                            else:
                                return False
                        
                        try:
                            interaction = await self.bot.wait_for("button_click", check = check, timeout = 30)
                            selection = interaction.component.label

                            if selection == "Confirm": # Perform trade
                                confirm_trade = discord.Embed(title = f'{username.display_name}, sell order succeeded!', color = discord.Color.green())
                                await update_money(user, database, 'wallet', sell_amount)
                                await update_item(database, user, item_amount, key, "remove")

                                await message.edit(embed = confirm_trade, components = [])
                            
                            if selection == "Decline":
                                decline_embed = discord.Embed(title = f"{username.display_name}, you declined the sell order!", color = discord.Color.red())
                                await message.edit(embed = decline_embed, components = [])
                                await interaction.respond(type=6)


                        except asyncio.TimeoutError:
                            timeout_embed = discord.Embed(title = f"{ctx.message.author.display_name}, your sell order timed out!")
                            await message.edit(embed = timeout_embed, components = [])
                            await interaction.respond(type=6)
                    
                    else: # Doesnt have enough items
                        await ctx.send(f"{username.mention}, you dont have enough of that item!")
                else:
                    await ctx.send("That item cannot be sold!")


    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add(self, reaction, user):
        username = user
        user = user.id
        await create_economy(username, user)
        database = await get_database()
        bank_data, stats_data = await get_info_from_database(user, database)
        title, t_color = await get_title(self, user, ctx, database)

        pass


    @commands.command(aliases = ['auction'])
    async def _auction(self, ctx, *args): # Library discontinued before I was able to make this.
        admin_check = await check_botadmin(user, ctx)

        if admin_check == True:
            pass
        else: 
            pass

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Testing
    @commands.command(aliases=['t', 'test'])
    async def _test(self, ctx):
        pass


# User data creation functions
async def create_economy(username, user):
    database = await get_database()
    kcdb_cursor = database.cursor()
    

    kcdb_cursor.execute("SELECT * FROM economy WHERE discord_id=%s", (user,))
    data = "error" #initially just assign the value
    
    for i in kcdb_cursor:
        data = i # if cursor has no data then loop will not run and value of data will be 'error'
    
    if data == "error": # User does not exist
        insert_1 = "INSERT INTO economy (username, discord_id, wallet, bank) VALUES (%s, %s, %s, %s)"
        insert_2 = (f"{username}", f"{user}", "0", "0")
        
        kcdb_cursor.execute(insert_1, insert_2)
        database.commit()
        print(f"{username} has registered.")
        
        await create_stats(username, user) # Continue to create stats 
    
    else: # User does exist already
        pass

async def create_stats(username, user): # Link to create_economy
    database = await get_database()
    kcdb_cursor = database.cursor()
    

    kcdb_cursor.execute("SELECT * FROM user_stats WHERE discord_id=%s", (user,))
    data = "error" #initially just assign the value
    
    for i in kcdb_cursor:
        data = i # if cursor has no data then loop will not run and value of data will be 'error'
    
    if data == "error": # User does not exist
        insert_1 = "INSERT INTO user_stats (username, discord_id) VALUES (%s, %s)"
        insert_2 = (f"{username}", f"{user}")
        
        kcdb_cursor.execute(insert_1, insert_2)
        database.commit()

        await create_inventory(username, user)

async def create_inventory(username, user): # Link to create_stats
    database = await get_database()
    kcdb_cursor = database.cursor()
    

    kcdb_cursor.execute("SELECT * FROM inventory WHERE discord_id=%s", (user,))
    data = "error" #initially just assign the value
    
    for i in kcdb_cursor:
        data = i # if cursor has no data then loop will not run and value of data will be 'error'
    
    if data == "error": # User does not exist
        insert_1 = "INSERT INTO inventory (username, discord_id) VALUES (%s, %s)"
        insert_2 = (f"{username}", f"{user}")
        
        kcdb_cursor.execute(insert_1, insert_2)
        database.commit()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Checking and managing health/status
async def update_health(user, ctx, database, change, severity):
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute("SELECT health FROM user_stats WHERE discord_id=%s", (user,))
    user_health = kcdb_cursor.fetchone()
    new_health = user_health[0] + change
    kcdb_cursor.execute("UPDATE user_stats SET health = %s WHERE discord_id = %s", (new_health, user))
    database.commit()

    if new_health <= 0:
        await kill_user(user, ctx, database, severity)
        return True
    else:
        return False
    
async def kill_user(user, ctx, database, severity):
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute("UPDATE user_stats SET health = %s WHERE discord_id = %s", (100, user))
    kcdb_cursor.execute("SELECT bank FROM economy WHERE discord_id=%s", (user,))
    current_bank = kcdb_cursor.fetchone()


    if severity == 1:
        loss_range = random.randrange(2000, 6000)
        new_bank = current_bank[0] - loss_range
    if severity == 2:
        pass
    if severity == 3:
        pass
    if severity == 4:
        pass
    
    kcdb_cursor.execute("UPDATE economy SET bank = %s WHERE discord_id = %s", (new_bank, user))
    database.commit()

    death_embed = discord.Embed(title = f'{ctx.message.author.display_name}, you died!', description = f'You paid {loss_range:,} gems for medical bill costs.' , color = discord.Color.red())
    death_embed.set_thumbnail(url = ctx.message.author.avatar_url)
    death_embed.set_footer(text = 'Your health has been reset to ❤️ 100!', icon_url = ctx.message.author.avatar_url)
    await ctx.send(embed = death_embed)

async def check_status(ctx, embed, status_list, stats_data):
    if len(status_list) >= 1:
        emoji_list = []
        for i in status_list:
            if i == "Stunned":
                emoji_list.append("💫")
            if i == "Toxin":
                emoji_list.append("🤢")
            if i == "Frozen":
                emoji_list.append("❄️")
            if i == "Charmed":
                emoji_list.append("💖")
            if i == "Cursed":
                emoji_list.append("💀")
        embed.set_footer(text =f"❤️ {stats_data[0]} | {' '.join([str(s) for s in list(emoji_list)])}", icon_url = f'{ctx.message.author.avatar_url}')
    else:
        embed.set_footer(text =f"❤️ {stats_data[0]}", icon_url = f'{ctx.message.author.avatar_url}')

async def change_title(database, user, title):
    query = f"UPDATE economy SET title = '{title}' WHERE discord_id = {user}"
    
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute(query)
    database.commit()

async def work_user(self, ctx, database, user, stats_data, title, t_color):
    gem_gif = self.bot.get_emoji(877620442712653824)
    user_tree = await get_user_tree(database, user)
    # health,crime_skill,slut_skill,stunned,toxin,frozen,police_skill,biologist_skill,journalist_skill,doctor_skill,mechanic_skill
    one_button = Button(label = "1", style = ButtonStyle.blue, custom_id = "one_button")
    two_button = Button(label = "2", style = ButtonStyle.blue, custom_id = "two_button")
    three_button = Button(label = "3", style = ButtonStyle.blue, custom_id = "three_button")

    def check(interaction):
        if ctx.author == interaction.user:
            return True
        else:
            return False

    if user_tree == "Police":
        police_skill = stats_data[6]
        skill_title = await check_skill_title("Police", police_skill)
        if skill_title == "Police Cadet":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "Your senior officer asks, what does radio code 10-10 mean?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Where is your location?\n2. Hurt/Injured.\n3. Off duty.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You spend {gem_gif} -{rand_gems} on a tv dinner and go home feeling like a failure.\n-**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', -1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(20, 50)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You bought an online course for {gem_gif} -{rand_gems} and learned 10-10 means: Off Duty.\n-**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', -1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your senior officer paid you {gem_gif} +{rand_gems} for being correct!\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "You see that your senior officer's phone is unlocked, what should you do?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Leave it alone.\n2. Snoop through his phone.\n3. Return it back to him.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You spend {gem_gif} -{rand_gems} on a movie and wonder what you would have found on his phone.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(50, 150)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You found evidence of corruption on his phone! The Chief of Police paid you {gem_gif} +{rand_gems} for being a good cop!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(20, 60)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your senior officer paid you {gem_gif} +{rand_gems} for finding his phone!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "Your senior officer asks, what does radio code 10-20 mean?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Where is your location?\n2. Hurt/Injured.\n3. Off duty.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your senior officer paid you {gem_gif} +{rand_gems} for being a well-informed cadet!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(20, 50)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You bought an online course for {gem_gif} -{rand_gems} and learned 10-20 means: Where is your location?.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You spend {gem_gif} -{rand_gems} on a word puzzle and go home feeling like a failure.!\n-**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])
            
        if skill_title == "Police Officer":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "You take your cadet on a ride-along and they asked you what 10-20 means."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. It means that you are in danger.\n2. It means 'where is your location'.\n3. It means bomb threat.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"You were fined {gem_gif} -{rand_gems} for giving your cadet wrong information.\n-**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', -1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(100, 200)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You were paid {gem_gif} +{rand_gems} for being a good officer.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(150, 220)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You gave your cadet wrong information but there really was a bomb threat and your cadet saved many lives. You were paid {gem_gif} +{rand_gems} for saving lives!\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "You see some suspicious activity in an alley-way, what do you do?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Check it out.\n2. Its probably nothing.\n3. Call it in to another officer.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(150, 220)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You caught a well known criminal but he managed to cut your arm. {gem_gif} +{rand_gems} were paid to you, but you lost ❤️ -1.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)
                        await update_health(user, ctx, database, -1, 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(20, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You were paid {gem_gif} +{rand_gems} for the day.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your fellow officer caught a well known criminal. {gem_gif} +{rand_gems} you were paid for the day!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "You see someone breaking the law, what do you do?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Arrest them.\n2. Let them go.\n3. Call it in to a fellow officer.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(50, 150)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You arrested the criminal and were paid {gem_gif} +{rand_gems} for doing a good job.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(20, 50)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"Your body cam caught you letting them go, you were fined {gem_gif} -{rand_gems} and got a lecture from your captain.\n-**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', -earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(50, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your fellow officer arrested the criminals. {gem_gif} +{rand_gems} was your daily pay.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])
           
        if skill_title == "Police Sergeant":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "You are asked to conduct an inspection of a suspicious vehicle at a roadblock. What do you do first?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Check under the car.\n2. Check the backseat.\n3. Talk to the driver.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(400, 1000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You found nothing, giving the driver enough time to hide anything illegal. {gem_gif} +{rand_gems} for doing police work.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(300, 800)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You found an illegal amount of drugs. {gem_gif} +{rand_gems} for being a good officer.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(300, 920)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"The driver told you nothing but you smelled drugs in his car and ended up finding some. {gem_gif} +{rand_gems} for doing good police work!\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "You take some officers to raid a potential gang safehouse. Where do you order your officers to enter from?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Through the front door.\n2. Check for an open window.\n3. Go through the back.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(300, 950)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You went through the front door but got shot in the arm. Multiple gang member casualties and no arrests. {gem_gif} +{rand_gems} was paid to you, but you lost ❤️ -5.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)
                        await update_health(user, ctx, database, -5, 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(300, 500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You told one of your officers to climb through a window but he was shot and killed. {gem_gif} +{rand_gems} was paid to you, but you feel like you caused a fellow officer to die.\n-**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', -earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(500, 1000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You went through the back and got multiple arrests. {gem_gif} +{rand_gems} you were paid for the day!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "You are asked to organize a police escort for an important VIP. Which car do you place the VIP in? 1-5"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Car 1, in the front.\n2. Car 3, in the middle.\n3. Car 5 at the back.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(300, 900)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"There was an attack on your escort but only the middle two cars were hit during the attack. {gem_gif} +{rand_gems} for doing a good job.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(300, 500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"The middle vehicles were blown up by an RPG and the VIP was killed. {gem_gif} -{rand_gems} you lost your paycheck for failing the escort service.\n-**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'police_skill', -earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(300, 900)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"The cars in front of you were blown up in a terrorist attack, however the VIP was safe. {gem_gif} +{rand_gems} was paid to you for safely escorting the VIP.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])
       
        if skill_title == "Deputy Police Chief":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "A local bank was being robbed and was escalated into a hostage situation, you arrive at scene, what do you do first?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Use a megaphone to communicate to the bank robbers.\n2. Set up snipers and a forward S.W.A.T team to take out the criminals.\n3. Send a negotiator into the bank.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(1000, 3000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You managed to get the hostages out safely, but during the scene one of the criminals escaped. {gem_gif} +{rand_gems} was paid for doing a fine job.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(1000, 2500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your officers managed to kill all of the criminals, but one of the hostages was executed in retaliation. {gem_gif} +{rand_gems} was your paycheck.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(1200, 2000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"The negotiator only escalated the situation and was killed in the process. However, during that time your officers managed to sneak in a different entrance and detain all criminals. {gem_gif} +{rand_gems} for doing your police work!\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "The chief asked you to take care of some police documents for him."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Start with incident reports.\n2. Start with case documents.\n3. Start with internal reports.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(1300, 3000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You go through and file incident reports. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(1300, 2000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You go through and fill out case documents. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(1500, 2200)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You go through internal reports and end up having to fire a cadet for drug use. {gem_gif} +{rand_gems} was your paycheck.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "The chief asks you to go over case files from a recent internal investigation."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Look at current evidence regarding possible corruption.\n2. Review evidence relating to the officers in question.\n3. Put off your work until later.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(1000, 3000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find no evidence of corruption, you submit your findings to the chief. {gem_gif} +{rand_gems} for doing a good job.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(1300, 2500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You found evidence of the officer commiting a crime. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(1300, 2600)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You failed work!", value = f"The chief was angry with you for not doing your job. {gem_gif} +{rand_gems} was your paycheck.\n-**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', -earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])
       
        if skill_title == "Chief of Police":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "As an attempt to reduce crime in your city you start a new program. What do you focus on?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Try to encourage people not to buy weapons.\n2. Increase patrol units in low-income districts.\n3. Offer free guns to people who can't afford it.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(5000, 20000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your program only slightly reduced crime rates, however, anything is better than nothing. {gem_gif} +{rand_gems} was paid to you.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(4000, 15500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"The patrols succeed in reducing crime rates by 10% in your city. {gem_gif} +{rand_gems} was paid to you.\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(2300, 12000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Giving out free weapons increased crime rates, also reducing your paycheck to make up for the amount spent on guns. {gem_gif} +{rand_gems} for doing good police work!\n+**1 Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "The president is flying into town and you are asked to assist in escorting him. How do you go about it?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Set up snipers in tall buildings to search for suspicious activity.\n2. Place multiple armored vehicles into the escort.\n3. Close off roads leading to his destination to prevent traffic.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(3000, 11000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"Your snipers see no suspicious activity and the escort goes well. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(3000, 10000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You place armored vehicles into the escort, everything goes well. {gem_gif} +{rand_gems} was paid to you, but you feel like armored vehicles was a bit too much.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(5000, 15000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You close off roads to prevent traffic and the escort goes well. {gem_gif} +{rand_gems} was paid to you!\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "You need to go over police documents. Where do you start?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Make your Deputy Chief do the paperwork.\n2. Begin with looking over officer duty logs.\n3. Sign important documents.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(3000, 9000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You give your deupty chief the work. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(4000, 13000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You completed your paperwork. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3": # important documents
                        rand_gems = random.randrange(4000, 15000)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You completed you paperwork. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Police Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'police_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])
       

    if user_tree == "Biologist": 
        biologist_skill = stats_data[7]
        skill_title = await check_skill_title("Biologist", biologist_skill)
        if skill_title == "Intern":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "You study a recently discovered micro organism called Mavungi. What do you focus on?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Self production.\n2. Defense mechanisms.\n3. The intelligence of the organism.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(100, 400)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You found out interesting information that the organism reproduces by itself. {gem_gif} +{rand_gems} was paid to you for your research.\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(200, 500)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You discover that the organism has the ability to defend itself from other invasive microorganisms {gem_gif} +{rand_gems} was paid to you for your research.\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(250, 550)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You study the organisms intellect but find no sign of any. You were paid {gem_gif} +{rand_gems} for your research findings!\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "You are asked to replace the water filters for a tank filled with bacteria."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Place new filter into the tank and leave the old one in.\n2. Remove the older filter and put in a new one.\n3. Ask another intern to help you.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(100, 400)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You insert the new filter into the tank and it seems to of worked well. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(100, 400)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You were paid {gem_gif} +{rand_gems} for helping out.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(20, 100)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"The intern you asked to help accidentally broke the filter. You had to pay {gem_gif} +{rand_gems} to replace it!\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', -rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "You study common bacteria. Where do you focus?"
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Living conditions.\n2. Reproductive capabilities.\n3. Diet and nutritional desires.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(100, 450)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You don't discover anything new, but do learn a few new things. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(120, 450)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You learn a lot of interesting facts, but discover nothing new. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(150, 400)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find that many bacteria feast on starches and sugars found on most living organisms. {gem_gif} +{rand_gems} was your daily pay.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

        if skill_title == "Microbiologist":
            rand = random.randrange(0, 100)
            embed = discord.Embed(title = f"{ctx.message.author.display_name} Working", description = f"{title}", color = t_color)
            if rand <= 10:
                scenario = "You are asked to study Mavungi more closely as it seems to be growing fast."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Study it's diet and nutrition intake. \n2. Study it's cell division process.\n3. Study how it's growing.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(300, 600)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You discover that Mavungi has the ability to eat just about anything. {gem_gif} +{rand_gems} was paid to you for your research.\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(300, 550)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You discover that Mavungi has the ability to increase it's size by 5% each week. {gem_gif} +{rand_gems} was paid to you for your research.\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(250, 700)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You study the organisms growth patterns and discover it is growing abnormally fast. You were paid {gem_gif} +{rand_gems} for your research findings!\n+**1 Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', 1)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 10 and rand <= 50:
                scenario = "You are invited along to a marine dive to study small marine creatures."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Look for coral and other sea plant life.\n2. Take samples of the ocean floor.\n3. Take records of temperatures and living conditions.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(400, 700)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find a lot of sea life and take some pictures. {gem_gif} +{rand_gems} was paid to you for your research.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(300, 600)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You scoop some samples of sand and other minerals for later studies. {gem_gif} +{rand_gems} for helping out.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(200, 600)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You take record of the temperature and take pictures of the ocean floor. You were paid {gem_gif} +{rand_gems} for your research!\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])

            if rand > 50:
                scenario = "You take water samples from a swamp to study life within it."
                embed.add_field(name = f"{scenario}", value = "**Choose an option:**\n\n1. Look for signs of life.\n2. Look for more signs of life.\n3. Look for even more signs of life.", inline = False)

                message = await ctx.send(
                    embed = embed,
                    components = [[one_button, two_button, three_button]]
                )

                try:
                    interaction = await self.bot.wait_for("button_click", check = check, timeout = 50)
                    selection = interaction.component.label

                    if selection == "1":
                        rand_gems = random.randrange(200, 700)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find signs of common algae and bacterial life. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "2":
                        rand_gems = random.randrange(120, 750)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find and odd lack of bacteria and algae in the samples. {gem_gif} +{rand_gems} was paid to you.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                    
                    if selection == "3":
                        rand_gems = random.randrange(250, 950)
                        new_embed = discord.Embed(title = f"{ctx.message.author.display_name} finished working.", description = f"{title}", color = t_color)
                        new_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        new_embed.add_field(name = "You completed work!", value = f"You find a sample of Mavungi somehow. This is an important discovery considering researchers thought they had the only sample of Mavungi {gem_gif} +{rand_gems} was paid to you for your research.\n+**{earned_w_skill} Marine Biology Skill**", inline = False)
                        await update_money(user, database, 'wallet', rand_gems)
                        await update_skill(user, database, 'biologist_skill', earned_w_skill)

                        await message.edit(embed = new_embed, components = [])
                        await interaction.respond(type=6)
                
                
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(title = "Timed out!")
                    await message.edit(embed = timeout_embed, components = [])


    
    if user_tree == "Journalist": 
        journalist_skill = stats_data[8]
        skill_title = await check_skill_title("Journalist", journalist_skill)

    
    if user_tree == "Doctor": 
        doctor_skill = stats_data[9]
        skill_title = await check_skill_title("Doctor", doctor_skill)

    
    if user_tree == "Mechanic": 
        mechanic_skill = stats_data[10]
        skill_title = await check_skill_title("Mechanic", mechanic_skill)

async def try_title_change(self, ctx, user, database, title):
    if title == "angel":
            amount = await fetch_item(user, database, "item76")
            if amount > 0:
                await change_title(database, user, "Angel")
            
    if title == "demon":
        amount = await fetch_item(user, database, "item77")
        if amount > 0:
            await change_title(database, user, "Demon")

    if title == "vampire":
        amount = await fetch_item(user, database, "item78")
        if amount > 0:
            await change_title(database, user, "Vampire")

    if title == "none":
        await change_title(database, user, "None")
    pass
    
async def get_skill_data(user, database):
    s_selection = await get_user_tree(database, user)
    bank_data, stats_data = await get_info_from_database(user, database)
    # health,crime_skill,slut_skill,stunned,toxin,frozen,police_skill,biologist_skill,journalist_skill,doctor_skill,mechanic_skill

    if s_selection == "Mechanic":
        s_amount = stats_data[10]
        s_title = await check_skill_title('Mechanic', s_amount)

    if s_selection == "Police":
        s_amount = stats_data[6]
        s_title = await check_skill_title('Police', s_amount)

    if s_selection == "Biologist":
        s_selection = "Marine Biologist"
        s_amount = stats_data[7]
        s_title = await check_skill_title('Biologist', s_amount)

    if s_selection == "Journalist":
        s_amount = stats_data[8]
        s_title = await check_skill_title('Journalist', s_amount)

    if s_selection == "Doctor":
        s_amount = stats_data[9]
        s_title = await check_skill_title('Doctor', s_amount)


    return s_selection, s_amount, s_title

async def change_job(user, database, desired):
    query = f"UPDATE economy SET work = '{desired}' WHERE discord_id = {user}"
    
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute(query)
    database.commit()

async def check_skill_title(skill, skill_amount):
    if skill == "Police":
        if skill_amount < 100:
            return "Police Cadet"
        if skill_amount >= 100 and skill_amount < 500:
            return "Police Officer"
        if skill_amount >= 500 and skill_amount < 2000:
            return "Police Sergeant"
        if skill_amount >= 2000 and skill_amount < 5000:
            return "Police Captain"
        if skill_amount >= 5000 and skill_amount < 10000:
            return "Deputy Police Chief"
        if skill_amount >= 10000:
            return "Chief of Police"
    
    if skill == "Biologist":
        if skill_amount < 100:
            return "Intern"
        if skill_amount >= 100 and skill_amount < 300:
            return "Microbiologist"
        if skill_amount >= 300 and skill_amount < 1000:
            return "Marine Biologist"
        if skill_amount >= 1000 and skill_amount < 2500:
            return "Aquarist"
        if skill_amount >= 2500 and skill_amount < 5000:
            return "Aquarium Manager"
    
    if skill == "Journalist":
        if skill_amount < 200:
            return "Freelance Writer"
        if skill_amount >= 200 and skill_amount < 400:
            return "Journalist"
        if skill_amount >= 400 and skill_amount < 900:
            return "Reporter"
        if skill_amount >= 900 and skill_amount < 2500:
            return "Investigative Journalist"
        if skill_amount >= 2500 and skill_amount < 6000:
            return "News Editor"
        if skill_amount >= 6000:
            return "News Manager"
    
    if skill == "Doctor":
        if skill_amount < 250:
            return "Intern"
        if skill_amount >= 250 and skill_amount < 600:
            return "Jr. Resident"
        if skill_amount >= 600 and skill_amount < 1400:
            return "Sr. Resident"
        if skill_amount >= 1400 and skill_amount < 3000:
            return "Chief Resident"
        if skill_amount >= 3000 and skill_amount < 5000:
            return "Doctor"
        if skill_amount >= 5000 and skill_amount < 10000:
            return "Surgeon"
        if skill_amount >= 10000:
            return "Medical Director"
    
    if skill == "Mechanic":
        if skill_amount < 100:
            return "Entry Technician"
        if skill_amount >= 100 and skill_amount < 300:
            return "Mechanic's Assistant"
        if skill_amount >= 300 and skill_amount < 1000:
            return "Auto Mechanic"
        if skill_amount >= 1000 and skill_amount < 3000:
            return "Repair Specialist"
        if skill_amount >= 3000:
            return "Supercar Mechanic"

async def get_user_tree(database, user):
    query = f"SELECT work FROM economy WHERE discord_id={user}"
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute(query)
    user_tree = kcdb_cursor.fetchone()

    return user_tree[0]

async def update_skill(user, database, skill, amount):
    kcdb_cursor = database.cursor()
    query1 = f"SELECT {skill} FROM user_stats WHERE discord_id={user}"

    kcdb_cursor.execute(query1)
    skill_amount = kcdb_cursor.fetchone()
    
    new_amount = skill_amount[0] + amount
    query2 = f"UPDATE user_stats SET {skill} = {new_amount} WHERE discord_id={user}"
    kcdb_cursor.execute(query2)

    database.commit()

async def apply_status(user, database, ctx, status_list):
    for i in status_list:
        if i == "Stunned":
            stunned_embed = discord.Embed(title = f'{ctx.message.author.display_name}, you are Stunned!', description = 'You must wait...', color = discord.Color.from_rgb(255, 204, 117))
            stunned_embed.set_thumbnail(url = ctx.message.author.avatar_url)
            await ctx.send(embed = stunned_embed)
        if i == "Toxin":
            death = await update_health(user, ctx, database, -1, 1) # First number is amount lost, second is severity so 1-4
            toxin_embed = discord.Embed(title = f'{ctx.message.author.display_name}, you are Toxined!', description = f'You lost :heart: 1 and have :heart: {stats_data[0] - 1} left.', color = discord.Color.from_rgb(131, 165, 99))
            toxin_embed.set_thumbnail(url = ctx.message.author.avatar_url)
            await ctx.send(embed = toxin_embed)
        if i == "Cursed":
            pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Change and manage money
async def update_money(user, database, column, amount):
    # Take in a user and update their money to new amount
    # Amount is current_amount + amount = new_amount
    # Column is bank/wallet
    kcdb_cursor = database.cursor()
    
    if column == "bank":
        kcdb_cursor.execute("SELECT bank FROM economy WHERE discord_id=%s", (user,))
        current_amount = kcdb_cursor.fetchone()
        new_amount = int(current_amount[0]) + int(amount)
        kcdb_cursor.execute("UPDATE economy SET bank = %s WHERE discord_id=%s", (new_amount, user,))

    if column == "wallet":
        kcdb_cursor.execute("SELECT wallet FROM economy WHERE discord_id=%s", (user,))
        current_amount = kcdb_cursor.fetchone()
        new_amount = int(current_amount[0]) + int(amount)
        kcdb_cursor.execute("UPDATE economy SET wallet = %s WHERE discord_id=%s", (new_amount, user,))

    database.commit()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#Inventory Creation & Management
max_items = 78 + 1
async def get_user_inventory_list(user, database):
    user_items = []
    
    i = 1
    while i < max_items:
        check = "item" + f"{i}"

        kcdb_cursor = database.cursor()
        kcdb_cursor.execute("SELECT item%s FROM inventory WHERE discord_id=%s", (i, user,))
        fetch_var = kcdb_cursor.fetchone()
        
        if fetch_var[0] != 0:
            user_items.append(check)

        i += 1
    
    return user_items

async def get_itemlist():
    with open(os.path.join(os.path.dirname(__file__),"itemlist.json"), 'r') as f:
        item_list = json.load(f)
    f.close()
    return item_list

async def fetch_item(user, database, item):
    query = f"SELECT {item} FROM inventory WHERE discord_id={user}"

    kcdb_cursor = database.cursor()
    kcdb_cursor.execute(query)
    item_amount = kcdb_cursor.fetchone()

    return item_amount[0]

async def update_item(database, user, item_quantity, item, check):

    if check == "add":
        current_amount = await fetch_item(user, database, item)
        new_amount = current_amount + int(item_quantity)

        query = f"UPDATE inventory SET {item} = {new_amount} WHERE discord_id={user}"

        kcdb_cursor = database.cursor()
        kcdb_cursor.execute(query)
        item_amount = kcdb_cursor.fetchone()

        database.commit()
    
    if check == "remove":
        current_amount = await fetch_item(user, database, item)
        new_amount = current_amount - int(item_quantity)

        query = f"UPDATE inventory SET {item} = {new_amount} WHERE discord_id={user}"

        kcdb_cursor = database.cursor()
        kcdb_cursor.execute(query)
        item_amount = kcdb_cursor.fetchone()

        database.commit()

async def dissect_for_trade(ctx, args):
    message = args

    if "for" in message or "For" in message: # No errors
        target_index = message.index('for')
        first_part = message[:target_index]
        target_index2 = target_index + 1
        second_part = message[target_index2:]

        try:
            item1_quantity = first_part[0]
            item1_name = first_part[1].lower() + " " + first_part[2].lower()
            item2_quantity = second_part[0]
            item2_name = second_part[1].lower() + " " + second_part[2].lower()

            return item1_quantity, item1_name, item2_quantity, item2_name
        except:
            try:
                item1_quantity = first_part[0]
                item1_name = first_part[1].lower()
                item2_quantity = second_part[0]
                item2_name = second_part[1].lower()

                return item1_quantity, item1_name, item2_quantity, item2_name
            except: 
                 return "Failed", "Failed", "Failed", "Failed"

async def dissect_for_shop(ctx, args):
    message = args
    try:
        try:
            item_amount = message[0]
            first_part = message[1]
            second_part = message[2]
            item_name = first_part.lower() + " " + second_part.lower()
            return item_amount, item_name
        
        except:
            item_amount = message[0]
            item_name = message[1].lower()
            return item_amount, item_name
    
    except:
        print("shop dissect error")
        return "Failed", "Failed"


async def get_offer_info(database, user1, user2, item1_quantity, item1_name, item2_quantity, item2_name):
    item1 = await get_item_key(item1_name)
    item2 = await get_item_key(item2_name)

    user1_item_amount = await fetch_item(user1, database, item1)
    user2_item_amount = await fetch_item(user2, database, item2)


    if user1_item_amount >= int(item1_quantity) and user2_item_amount >= int(item2_quantity):
        return "ready", "ready"
    else:
        print("get_offer_info failed")
        return "quantity_error", "quantity_error"

async def get_item_key(name):

    if str(name) == "Failed":
        return "Failed"

    grape_alias = ['grap', 'grapes', 'grape']
    if str(name).lower() in grape_alias:
        return "item1"

    corn_alias = ['corn']
    if str(name).lower() in corn_alias:
        return "item2"

    blueb_alias = ['blueb', 'blueberry', 'blueberri', 'blueberrie', 'blueberies', 'blueberries', 'blueberrys']
    if str(name).lower() in blueb_alias:
        return "item3"

    eggplant_alias = ['eggp', 'eggplant', 'eggplants', 'egplant', 'egplants']
    if str(name).lower() in eggplant_alias:
        return "item4"

    banana_alias = ['banana', 'bana', 'bananas', 'banan', 'banans']
    if str(name).lower() in banana_alias:
        return "item5"

    apple_alias = ['apple', 'aple', 'appl', 'apples', 'aples']
    if str(name).lower() in apple_alias:
        return "item6"

    mango_alias = ['mango', 'mang', 'mangos']
    if str(name).lower() in mango_alias:
        return "item7"

    bread_alias = ['bread', 'breads']
    if str(name).lower() in bread_alias:
        return "item8"

    peanuts_alias = ['peanuts', 'pean', 'peanut', 'penut', 'penuts', 'peanutt']
    if str(name).lower() in peanuts_alias:
        return "item9"

    olives_alias = ['olives', 'olive', 'olivs', 'oliv']
    if str(name).lower() in olives_alias:
        return "item10"

    salt_alias = ['salt', 'salts']
    if str(name).lower() in salt_alias:
        return "item11"

    iphone_alias = ['iphone', 'ifone', 'phone', 'phones', 'iphones', 'ifones']
    if str(name).lower() in iphone_alias:
        return "item12"

    cow_alias = ['cow', 'cows']
    if str(name).lower() in cow_alias:
        return "item13"

    milk_alias = ['milk', 'milks']
    if str(name).lower() in milk_alias:
        return "item14"

    pinkmilk_alias = ['pink milk', 'pinks', 'pink', 'pmilk', 'pink milks']
    if str(name).lower() in pinkmilk_alias:
        return "item15"

    fruitbowl_alias = ['fruit bowl', 'fruit', 'fruits', 'frute', 'fruit bowls']
    if str(name).lower() in fruitbowl_alias:
        return "item16"

    kingcrown_alias = ['king crown', 'kings crown']
    if str(name).lower() in kingcrown_alias:
        return "item17"

    frostcrown_alias = ['frost crown']
    if str(name).lower() in frostcrown_alias:
        return "item18"

    froststaff_alias = ['frost staff', 'frost', 'frost staffs']
    if str(name).lower() in froststaff_alias:
        return "item19"

    meat_alias = ['meat', 'meats']
    if str(name).lower() in meat_alias:
        return "item20"

    hide_alias = ['hide', 'hides']
    if str(name).lower() in hide_alias:
        return "item21"

    rat_alias = ['rat', 'rats']
    if str(name).lower() in rat_alias:
        return "item22"

    specialturkey_alias = ['special turkey', 'special', 'special turkeys']
    if str(name).lower() in specialturkey_alias:
        return "item23"

    rifle_alias = ['rifle', 'rifles']
    if str(name).lower() in rifle_alias:
        return "item24"

    floppa_alias = ['floppa', 'floppas']
    if str(name).lower() in floppa_alias:
        return "item25"

    icephoenix_alias = ['ice phoenix', 'ice phoenixs']
    if str(name).lower() in icephoenix_alias:
        return "item26"

    grifle_alias = ['golden rifle', 'grifle', 'goldrifle', 'gold rifle', 'gold rifles', 'golden rifles']
    if str(name).lower() in grifle_alias:
        return "item27"

    ivory_alias = ['ivory', 'ivorys']
    if str(name).lower() in ivory_alias:
        return "item28"

    lionfur_alias = ['lion fur', 'lion', 'lions', 'furs']
    if str(name).lower() in lionfur_alias:
        return "item29"

    hunterskamas_alias = ['hunters kamas', 'hunters kama', 'hunters']
    if str(name).lower() in hunterskamas_alias:
        return "item30"

    nevam_alias = ['nevam', 'crypto', 'cryptos', 'nevam crypto', 'nevam cryptos']
    if str(name).lower() in nevam_alias:
        return "item31"

    cocobeans_alias = ['cocobeans', 'coco beans', 'coco bean', 'cocos', 'coco']
    if str(name).lower() in cocobeans_alias:
        return "item32"

    bloodcrystal_alias = ['bloodcrystal', 'blood crystal', 'blood crystals']
    if str(name).lower() in bloodcrystal_alias:
        return "item33"

    crystalmeth_alias = ['crystalmeth', 'crystal meth', 'meth', 'meths', 'crystal meths']
    if str(name).lower() in crystalmeth_alias:
        return "item34"

    weed_alias = ['weed', 'weeds']
    if str(name).lower() in weed_alias:
        return "item35"

    weedplant_alias = ['weedplant', 'weed plant', 'weed plants']
    if str(name).lower() in weedplant_alias:
        return "item36"

    ape_alias = ['ape', 'apes']
    if str(name).lower() in ape_alias:
        return "item37"

    sealteamsix_alias = ['sealteam', 'seal team', 'seal teams']
    if str(name).lower() in sealteamsix_alias:
        return "item38"

    oilresidue_alias = ['oilresidue', 'oil residue', 'residue', 'oil residues', 'residues']
    if str(name).lower() in oilresidue_alias:
        return "item39"

    fishingrod_alias = ['fishingrod', 'rod', 'fishing rod', 'rods', 'fishing rods', 'fishing']
    if str(name).lower() in fishingrod_alias:
        return "item40"

    bait_alias = ['bait', 'baits']
    if str(name).lower() in bait_alias:
        return "item41"

    seabass_alias = ['seabass', 'sea bass', 'sea basses', 'bass', 'basses']
    if str(name).lower() in seabass_alias:
        return "item42"

    mackeral_alias = ['mackeral', 'mackerals']
    if str(name).lower() in mackeral_alias:
        return "item43"

    goldentuna_alias = ['goldentuna', 'golden tuna', 'tuna', 'golden tunas', 'tunas']
    if str(name).lower() in goldentuna_alias:
        return "item44"

    butteredtoast_alias = ['butteredtoast', 'buttered', 'buttered toast']
    if str(name).lower() in butteredtoast_alias:
        return "item45"

    butter_alias = ['butter', 'butters']
    if str(name).lower() in butter_alias:
        return "item46"

    simp_alias = ['simp', 'simps']
    if str(name).lower() in simp_alias:
        return "item47"

    rolledjoint_alias = ['rolledjoint', 'rolled', 'rolled joints', 'joint', 'joints']
    if str(name).lower() in rolledjoint_alias:
        return "item48"

    noxiousspider_alias = ['noxiousspider', 'noxious', 'noxious spider']
    if str(name).lower() in noxiousspider_alias:
        return "item49"

    antibiotics_alias = ['antibiotics', 'anti', 'antis', 'biotics', 'antibiotic']
    if str(name).lower() in antibiotics_alias:
        return "item50"

    nevamspirit_alias = ['nevamspirit', 'nevam spirit']
    if str(name).lower() in nevamspirit_alias:
        return "item51"

    chicken_alias = ['chicken', 'chickens']
    if str(name).lower() in chicken_alias:
        return "item52"

    eggs_alias = ['eggs', 'egg']
    if str(name).lower() in eggs_alias:
        return "item53"

    basiclootcrate_alias = ['basiclootcrate', 'basic', 'basic lootcrate']
    if str(name).lower() in basiclootcrate_alias:
        return "item54"

    flimsywalmart_alias = ['flimsywalmart', 'flimsy walmart', 'katana', 'flimsy']
    if str(name).lower() in flimsywalmart_alias:
        return "item55"

    cocaine_alias = ['cocaine', 'cocain', 'cocains', 'cocaines']
    if str(name).lower() in cocaine_alias:
        return "item56"

    cocaleaves_alias = ['cocaleaves', 'coca leaves', 'coca']
    if str(name).lower() in cocaleaves_alias:
        return "item57"

    lime_alias = ['lime', 'limess']
    if str(name).lower() in lime_alias:
        return "item58"

    water_alias = ['water', 'waters']
    if str(name).lower() in water_alias:
        return "item59"

    kerosene_alias = ['kerosene', 'kerosenes']
    if str(name).lower() in kerosene_alias:
        return "item60"

    sugar_alias = ['sugar', 'sugars']
    if str(name).lower() in sugar_alias:
        return "item61"

    cake_alias = ['cake', 'cakes']
    if str(name).lower() in cake_alias:
        return "item62"

    wine_alias = ['wine', 'wines']
    if str(name).lower() in wine_alias:
        return "item63"

    strawberry_alias = ['strawberry', 'strawberries', 'strawberrys', 'strawberrie', 'strawberies', 'strawbery', 'strawberr']
    if str(name).lower() in strawberry_alias:
        return "item64"

    oven_alias = ['oven', 'ovens']
    if str(name).lower() in oven_alias:
        return "item65"

    rolex_alias = ['rolexwatch', 'rolex', 'rolexs', 'rolex watch', 'rolex watches']
    if str(name).lower() in rolex_alias:
        return "item66"

    pearlnecklace_alias = ['pearlnecklace', 'pearl necklace', 'pearl necklaces']
    if str(name).lower() in pearlnecklace_alias:
        return "item67"

    tobaccoplant_alias = ['tobaccoplant', 'tobacco plants', 'tobacco plant', 'tobaco plant', 'tobaco plants']
    if str(name).lower() in tobaccoplant_alias:
        return "item68"

    tobacco_alias = ['tobacco', 'tobaco', 'tobacos', 'tobaccos']
    if str(name).lower() in tobacco_alias:
        return "item69"

    emeraldseal_alias = ['emeraldseal', 'emerald seal']
    if str(name).lower() in emeraldseal_alias:
        return "item70"

    rubyseal_alias = ['rubyseal', 'ruby seal']
    if str(name).lower() in rubyseal_alias:
        return "item71"

    amethystseal_alias = ['amethystseal', 'amethyst seal']
    if str(name).lower() in amethystseal_alias:
        return "item72"

    emerald_alias = ['emerald', 'emeralds']
    if str(name).lower() in emerald_alias:
        return "item73"

    ruby_alias = ['ruby', 'rubie', 'rubys', 'rubies']
    if str(name).lower() in ruby_alias:
        return "item74"

    amethyst_alias = ['amethyst', 'amethysts']
    if str(name).lower() in amethyst_alias:
        return "item75"

    angelwings_alias = ['angelwings', 'angel wings', 'angels', 'angel', 'angel wing']
    if str(name).lower() in angelwings_alias:
        return "item76"

    demonwings_alias = ['demonwings', 'demon wings', 'demon wing', 'demon', 'demons']
    if str(name).lower() in demonwings_alias:
        return "item77"

    vampirewings_alias = ['vampirewings', 'vampire wings', 'vampire', 'vampires', 'vampire wing']
    if str(name).lower() in vampirewings_alias:
        return "item78"

    grape_alias = ['grape', 'grapes', 'grap']
    if str(name).lower() in grape_alias:
        return "item79"

    grape_alias = ['grape', 'grapes', 'grap']
    if str(name).lower() in grape_alias:
        return "item80"

async def get_shop(items):
    shopables = []
    check = "item"
    i = 1
    while i < max_items:
        check = "item" + f"{i}"
        if items[check]["shop"] == "Shop":
            shopables.append(check)
        i+=1
    
    return shopables
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Helper functions
async def get_database(): # Details removed
    database = mysql.connector.connect(
    host = "localhost",
    user = "localhost",
    passwd = "passwd",
    database = "database", 
    auth_plugin='mysql_native_password')

    return database

async def get_info_from_database(user, database):
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute("SELECT wallet,bank FROM economy WHERE discord_id=%s", (user,))
    bank_data = kcdb_cursor.fetchone()
    
    return bank_data, stats_data

async def get_status_affected(user, database):
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute("SELECT stunned,toxin,frozen,charmed,cursed FROM user_stats WHERE discord_id=%s", (user,))
    data = kcdb_cursor.fetchone()
    status_list = []
    for i in data:
        if i == "Stunned":
            status_list.append("Stunned")
        if i == "Toxin":
            status_list.append("Toxin")
        if i == "Frozen":
            status_list.append("Frozen")
        if i == "Charmed":
            status_list.append("Charmed")
        if i == "Cursed":
            status_list.append("Cursed")
    
    return status_list

async def get_title(self, user, ctx, database):
    t_color = discord.Color.from_rgb(146, 146, 146)
    title = " "

    query = f"SELECT title FROM economy WHERE discord_id={user}"
    kcdb_cursor = database.cursor()
    kcdb_cursor.execute(query)
    title_var = kcdb_cursor.fetchone()


    if title_var[0] == "Owner":
        title = f"**{self.bot.get_emoji(821518453529772032)} Owner**"
        t_color = discord.Color.from_rgb(144, 246, 195)
    
    if title_var[0] == "Angel":
        title = f"{self.bot.get_emoji(878352957568061460)} **Angel** {self.bot.get_emoji(878352958163677214)}"
        t_color = discord.Color.from_rgb(235, 93, 173)
    
    if title_var[0] == "Demon":
        title = f"{self.bot.get_emoji(878351744667643964)} **Demon** {self.bot.get_emoji(878351744877363310)}"
        t_color = discord.Color.from_rgb(201, 0, 0)
    
    if title_var[0] == "Vampire":
        title = f"{self.bot.get_emoji(878351743849758730)} **Vampire** {self.bot.get_emoji(878351743338025031)}"
        t_color = discord.Color.from_rgb(68, 68, 68)
    
    if title_var[0] == "Frost":
        title = f"{self.bot.get_emoji(631204093620256768)} **Frost King**"
        t_color = discord.Color.from_rgb(135, 212, 204)

    if title_var[0] == "King":
        title = f"{self.bot.get_emoji(819685240691884063)} **King**"
        t_color = discord.Color.from_rgb(255, 239, 0)

    
    return title, t_color

async def get_title_options(user, database):
    selection_list = []

    bank_data, stats_data = await get_info_from_database(user, database)
    
    if True:
        none_select = SelectOption(label = "None", value = "none")
        selection_list.append(none_select)

    if stats_data[9] >= 10000:
        md = SelectOption(label = "Medical Director", value = "medical")
        selection_list.append(md)

    if stats_data[1] >= 5000:
        md2 = SelectOption(label = "Kingpin", value = "kingpin")
        selection_list.append(md2)
    
    if king_amount > 0:
        md3 = SelectOption(label = "King", value = "king")
        selection_list.append(md3)

    if fking_amount > 0:
        md4 = SelectOption(label = "Frost King", value = "frostking")
        selection_list.append(md4)

    if angel_amount > 0:
        md5 = SelectOption(label = "Angel", value = "angel")
        selection_list.append(md5)

    if demon_amount > 0:
        md6 = SelectOption(label = "Demon", value = "demon")
        selection_list.append(md6)

    if vampire_amount > 0:
        md7 = SelectOption(label = "Vampire", value = "vampire")
        selection_list.append(md7)


    try:
        if len(selection_list) > 0:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0]], custom_id = "title_select0")
        if len(selection_list) > 1:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1]], custom_id = "title_select1")
        if len(selection_list) > 2:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2]], custom_id = "title_select2")
        if len(selection_list) > 3:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3]], custom_id = "title_select3")
        if len(selection_list) > 4:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4]], custom_id = "title_select4")
        if len(selection_list) > 5:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5]], custom_id = "title_select5")
        if len(selection_list) > 6:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6]], custom_id = "title_select6")
        if len(selection_list) > 7:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7]], custom_id = "title_select7")
        if len(selection_list) > 8:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8]], custom_id = "title_select8")
        if len(selection_list) > 9:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8], selection_list[9]], custom_id = "title_select9")
        if len(selection_list) > 10:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8], selection_list[9], selection_list[10]], custom_id = "title_select10")
        if len(selection_list) > 11:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8], selection_list[9], selection_list[10], selection_list[11]], custom_id = "title_select")
        if len(selection_list) > 12:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8], selection_list[9], selection_list[10], selection_list[11], selection_list[12]], custom_id = "title_select")
        if len(selection_list) > 13:
            title_select = Select(placeholder = "Select Title", options = [selection_list[0], selection_list[1], selection_list[2], selection_list[3], selection_list[4], selection_list[5], selection_list[6], selection_list[7], selection_list[8], selection_list[9], selection_list[10], selection_list[11], selection_list[12], selection_list[13]], custom_id = "title_select")

        return title_select

    except:
        pass
    
    return title_select
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def setup(bot):
    bot.add_cog(EconomyModule(bot))
