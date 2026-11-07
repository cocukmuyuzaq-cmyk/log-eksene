import discord
from discord.ext import commands
import aiohttp
import os
import json
from flask import Flask
from threading import Thread

# ==================== RENDER İÇİN SAHTE WEB SUNUCUSU ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve calisiyor!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ==================== BOT AYARLARI ====================
TOKEN = os.getenv("TOKEN")
ALLOWED_GUILD_ID = 1564299296097050855 # Sadece bu sunucuda calisacak

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# API ADRESLERİ
API_BASE_1 = "https://wazely.vercel.app/api"
API_BASE_2 = "https://wazelyapi.vercel.app/api"
ID_API = "https://prox0959.netlify.app/api/search?id="

# LOGO URL
LOGO_URL = "https://images-ext-1.discordapp.net/external/agYlzG6UyMpfrhR9NA4z8NZcqb89E4cpR7SH2JolLlA/https/cdn.discordapp.com/icons/1564299296097050855/550f4dd8fb04c6e7377b3ecac363689a.webp?format=webp"

# ==================== FİLTRE (TEMİZLEYİCİ) ====================
def temizle(data):
    if isinstance(data, dict):
        return {k: temizle(v) for k, v in data.items() if k.lower() not in ['dev', 'author', 'provider', 'credit']}
    elif isinstance(data, list):
        return [temizle(i) for i in data]
    return data

# ==================== MODAL (GİRİŞ FORMLARI) ====================
class SorguModal(discord.ui.Modal):
    def __init__(self, title, placeholder, api_url):
        super().__init__(title=title)
        self.api_url = api_url
        self.sorgu = discord.ui.TextInput(
            label="Sorgu Değeri",
            placeholder=placeholder,
            required=True,
            max_length=100
        )
        self.add_item(self.sorgu)

    async def on_submit(self, interaction: discord.Interaction):
        # Sunucu kontrolü
        if interaction.guild is None or interaction.guild.id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        deger = self.sorgu.value
        target_url = f"{self.api_url}{deger}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url, timeout=15) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ Sorgu Hatası: HTTP {resp.status}", ephemeral=True)
                        return
                    
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()

            if not data:
                await interaction.followup.send("⚠️ Sonuç bulunamadı.", ephemeral=True)
                return

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)

            if len(sonuc_str) > 1900:
                sonuc_str = sonuc_str[:1900] + "\n... (Devamı kırpıldı)"

            embed = discord.Embed(
                title=f"✅ Sorgu Sonucu: {self.title}",
                description=f"```json\n{sonuc_str}\n```",
                color=0x00E676
            )
            embed.set_thumbnail(url=LOGO_URL)
            embed.set_footer(text="discord.gg/bergmu")

            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ Sonuç özel mesaj (DM) olarak gönderildi!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ Size DM gönderemiyorum. Lütfen DM kutunuzu açın.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Beklenmeyen Hata: {str(e)}", ephemeral=True)

class BosSorguModal(discord.ui.Modal):
    def __init__(self, title, api_url):
        super().__init__(title=title)
        self.api_url = api_url

    async def on_submit(self, interaction: discord.Interaction):
        # Sunucu kontrolü
        if interaction.guild is None or interaction.guild.id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=15) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ Sorgu Hatası: HTTP {resp.status}", ephemeral=True)
                        return
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()

            if not data:
                await interaction.followup.send("⚠️ Sonuç bulunamadı.", ephemeral=True)
                return

            temiz_data = temizle(data)
            sonuc_str = json.dumps(temiz_data, indent=2, ensure_ascii=False) if isinstance(temiz_data, dict) else str(temiz_data)

            if len(sonuc_str) > 1900:
                sonuc_str = sonuc_str[:1900] + "\n... (Devamı kırpıldı)"

            embed = discord.Embed(
                title=f"✅ Sorgu Sonucu: {self.title}",
                description=f"```json\n{sonuc_str}\n```",
                color=0x00E676
            )
            embed.set_thumbnail(url=LOGO_URL)
            embed.set_footer(text="discord.gg/bergmu")

            try:
                await interaction.user.send(embed=embed)
                await interaction.followup.send("✅ Sonuç özel mesaj (DM) olarak gönderildi!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("❌ Size DM gönderemiyorum. Lütfen DM kutunuzu açın.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Beklenmeyen Hata: {str(e)}", ephemeral=True)

# ==================== MENÜ SEÇENEKLERİ ====================
class SorguSecim(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ID Sorgu (Mail/Veri)", description="Discord ID üzerinden veri sızdırır", value="idsorgu"),
            discord.SelectOption(label="Log Çekme", description="Site loglarını çeker (Örn: sahibinden)", value="log"),
            discord.SelectOption(label="Eczane Sorgu", description="Eczane adından bilgi çeker", value="eczane"),
            discord.SelectOption(label="IP Bilgi", description="IP adresinin konumunu bulur", value="ipinfo"),
            discord.SelectOption(label="DNS Sorgu", description="Domain DNS kayıtlarını çeker", value="dns"),
            discord.SelectOption(label="Bahis Sorgu", description="İsim soyisim ile bahis kaydı arar", value="bahis"),
            discord.SelectOption(label="Plaka Sorgu", description="Plaka üzerinden araç bilgisi bulur", value="plaka"),
            discord.SelectOption(label="MC Bedrock", description="Minecraft Bedrock sunucu durumu", value="bedrock"),
            discord.SelectOption(label="Nitro Üret", description="Rastgele Nitro kodları üretir (Max 100)", value="nitro"),
            discord.SelectOption(label="Exxen Hesap", description="Rastgele Exxen hesabı üretir", value="exxen"),
            discord.SelectOption(label="Predunyam Hesap", description="Rastgele Predunyam hesabı üretir", value="predunyam"),
            discord.SelectOption(label="User Agent", description="Rastgele User-Agent üretir", value="ua"),
            discord.SelectOption(label="CC Gen", description="Rastgele kredi kartı üretir", value="ccgen"),
            discord.SelectOption(label="CC Check", description="Kredi kartı geçerliliğini kontrol eder", value="cccheck"),
            discord.SelectOption(label="Discord Token Check", description="Bot tokenini kontrol eder", value="dctoken"),
            discord.SelectOption(label="Telegram Token Check", description="Telegram tokenini kontrol eder", value="tgtoken"),
        ]
        super().__init__(placeholder="Bir sorgu sistemi seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Sunucu kontrolü
        if interaction.guild is None or interaction.guild.id != ALLOWED_GUILD_ID:
            await interaction.response.send_message("❌ Bu bot sadece özel sunucuda çalışır.", ephemeral=True)
            return

        secim = self.values[0]

        if secim == "idsorgu":
            await interaction.response.send_modal(SorguModal("ID Sorgu", "Discord ID (Örn: 92433932011724800)", ID_API))
        elif secim == "log":
            await interaction.response.send_modal(SorguModal("Log Çekme", "Site adı (Örn: sahibinden)", f"{API_BASE_1}/trlog?site="))
        elif secim == "eczane":
            await interaction.response.send_modal(SorguModal("Eczane Sorgu", "Eczane Adı (Örn: Murat Eczanesi)", f"{API_BASE_1}/eczane?ad="))
        elif secim == "ipinfo":
            await interaction.response.send_modal(SorguModal("IP Bilgi", "IP Adresi (Örn: 1.1.1.1)", f"{API_BASE_1}/ipinfo?ip="))
        elif secim == "dns":
            await interaction.response.send_modal(SorguModal("DNS Sorgu", "Domain (Örn: google.com)", f"{API_BASE_1}/dns?domain="))
        elif secim == "bahis":
            await interaction.response.send_modal(SorguModal("Bahis Sorgu", "İsim Soyisim", f"{API_BASE_1}/bahis?isimsoyisim="))
        elif secim == "plaka":
            await interaction.response.send_modal(SorguModal("Plaka Sorgu", "Plaka Kodu", f"{API_BASE_1}/plaka?plate="))
        elif secim == "bedrock":
            await interaction.response.send_modal(SorguModal("MC Bedrock", "Sunucu IP (Örn: play.site.com)", f"{API_BASE_2}/bedrock?adres="))
        elif secim == "nitro":
            await interaction.response.send_modal(SorguModal("Nitro Üret", "Adet (Örn: 10)", f"{API_BASE_1}/fakeNitro?count="))
        elif secim == "cccheck":
            await interaction.response.send_modal(SorguModal("CC Check", "Kart (Örn: 1111...|11|11|111)", f"{API_BASE_2}/check?data="))
        elif secim == "dctoken":
            await interaction.response.send_modal(SorguModal("Discord Token Check", "Bot Tokeni", f"{API_BASE_2}/dcbottokencheck?token="))
        elif secim == "tgtoken":
            await interaction.response.send_modal(SorguModal("Telegram Token Check", "Bot Tokeni", f"{API_BASE_2}/tgtokencheck?token="))
        elif secim == "exxen":
            await interaction.response.send_modal(BosSorguModal("Exxen Hesap", f"{API_BASE_1}/exxengen"))
        elif secim == "predunyam":
            await interaction.response.send_modal(BosSorguModal("Predunyam Hesap", f"{API_BASE_1}/predunyam"))
        elif secim == "ua":
            await interaction.response.send_modal(BosSorguModal("User Agent", f"{API_BASE_1}/randomuseragent"))
        elif secim == "ccgen":
            await interaction.response.send_modal(BosSorguModal("CC Gen", f"{API_BASE_2}/ccgen"))

# ==================== MENÜ YAPISI ====================
class GenelSorguView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SorguSecim())

# ==================== KOMUT ====================
@bot.event
async def on_ready():
    print(f"✅ Bot hazır: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!logçek | discord.gg/bergmu"))

@bot.command(name="logçek", aliases=["logcek", "log"])
async def logcek(ctx):
    # DM KORUMASI
    if ctx.guild is None:
        return # DM'den yazılırsa hiçbir şey yapma (sessizce yoksay)
    
    # SUNUCU KORUMASI
    if ctx.guild.id != ALLOWED_GUILD_ID:
        return # Yanlış sunucudaysa hiçbir şey yapma

    embed = discord.Embed(
        title="🕵️‍♂️ BergMu Sorgu Paneli",
        description="Aşağıdaki menüden yapmak istediğiniz sorguyu seçin.\nSonuçlar **özel mesaj (DM)** olarak gönderilecektir.",
        color=0x5865F2
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="discord.gg/bergmu")
    
    await ctx.send(embed=embed, view=GenelSorguView())

# ==================== ÇALIŞTIR ====================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: TOKEN bulunamadı!")
    else:
        keep_alive() 
        bot.run(TOKEN)