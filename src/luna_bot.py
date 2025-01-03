import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import os
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import asyncio
from discord import FFmpegPCMAudio
from googlesearch import search
import random
import logging

# Lataa ympäristömuuttujat
load_dotenv()

# Asetukset
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
intents.message_content = True

# ----- YLEISET KOMENNOT -----
@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} on käynnissä!")
    await bot.change_presence(activity=discord.Game(name="Hallinnoi palvelinta!"))

@bot.command()
async def komennot(ctx):
    """Näytä käytettävissä olevat komennot."""
    if ctx.author.id == OWNER_ID or ctx.author.guild_permissions.administrator:
        admin_komennot = """
        **Admin-komennot:**
        - !ban [käyttäjä] [syy] - Bannaa käyttäjä.
        - !kick [käyttäjä] [syy] - Potkaise käyttäjä.
        - !mute [käyttäjä] [syy] - Mykistä käyttäjä.
        - !unmute [käyttäjä] - Poista mykistys.
        - !kanava [toiminto] - Luo tai hallinnoi kanavia.
        - !musiikki [YouTube-linkki] - Soita musiikkia.
        - !pysäytä - Lopeta musiikki.
        - !haku [kysymys] - Hae tietoa netistä.
        - !peli - Pelaa minipelejä.
        - !liity - Liity puhekanavalle ja soita musiikkia.
        - !kanava - luo tai hallinnoi kanavia - !kanava [luo/poista] [nimi]".
        - !jono - Näytä soittolista ja sen kappaleet.
        - !play_next - soittaa seuraavan kappaleen jonosta.
        - !skip - hyppää seuraavaan kappaleeseen. 
        - !pause -  keskeytä musiikki
        - !resume - jatka keskeytettyä musiikkia
        - !stop - lopettaa musiikin soittamisen ja irrottautuu äänikanavalta.
        - !poista - Poistaa tietyn määrän viestejä nykyisestä kanavasta.
        - !slowmode(time) - Lisää kanavalle slowmode.
        """
        await ctx.send(admin_komennot)
    else:
        yleiset_komennot = """
        **Käyttäjäkomennot:**
        - !musiikki [YouTube-linkki] - Soita musiikkia.
        - !pysäytä - Lopeta musiikki.
        - !haku [kysymys] - Hae tietoa netistä.
        - !peli - Pelaa minipelejä.
        - !liity - Liity puhekanavalle ja soita musiikkia.
        - !jono - Näytä soittolista ja sen kappaleet.
        - !play_next - soittaa seuraavan kappaleen jonosta.
        - !skip - hyppää seuraavaan kappaleeseen. 
        - !pause -  keskeytä musiikki
        - !resume - jatka keskeytettyä musiikkia
        - !stop - lopettaa musiikin soittamisen ja irrottautuu äänikanavalta.
        """
        await ctx.send(yleiset_komennot)

# ----- ADMIN-KOMENNOT -----
@bot.command()
@has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Bannaa käyttäjä."""
    await member.ban(reason=reason)
    await ctx.send(f"**{member.name}** bannattiin. Syy: {reason}")

@bot.command()
@has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Potkaise käyttäjä."""
    await member.kick(reason=reason)
    await ctx.send(f"**{member.name}** potkaistiin. Syy: {reason}")

@bot.command()
@has_permissions(administrator=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    """Mykistä käyttäjä."""
    guild = ctx.guild
    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f"**{member.name}** mykistettiin. Syy: {reason}")

@bot.command()
@has_permissions(administrator=True)
async def unmute(ctx, member: discord.Member):
    """Poista käyttäjän mykistys."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"**{member.name}** mykistys poistettiin.")

# ---- ILMOITUKSET ---

# Aseta tervetulokanavan ID tähän 
WELCOME_CHANNEL_ID = 1177975111593246722  

@bot.event
async def on_member_join(member):
    """Käsittelee, kun uusi jäsen liittyy palvelimelle."""
    # Lähetetään yksityisviesti liittyneelle henkilölle
    try:
        await member.send(
            f"Tervetuloa, {member.name}, palvelimelle!\n\n"
            "Olemme iloisia, että liityit. Tässä on muutama tärkeä tieto:\n"
            "- **Säännöt:** Muista olla kunnioittava ja noudattaa sääntöjä.\n"
            "- **Komennot:** Voit käyttää bottia erilaisilla komennoilla. Kokeile `!komennot` nähdäksesi, mitä voit tehdä.\n"
            "- **Tuki:** Jos tarvitset apua, ota yhteyttä ylläpitoon tai kysy yleisellä kanavalla.\n\n"
            "Nauti ajastasi täällä!"
        )
    except discord.Forbidden:
        print(f"En voinut lähettää yksityisviestiä käyttäjälle {member.name}.")

    # Ilmoitetaan tervetulokanavalla
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"Tervetuloa palvelimelle, {member.mention}! 👋")
    else:
        print("Tervetulokanavaa ei löytynyt. Tarkista WELCOME_CHANNEL_ID.")

# ---- ROOLIJAKO -----

@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name="YourRoleName")
    member = guild.get_member(payload.user_id)
    if member and role:
        await member.add_roles(role)


# ---- SLOW MODE -----

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slow mode is now set to {seconds} seconds.")
        
# ----- MUSIIKKI ----- 

# Asetetaan debug-lokitus
logging.basicConfig(level=logging.DEBUG)

# Soittolista
music_queue = []

# Asetetaan FFmpeg-optioita
ffmpeg_options = {
    'options': '-vn',  # Ei videota
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"  # Yhdistä aina uudelleen
}

# Komento musiikin hakemiseen ja lisäämiseen soittolistalle
@bot.command()
async def musiikki(ctx, *, search: str):
    """Hae musiikkia YouTubesta nimellä ja lisää se soittolistalle."""
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("Sinun täytyy olla puhekanavalla käyttääksesi tätä komentoa.")
        return

    if ctx.voice_client is None:
        await voice_channel.connect()

    # Etsi YouTube-haku käyttäen yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,  # Ei lataa soittolistaa
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)
            url = info['entries'][0]['url']
            title = info['entries'][0]['title']

            # Lisää kappale soittolistalle
            music_queue.append({'url': url, 'title': title})
            await ctx.send(f"Kappale {title} lisätty jonoon.")

        # Soita seuraava kappale, jos ei ole muuta meneillään
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)

    except youtube_dl.DownloadError as e:
        logging.error(f"Virhe YouTube-hakua suoritettaessa: {e}")
        await ctx.send("Musiikin hakeminen epäonnistui. Yritä uudelleen.")
    except Exception as e:
        logging.error(f"Virhe musiikin lisäämisessä: {e}")
        await ctx.send("Jokin meni pieleen musiikin lisäämisessä. Yritä uudelleen.")

# Komento soittolistalle
@bot.command()
async def jono(ctx):
    """Näytä soittolista ja sen kappaleet."""
    if not music_queue:
        await ctx.send("Soittolistalla ei ole musiikkia.")
    else:
        queue = "\n".join([f"{index + 1}. {song['title']}" for index, song in enumerate(music_queue)])
        await ctx.send(f"Soittolista:\n{queue}")

# Komento musiikin soittamiseen
async def play_next(ctx):
    """Soita seuraava kappale jonosta."""
    if not music_queue:
        await ctx.send("Soittolista on tyhjä. Botti poistui kanavalta.")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        return

    song = music_queue.pop(0)
    url = song['url']
    title = song['title']

    voice_client = ctx.voice_client

    # Tarkista, että botti on yhä yhteydessä kanavaan
    if not voice_client.is_connected():
        await ctx.send("Botti ei ole enää yhteydessä kanavalle.")
        return

    def after_playing(error):
        """Kutsutaan, kun kappaleen soitto on päättynyt."""
        if error:
            logging.error(f"Virhe musiikin soittamisessa: {error}")
        # Soita seuraava kappale
        asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

    try:
        # Soita kappale
        audio_source = FFmpegPCMAudio(url, options='-vn')  # Lisää '-vn', jotta video ei yritä ladata
        voice_client.play(audio_source, after=after_playing)
        await ctx.send(f"Soitetaan: {title}")
    except Exception as e:
        logging.error(f"Virhe FFmpeg-prosessissa: {e}")
        await ctx.send(f"Virhe kappaleen soittamisessa: {title}")
        await play_next(ctx)  # Yritetään soittaa seuraava kappale

# Komento musiikin keskeyttämiseen (skip)
@bot.command()
async def skip(ctx):
    """Hyppää nykyinen kappale ja soita seuraava."""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Kappale ohitettu.")
        await play_next(ctx)
    else:
        await ctx.send("Ei ole kappaleita soitettavana.")

# Komento musiikin lopettamiseen ja kanavalta poistumiseen
@bot.command()
async def stop(ctx):
    """Lopettaa musiikin soittamisen ja irrottautuu äänikanavalta."""
    voice_client = ctx.voice_client
    if voice_client:
        voice_client.stop()
        await voice_client.disconnect()
        await ctx.send("Musiikin soittaminen lopetettu ja botti poistui kanavalta.")
    else:
        await ctx.send("En ole liitetty äänikanavalle.")


# ----- PELIT ----- 
@bot.command()
async def peli(ctx):
    """Minipelejä."""
    games = """
    **Valitse peli:**
    - 1. Kolikon heitto: !kolikko
    """
    await ctx.send(games)

@bot.command()
async def kolikko(ctx):
    """Kolikon heitto."""
    import random
    result = random.choice(["Kruuna", "Klaava"])
    await ctx.send(f"Kolikko näyttää: {result}")

# ----- HAKU ----- 
@bot.command()
async def haku(ctx, *, kysymys):
    """Hae tietoa netistä ja jaa tulos yleisessä kanavassa."""
    try:
        # Suoritetaan Google-haku
        hakutulokset = search(kysymys, num_results=3)  # Hae 3 tulosta
        if not hakutulokset:
            await ctx.send("Hakutuloksia ei löytynyt.")
            return

        # Luo vastausviesti
        vastaus = f"**Haku tuloksille:** {kysymys}\n\n" + "\n".join([f"{i+1}. {tulos}" for i, tulos in enumerate(hakutulokset)])
        
        # Lähetetään viesti kanavaan
        yleinen_kanava = discord.utils.get(ctx.guild.channels, name="yleinen")  # Korvaa kanavan nimi oikealla
        if yleinen_kanava:
            await yleinen_kanava.send(vastaus)
        else:
            await ctx.send("Yleistä kanavaa ei löydetty. Lähetetään tulokset tähän.")
            await ctx.send(vastaus)
    except Exception as e:
        await ctx.send(f"Haku epäonnistui: {e}")

# ----- KANAVAN HALLINTA ----- 
@bot.command()
@has_permissions(administrator=True)
async def kanava(ctx, toiminto: str, *, nimi=None):
    """Luo tai hallinnoi kanavia."""
    if toiminto == "luo":
        await ctx.guild.create_text_channel(name=nimi)
        await ctx.send(f"Tekstikanava **{nimi}** luotu.")
    elif toiminto == "poista" and nimi:
        channel = discord.utils.get(ctx.guild.channels, name=nimi)
        if channel:
            await channel.delete()
            await ctx.send(f"Kanava **{nimi}** poistettu.")
    else:
        await ctx.send("Käytä: !kanava [luo/poista] [nimi]")

# POISTA VIESTEJÄ
@bot.command()
@commands.has_permissions(manage_messages=True)
async def poista(ctx, määrä: int):
    """Poistaa tietyn määrän viestejä nykyisestä kanavasta."""
    if määrä <= 0:
        await ctx.send("Määrän täytyy olla suurempi kuin 0.")
        return

    try:
        deleted = await ctx.channel.purge(limit=määrä)
        await ctx.send(f"Poistettu {len(deleted)} viestiä.", delete_after=5)  # Tämä viesti poistetaan 5 sekunnin jälkeen.
    except Exception as e:
        await ctx.send(f"Virhe viestien poistamisessa: {e}")


# ----- LIITY PUHEKANAVALLE ----- 
@bot.command()
async def liity(ctx):
    """Liity puhekanavalle ja soita musiikkia kaikille."""
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("Sinun täytyy olla puhekanavalla, jotta voin liittyä siihen.")
        return

    vc = await voice_channel.connect()
    await ctx.send("Botti liittyi puhekanavalle ja soittaa musiikkia!")

# Käynnistä botti
bot.run(TOKEN)
