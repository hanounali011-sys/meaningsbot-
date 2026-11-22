# language: Python 3.10+, file: pseudo_bot_final.py
# pip install discord.py aiohttp
#
# SETUP WORDLISTS (une fois, dans le même dossier) :
#   curl -o words_en.txt https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt
#   curl -o words_fr.txt https://raw.githubusercontent.com/hbenbel/French-Dictionary/master/dictionary/dictionary.txt
#
# puis lancer : python3 pseudo_bot_final.py
# le bot nettoie automatiquement les accents au démarrage

import discord
from discord.ext import commands
import aiohttp
import asyncio
import random
import itertools
import re
import unicodedata
import os
import urllib.request
import ssl

# ── AUTO-SETUP : télécharge les dicos si absents ─────────────────────────────
_WORDLISTS = {
    "words_en.txt": "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
    "words_fr.txt": "https://raw.githubusercontent.com/hbenbel/French-Dictionary/master/dictionary/dictionary.txt",
}
_ctx = ssl.create_default_context()
for _fname, _url in _WORDLISTS.items():
    if not os.path.exists(_fname):
        print(f"[*] Téléchargement {_fname}...")
        try:
            urllib.request.urlretrieve(_url, _fname)
            print(f"[OK] {_fname} téléchargé")
        except Exception as _e:
            print(f"[WARN] Impossible de télécharger {_fname} : {_e} — fallback intégré")

# ── CONFIG ───────────────────────────────────────────────────────────────────
BOT_TOKEN   = "YOUR_BOT_TOKEN_HERE"
USER_TOKEN  = "YOUR_USER_TOKEN_HERE"
CHECK_DELAY = 0.5    # secondes entre chaque check
MAX_RESULTS = 15     # pseudos dispos max par commande
CANDIDATES  = 300    # candidats générés par scan
PARALLEL    = 3      # checks simultanés
PREFIX      = "+"

USER_HEADERS = {
    "Authorization": USER_TOKEN,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ── NETTOYAGE ACCENTS ─────────────────────────────────────────────────────────
def strip_accents(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# ── CHARGEMENT DICOS ─────────────────────────────────────────────────────────
def load_wordlist(path: str, lang: str) -> list[str]:
    if not os.path.exists(path):
        print(f"[WARN] {path} introuvable — utilise le dico intégré {lang}")
        return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        words = []
        for line in f:
            w = strip_accents(line.strip().lower())
            if re.match(r'^[a-z]{3,20}$', w):
                words.append(w)
    result = list(set(words))
    print(f"[*] {lang}: {len(result):,} mots chargés depuis {path}")
    return result

# ── DICO INTÉGRÉ FR (fallback si words_fr.txt absent) ────────────────────────
BUILTIN_FR = list(set([
    "lune","soleil","etoile","ciel","nuage","brume","brouillard","orage","foudre","eclair",
    "pluie","neige","givre","glace","gel","vent","tempete","cyclone","avalanche","montagne",
    "colline","vallee","plaine","desert","foret","jungle","marais","lagune","ocean","mer",
    "lac","riviere","fleuve","torrent","cascade","source","ruisseau","vague","maree","ile",
    "cap","falaise","grotte","caverne","gouffre","abime","cratere","volcan","roche","pierre",
    "sable","boue","terre","argile","cendre","poussiere","fumee","braise","flamme","feu",
    "brasier","charbon","suie","encre","huile","resine","ambre","fleur","rose","lys",
    "tulipe","violette","marguerite","coquelicot","lavande","jasmin","lilas","arbre","chene",
    "sapin","bouleau","erable","peuplier","saule","if","cedre","herbe","mousse","fougere",
    "lierre","ronce","ortie","chardon","bambou","roseau","louve","renard","corbeau","chouette",
    "aigle","faucon","vautour","hibou","pie","merle","serpent","vipere","couleuvre","lezard",
    "gecko","cameleon","crocodile","tortue","grenouille","crapaud","loup","ours","lion","tigre",
    "panthere","jaguar","lynx","puma","guepard","hyene","cerf","biche","chevreuil","sanglier",
    "blaireau","herisson","loutre","castor","taupe","nebule","cosmos","galaxie","comete",
    "meteor","pulsar","quasar","nova","supernova","vide","orbit","eclipse","zenith","nadir",
    "equinoxe","solstice","aurore","crepuscule","infini","ether","plasma","photon","electron",
    "neutron","proton","quantum","atom","ion","flux","eau","metal","bois","obscurite","chaos",
    "ordre","temps","espace","matiere","energie","force","masse","rage","fureur","colere",
    "haine","vengeance","rancune","jalousie","envie","orgueil","arrogance","peur","terreur",
    "angoisse","effroi","horreur","panique","anxiete","doute","desespoir","joie","extase",
    "euphorie","felicite","bonheur","amour","tendresse","compassion","empathie","grace",
    "tristesse","melancolie","nostalgie","regret","chagrin","deuil","peine","larme","douleur",
    "souffrance","calme","serenite","paix","quiete","douceur","harmonie","equilibre","verite",
    "mensonge","illusion","chimere","reve","cauchemar","vision","mirage","fantome","spectre",
    "ame","esprit","conscience","memoire","oubli","eternite","mortalite","destin","hasard",
    "gloire","honneur","honte","infamie","legende","mythe","saga","chronique","oracle","ombre",
    "lumiere","dualite","paradoxe","enigme","mystere","secret","arcane","rituel","magie",
    "forge","acier","lame","epee","bouclier","armure","fleche","arc","dague","lance","tour",
    "chateau","donjon","citadelle","bastion","rempart","fortresse","palais","arene","labyrinthe",
    "noir","blanc","rouge","bleu","vert","jaune","orange","violet","rose","gris","argent",
    "bronze","cuivre","platine","ebene","ivoire","ecarlate","cramoisi","carmin","azur","indigo",
    "turquoise","emeraude","rubis","saphir","amethyste","topaze","onyx","jade","vermeil",
    "vermillon","bordeaux","bourgogne","marine","cobalt","cyan","magenta","ocre","sepia",
    "aube","midi","soir","vespere","nuit","minuit","hier","demain","jadis","jamais","toujours",
    "parfois","souvent","deja","encore","enfin","hiver","printemps","ete","automne","titan",
    "olympe","hades","elysee","tartare","styx","lethe","acheron","erebe","atlas","cronos",
    "zeus","poseidon","aphrodite","artemis","apollon","hermes","ares","odin","thor","loki",
    "freya","tyr","heimdall","baldur","fenrir","midgard","anubis","osiris","isis","horus",
    "thot","sekhmet","bastet","brahma","vishnu","shiva","kali","ganesha","indra","varuna",
    "glitch","pixel","voxel","shader","render","vector","matrix","kernel","daemon","thread",
    "byte","cache","stack","heap","patch","debug","crash","overflow","exploit","cipher",
    "proxy","tunnel","hash","token","beacon","signal","entropie","neon","hologram","cyber",
    "stealth","rogue","revenant","arcade","retro","cassette","vinyle","numerique","binaire",
    "derive","eclat","fracas","fracture","rupture","chute","envol","plongeon","errance","fuite",
    "quete","chasse","traque","poursuite","combat","duel","assaut","siege","raid","embuscade",
    "naufrage","exil","bannissement","redemption","purge","absolution","condamnation","jugement",
    "verdict","torpeur","langueur","apathie","lassitude","ferveur","ardeur","vaillance","bravoure",
    "audace","curiosite","fascination","mepris","dedain","repulsion","degout","culpabilite",
    "remords","vergogne","contrition","repentir","expiation","pardon","absurde","symbole",
    "allegorie","metaphore","parabole","analogie","archetype","paradigme","nexus","vortex",
    "resonance","vibration","frequence","amplitude","transgression","subversion","revolution",
    "evolution","mutation","metamorphose","transformation","sublimation","transcendance",
    "sulfure","mercure","etain","plomb","arsenic","antimoine","bismuth","cobalt","nickel",
    "chrome","titane","tungstene","osmium","iridium","rhodium","palladium","beryllium","lithium",
    "cesium","rubidium","ozone","azote","argon","helium","neon","krypton","xenon","radon",
    "nacre","perle","opalin","irise","mordore","anthracite","ardoise","taupe","beige","creme",
    "vanille","caramel","noisette","marron","aubergine","framboise","cerise","fraise","corail",
    "saumon","peche","abricot","citron","chartreuse","olive","kaki","sauge","menthe","pistache",
    "rouille","instant","moment","seconde","minute","fugace","ephemere","transitoire","permanent",
    "immuable","perpetuel","immemorial","ancestral","primordial","hypnos","thanatos","eros",
    "morphee","nemesis","tyche","moira","clotho","lachesis","atropos","chronos","dionysos",
    "demeter","persephone","enki","enlil","inanna","marduk","ishtar","gilgamesh","enkidu",
    "quetzalcoatl","tezcatlipoca","tlaloc","coatlicue","amaterasu","susanoo","tsukuyomi",
    "izanagi","izanami","raijin","fujin","inari","cernunnos","lugh","dagda","morrigan","brigid",
    "dragon","phoenix","griffon","hydre","chimere","basilic","kraken","leviathan","behemoth",
    "banshee","valkyrie","berserker","paladin","druide","chaman","necromancien","sorcier",
    "golem","automate","manticore","sphinx","minotaure","centaure","satyre","faune","firmware",
    "bootloader","rootkit","payload","shellcode","dropper","loader","polymorphe","metamorphe",
    "chiffre","encode","obfusque","latence","bande","debit","paquet","trame","socket","port",
    "protocole","algorithme","heuristique","recursion","iteration","boucle","condition","branche",
    "fractal","automate","reseau","neurone","synapse","dendrite","axone","potentiel","impulsion",
    "holographie","interference","diffraction","polarisation","refraction","reflection","emission",
    "absorption","transmission","propagation","ascension","descente","traversee","expedition",
    "peripetie","odyssee","periple","exploration","decouverte","creation","destruction",
    "renaissance","fusion","fission","implosion","explosion","erosion","corrosion","oxydation",
    "decomposition","fermentation","distillation","condensation","evaporation","germination",
    "floraison","maturation","hibernation","dormance","nymphose","marbre","quartz","schiste",
    "basalte","obsidienne","silex","craie","stalactite","delta","estuaire","recif","atoll",
    "geyser","typhon","mousson","simoun","tramontane","mistral","sirocco","bruine","verglas",
    "sequoia","baobab","mangrove","toundra","savane","steppe","taiga","brousse","maquis",
    "baleine","dauphin","requin","pieuvre","meduse","corail","araignee","scorpion","condor",
    "albatros","flamant","pelican","cigogne","hirondelle","rossignol","tourterelle","mustang",
    "bison","caribou","renne","yak","buffle","ibex","chamois","mouflon","varan","astronomie",
    "lunaire","solaire","stellaire","cosmique","interstellaire","galactique","celeste","sideral",
    "apogee","perigee","equinoxe","conjunction","opposition","tachyon","neutrino","boson",
    "quark","lepton","hadron","fermion","gluon","graviton","axion","singularite","antimatiere",
]))

# ── DICO INTÉGRÉ EN (fallback si words_en.txt absent) ────────────────────────
BUILTIN_EN = list(set([
    "moon","sun","star","sky","cloud","mist","fog","storm","thunder","lightning","rain","snow",
    "frost","ice","sleet","wind","gale","blizzard","hail","drizzle","mountain","hill","valley",
    "plain","desert","forest","jungle","swamp","lagoon","ocean","sea","lake","river","stream",
    "torrent","waterfall","spring","brook","wave","tide","island","cape","cliff","cave","cavern",
    "abyss","crater","volcano","ridge","peak","rock","stone","sand","mud","earth","clay","ash",
    "dust","smoke","ember","flame","fire","blaze","coal","soot","ink","oil","resin","amber",
    "tar","flower","rose","lily","tulip","violet","daisy","poppy","lavender","jasmine","lilac",
    "tree","oak","pine","birch","maple","willow","yew","cedar","sequoia","elm","grass","moss",
    "fern","ivy","thorn","nettle","thistle","bamboo","reed","sedge","wolf","fox","raven","crow",
    "owl","eagle","hawk","vulture","magpie","thrush","snake","viper","lizard","gecko","chameleon",
    "crocodile","turtle","frog","toad","newt","bear","lion","tiger","panther","jaguar","lynx",
    "puma","cheetah","hyena","jackal","deer","doe","boar","badger","hedgehog","otter","beaver",
    "mole","shrew","marble","quartz","schist","basalt","obsidian","flint","chalk","stalactite",
    "delta","estuary","reef","atoll","geyser","typhoon","monsoon","simoom","tramontane","mistral",
    "sirocco","drizzle","tundra","savanna","steppe","taiga","shrubland","cactus","algae","lichen",
    "spore","mycelium","fungus","truffle","belladonna","whale","dolphin","shark","octopus",
    "jellyfish","coral","lobster","spider","scorpion","mantis","condor","albatross","flamingo",
    "pelican","stork","swallow","nightingale","warbler","dove","canary","mustang","bison",
    "caribou","reindeer","yak","buffalo","ibex","chamois","monitor","mangrove","redwood","banyan",
    "nebula","cosmos","galaxy","comet","meteor","pulsar","quasar","nova","supernova","void",
    "orbit","eclipse","zenith","nadir","equinox","solstice","aurora","dusk","infinite","aether",
    "plasma","photon","electron","neutron","proton","quantum","atom","ion","flux","warp",
    "singularity","horizon","gravity","dark","matter","antimatter","entropy","vacuum","rift",
    "apogee","perigee","aphelion","perihelion","transit","occultation","conjunction","opposition",
    "tachyon","neutrino","boson","quark","lepton","hadron","fermion","gluon","graviton","axion",
    "water","metal","wood","shadow","light","chaos","order","time","space","energy","force","mass",
    "wave","pulse","spark","surge","static","arc","flux","field","current","charge","sulfur",
    "mercury","tin","lead","arsenic","antimony","bismuth","cobalt","nickel","chromium","titanium",
    "tungsten","osmium","iridium","rhodium","palladium","beryllium","lithium","cesium","rubidium",
    "ozone","nitrogen","argon","helium","neon","krypton","xenon","radon","chlorine","fluorine",
    "rage","fury","wrath","hate","vengeance","grudge","jealousy","envy","pride","arrogance",
    "fear","terror","dread","horror","panic","anxiety","doubt","despair","grief","sorrow","joy",
    "bliss","ecstasy","euphoria","love","tender","mercy","empathy","grace","peace","calm","serene",
    "quiet","still","gentle","soft","harmony","balance","pure","bitter","hollow","numb","broken",
    "shattered","lost","exile","cold","torpor","languor","apathy","weariness","dejection",
    "fervor","ardor","valor","bravery","audacity","intrepid","stoic","resilient","tenacity",
    "curiosity","fascination","wonder","astonishment","bewilderment","perplexity","confusion",
    "contempt","disdain","repulsion","disgust","aversion","loathing","antipathy","hostility",
    "guilt","remorse","shame","regret","contrition","repentance","expiation","forgiveness",
    "longing","yearning","craving","desire","lust","obsession","fixation","compulsion","serenity",
    "tranquility","equanimity","composure","impassivity","detachment","indifference","vacancy",
    "truth","lie","illusion","dream","nightmare","vision","mirage","ghost","specter","shade",
    "soul","spirit","mind","memory","oblivion","eternity","fate","chance","order","glory","honor",
    "shame","legend","myth","saga","oracle","prophecy","omen","rune","blade","steel","shield",
    "arrow","bow","dagger","lance","axe","mace","spear","tower","castle","dungeon","bastion",
    "rampart","fortress","palace","arena","labyrinth","vault","axiom","postulate","theorem",
    "corollary","lemma","hypothesis","conjecture","inference","deduction","induction","symbol",
    "allegory","metaphor","parable","analogy","archetype","paradigm","topos","motif","leitmotif",
    "nexus","vortex","matrix","prism","filter","resonance","vibration","frequency","amplitude",
    "transgression","subversion","revolution","evolution","mutation","metamorphosis","sublimation",
    "transcendence","norm","taboo","ritual","ceremony","rite","sacrament","covenant","oath",
    "doctrine","dogma","heresy","schism","apostasy","orthodoxy","nihilism","absurd","existential",
    "black","white","red","blue","green","gold","silver","gray","violet","crimson","scarlet",
    "azure","indigo","teal","emerald","ruby","sapphire","amethyst","onyx","jade","cobalt","cyan",
    "magenta","ochre","sepia","ivory","ebony","bronze","copper","platinum","vermilion","maroon",
    "navy","slate","charcoal","pearl","obsidian","alabaster","umber","nacre","opaline","iridescent",
    "gilded","smoky","anthracite","taupe","beige","vanilla","caramel","hazel","chestnut","auburn",
    "mahogany","russet","sienna","terracotta","brick","aubergine","raspberry","cherry","strawberry",
    "coral","salmon","peach","apricot","lemon","chartreuse","olive","khaki","sage","mint",
    "pistachio","seafoam","verdigris","patina","rust","oxidized","dawn","noon","midnight","twilight",
    "eve","morning","night","era","epoch","past","future","never","always","often","still","once",
    "winter","spring","summer","autumn","instant","moment","second","minute","decade","century",
    "millennium","aeon","cycle","rhythm","cadence","tempo","pulse","interval","fleeting","ephemeral",
    "transient","permanent","immutable","perpetual","sempiternal","immemorial","ancestral","primordial",
    "north","south","east","west","above","below","beyond","between","within","outside","arctic",
    "sahara","siberia","amazon","himalaya","outback","tundra","haven","refuge","wasteland",
    "frontier","borderland","threshold","crossroads","summit","depths","zenith","nadir","meridian",
    "parallel","equator","tropic","polar","temperate","boreal","austral","lowland","highland",
    "wetland","badland","heathland","moorland","marshland","canyon","gorge","ravine","gully",
    "defile","pass","col","saddle","escarpment","plateau","mesa","butte","peneplain","titan",
    "olympus","hades","elysium","tartarus","styx","lethe","acheron","erebus","atlas","chronos",
    "zeus","poseidon","aphrodite","artemis","apollo","hermes","ares","odin","thor","loki","freya",
    "tyr","heimdall","baldur","fenrir","midgard","anubis","osiris","isis","horus","seth","thoth",
    "ra","amon","sekhmet","bastet","dragon","phoenix","griffin","hydra","chimera","basilisk",
    "kraken","leviathan","behemoth","banshee","valkyrie","berserker","paladin","warlock","sorcerer",
    "necromancer","druid","shaman","oracle","prophet","hypnos","thanatos","eros","morpheus",
    "nemesis","tyche","moira","clotho","lachesis","atropos","nike","iris","aeolus","dionysus",
    "demeter","persephone","hephaestus","hecate","selene","helios","enki","enlil","anu","inanna",
    "marduk","ishtar","gilgamesh","enkidu","shamash","amaterasu","susanoo","tsukuyomi","izanagi",
    "izanami","raijin","fujin","inari","benzaiten","cernunnos","lugh","dagda","morrigan","brigid",
    "cuchulainn","golem","homunculus","automaton","manticore","sphinx","minotaur","centaur","satyr",
    "faun","nymph","selkie","kelpie","leprechaun","brownie","pixie","sprite","undine","sylph",
    "gnome","quetzalcoatl","tezcatlipoca","tlaloc","coatlicue","xolotl","glitch","pixel","voxel",
    "shader","render","vector","matrix","kernel","daemon","thread","byte","cache","stack","heap",
    "patch","debug","crash","overflow","exploit","cipher","proxy","tunnel","hash","salt","token",
    "beacon","signal","noise","entropy","static","neon","hologram","cyber","stealth","rogue",
    "ghost","phantom","wraith","revenant","specter","arcade","retro","cassette","vinyl","analog",
    "digital","binary","hex","null","firmware","bootloader","rootkit","payload","shellcode",
    "dropper","loader","polymorphic","metamorphic","encrypted","encoded","obfuscated","packed",
    "latency","bandwidth","throughput","packet","frame","socket","port","protocol","layer",
    "algorithm","heuristic","recursion","iteration","loop","branch","conditional","fractal",
    "automaton","network","neuron","synapse","dendrite","axon","potential","impulse","holography",
    "interference","diffraction","polarization","refraction","reflection","emission","absorption",
    "transmission","propagation","interface","abstraction","encapsulation","inheritance","node",
    "graph","tree","list","queue","array","drift","shatter","fracture","rupture","fall","flight",
    "plunge","wander","escape","chase","hunt","stalk","clash","duel","assault","siege","raid",
    "ambush","strike","surge","forge","destroy","morph","evolve","mutate","fuse","split","implode",
    "ignite","collapse","wreck","redeem","purge","condemn","descent","ascent","traverse","banish",
    "reclaim","erosion","corrosion","oxidation","decomposition","fermentation","distillation",
    "sublimation","condensation","evaporation","crystallization","germination","flowering","maturation",
    "dormancy","hibernation","metamorphosis","molting","regeneration","oscillation","undulation",
    "dispersion","concentration","convergence","divergence","refraction",
]))

# ── CHARGEMENT PRINCIPAL ──────────────────────────────────────────────────────
print("[*] Chargement des dicos...")
_loaded_fr = load_wordlist("words_fr.txt", "FR")
_loaded_en = load_wordlist("words_en.txt", "EN")

ALL_FR = _loaded_fr if _loaded_fr else BUILTIN_FR
ALL_EN = _loaded_en if _loaded_en else BUILTIN_EN

if not _loaded_fr:
    print(f"[*] FR fallback intégré : {len(ALL_FR):,} mots")
if not _loaded_en:
    print(f"[*] EN fallback intégré : {len(ALL_EN):,} mots")

print(f"[*] Prêt — FR: {len(ALL_FR):,} mots | EN: {len(ALL_EN):,} mots")

# ── VALIDATION PSEUDO DISCORD ─────────────────────────────────────────────────
def is_valid(name: str) -> bool:
    if not (2 <= len(name) <= 32):
        return False
    if not re.match(r'^[a-z0-9][a-z0-9_]*[a-z0-9]$', name):
        return False
    if '__' in name:
        return False
    return True

# ── GÉNÉRATION DE CANDIDATS ───────────────────────────────────────────────────
SUFFIXES = ["", "x", "z", "v", "ix", "oz", "_", "xo", "00", "real", "irl", "og", "0x", "vx"]
PREFIXES_LIST = ["its", "im", "the", "not", "un", "re", "de", "anti", "xo", "pro"]

def build_pool(word_list: list[str], n: int = CANDIDATES) -> list[str]:
    pool = set()
    sample = random.sample(word_list, min(500, len(word_list)))

    for w in sample:
        for s in SUFFIXES:
            pool.add(f"{w}{s}")
        for p in PREFIXES_LIST[:5]:
            pool.add(f"{p}{w}")
            pool.add(f"{p}_{w}")

    pairs = random.sample(sample, min(80, len(sample)))
    for a, b in itertools.combinations(pairs, 2):
        if 4 <= len(a) + len(b) <= 20:
            pool.add(f"{a}{b}")
            pool.add(f"{a}_{b}")

    result = [p for p in pool if is_valid(p)]
    random.shuffle(result)
    return result[:n]

def gen_fr():  return build_pool(ALL_FR)
def gen_en():  return build_pool(ALL_EN)
def gen_mix():
    combined = random.sample(ALL_FR, min(300, len(ALL_FR))) + \
               random.sample(ALL_EN, min(300, len(ALL_EN)))
    return build_pool(combined)

# ── CHECK DISPO (pomelo-attempt, user token) ──────────────────────────────────
async def check_available(session: aiohttp.ClientSession, username: str) -> bool | None:
    url = "https://discord.com/api/v9/users/@me/pomelo-attempt"
    try:
        async with session.post(
            url,
            json={"username": username},
            headers=USER_HEADERS,
            timeout=aiohttp.ClientTimeout(total=5)
        ) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                return not data.get("taken", True)
            elif r.status == 429:
                retry = float(r.headers.get("Retry-After", 3))
                await asyncio.sleep(retry)
                return None
            else:
                return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

async def scan_candidates(candidates: list[str], max_results: int, progress_msg) -> list[str]:
    found = []
    checked = 0
    sem = asyncio.Semaphore(PARALLEL)

    async def check_one(session, username):
        nonlocal checked
        async with sem:
            result = await check_available(session, username)
            checked += 1
            if result is True:
                found.append(username)
                if len(found) % 3 == 0:
                    embed = discord.Embed(
                        title="🔍 Scan en cours...",
                        description=(
                            f"Vérifiés : **{checked}** | Trouvés : **{len(found)}/{max_results}**\n\n"
                            + "\n".join(f"`{p}`" for p in found)
                        ),
                        color=0x5865F2
                    )
                    try:
                        await progress_msg.edit(embed=embed)
                    except Exception:
                        pass
            await asyncio.sleep(CHECK_DELAY)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for username in candidates:
            if len(found) >= max_results:
                break
            tasks.append(asyncio.create_task(check_one(session, username)))
            if len(tasks) >= PARALLEL * 10:
                await asyncio.gather(*tasks)
                tasks = []
                if len(found) >= max_results:
                    break
        if tasks:
            await asyncio.gather(*tasks)

    return found[:max_results]

# ── BOT ───────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"[*] Bot connecté : {bot.user}")
    print(f"[*] Dico actif — FR: {len(ALL_FR):,} | EN: {len(ALL_EN):,}")

async def run_scan(ctx, generator_fn, label: str, color: int):
    embed = discord.Embed(
        title=f"🔍 Génération {label}...",
        description="Scan en cours, patienter...",
        color=color
    )
    msg = await ctx.send(embed=embed)
    candidates = generator_fn()
    embed.title = f"🔍 Scan {label} — {len(candidates)} candidats"
    await msg.edit(embed=embed)
    found = await scan_candidates(candidates, MAX_RESULTS, msg)
    if not found:
        embed = discord.Embed(
            title=f"❌ Aucun pseudo dispo ({label})",
            description="Tous pris ou erreur API. Réessaie.",
            color=0xFF4444
        )
    else:
        chunks = [found[i:i+10] for i in range(0, len(found), 10)]
        lines = "\n".join("  ".join(f"`{p}`" for p in chunk) for chunk in chunks)
        embed = discord.Embed(
            title=f"✅ Pseudos dispos {label} ({len(found)})",
            description=lines,
            color=color
        )
        embed.set_footer(
            text=f"{len(candidates)} candidats scannés | "
                 f"Dico : {len(ALL_FR):,} FR + {len(ALL_EN):,} EN"
        )
    await msg.edit(embed=embed)

@bot.command(name="meaningfr")
async def meaning_fr(ctx):
    await run_scan(ctx, gen_fr, "🇫🇷 FR", 0x0055A4)

@bot.command(name="meaningen")
async def meaning_en(ctx):
    await run_scan(ctx, gen_en, "🇬🇧 EN", 0xC8102E)

@bot.command(name="meaningmix")
async def meaning_mix(ctx):
    await run_scan(ctx, gen_mix, "🌐 MIX", 0x9B59B6)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📖 Commandes",
        description=(
            "`+meaningfr` — pseudos FR dispos\n"
            "`+meaningen` — pseudos EN dispos\n"
            "`+meaningmix` — combos FR×EN dispos\n"
        ),
        color=0x5865F2
    )
    embed.set_footer(
        text=f"Dico : {len(ALL_FR):,} FR + {len(ALL_EN):,} EN | Max {MAX_RESULTS} résultats"
    )
    await ctx.send(embed=embed)

bot.run(BOT_TOKEN)
