# language: Python 3.10+, file: pseudo_bot_final.py
# pip install discord.py aiohttp

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
import time
import csv
import math
import string
import traceback
from datetime import datetime
from collections import defaultdict

# ── AUTO-SETUP ────────────────────────────────────────────────────────────────
_WORDLISTS = {
    "words_en.txt":     "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
    "words_fr.json":    "https://raw.githubusercontent.com/words/an-array-of-french-words/master/index.json",
    "words_cities.csv": "https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv",
}
for _fname, _url in _WORDLISTS.items():
    if not os.path.exists(_fname):
        print(f"[*] Téléchargement {_fname}...")
        try:
            urllib.request.urlretrieve(_url, _fname)
            print(f"[OK] {_fname}")
        except Exception as _e:
            print(f"[WARN] {_fname} : {_e}")

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ.get("BOT_TOKEN",  "").strip()
USER_TOKEN  = os.environ.get("USER_TOKEN", "").strip()
CHECK_DELAY = 0.3
MAX_RESULTS = 15
PARALLEL    = 5
PREFIX      = "+"
START_TIME  = time.time()
OWNER_ID    = int(os.environ.get("OWNER_ID", "0") or 0)


def get_user_headers():
    return {
        "Authorization": USER_TOKEN,
        "Content-Type":  "application/json",
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }


# ── ÉTAT GLOBAL ───────────────────────────────────────────────────────────────
STATS        = {"scans": 0, "found": 0, "checked": 0, "commands": 0}
WATCHLIST    = {}
FAVORITES    = defaultdict(list)
HISTORY      = defaultdict(list)
LEADERBOARD  = defaultdict(int)
FAV_NOTES    = defaultdict(dict)
FAV_TAGS     = defaultdict(dict)
WATCH_PAUSED = set()
CONFIG       = {"max_results": MAX_RESULTS, "check_delay": CHECK_DELAY, "parallel": PARALLEL}
TOTAL_CMDS   = 0
RATE         = {"until": 0.0}   # fin du blocage 429 sur la route pseudo

# ── COULEURS ──────────────────────────────────────────────────────────────────
C = {
    "dark":0x2B2D31,"fr":0x0055A4,"en":0xED4245,"mix":0x9B59B6,
    "city":0x27AE60,"og":0xF1C40F,"aesthetic":0xE91E8C,
    "short":0x1ABC9C,"check":0x57F287,"error":0xFF4444,
    "warn":0xFEE75C,"info":0x5865F2,"watch":0xFF9500,
    "stats":0x2ECC71,"myth":0xA084E8,"astro":0x1A1A2E,
    "nature":0x228B22,"animal":0xD2691E,"food":0xFF6B35,
    "sport":0xFF4500,"science":0x00CED1,"music":0xFF1493,
    "game":0x7B2D8B,"lucky":0xFFAA00,"dark2":0x1A1A2E,
    "neon":0x39FF14,"retro":0xFF6EC7,"pirate":0x8B4513,
    "cyber":0x00FFFF,"magic":0xBF40BF,"war":0x8B0000,
    "ocean":0x006994,"space":0x0D0221,"fire":0xFF4500,
    "ice":0xADD8E6,"forest":0x228B22,"desert":0xC2B280,
    "storm":0x607D8B,"viking":0x795548,"samurai":0xF44336,
    "ninja":0x212121,"aztec":0xFF5722,"celtic":0x4CAF50,
    "egyptian":0xFFC107,"roman":0x9E9E9E,"spartan":0xF44336,
    "gem":0xE91E63,"metal":0x78909C,"color":0xFF9800,
    "admin":0xFF0000,"profile":0x9C27B0,
}

# ── THÈMES ────────────────────────────────────────────────────────────────────
THEMES = {
    "mythologie": [
        "zeus","hera","poseidon","demeter","athena","apollo","artemis","ares","aphrodite",
        "hephaestus","hermes","dionysus","hades","persephone","nike","nemesis","tyche","eros",
        "psyche","iris","hecate","selene","helios","nyx","erebus","chronos","chaos","gaia",
        "uranus","titan","atlas","prometheus","epimetheus","pandora","orpheus","eurydice",
        "narcissus","echo","medusa","perseus","theseus","achilles","odysseus","agamemnon",
        "odin","thor","loki","freya","frigg","baldur","tyr","heimdall","skadi","njord","mimir",
        "fenrir","sleipnir","anubis","osiris","isis","horus","ra","thoth","set","nephthys",
        "bastet","sekhmet","ptah","sobek","amun","brahma","vishnu","shiva","lakshmi","durga",
        "kali","ganesh","hanuman","indra","agni","vayu","varuna","surya","chandra","yama",
    ],
    "astro": [
        "andromeda","orion","pegasus","cassiopeia","perseus","cygnus","lyra","aquila",
        "scorpius","sagittarius","capricorn","aquarius","pisces","aries","taurus","gemini",
        "cancer","leo","virgo","libra","draco","hercules","bootes","ophiuchus","centaurus",
        "sirius","vega","arcturus","rigel","betelgeuse","aldebaran","spica","antares","pollux",
        "deneb","regulus","altair","procyon","achernar","hadar","mimosa","neutron","pulsar",
        "quasar","nebula","galaxy","cosmos","stellar","solar","lunar","orbital","eclipse",
        "solstice","equinox","zenith","nadir","apogee","perigee","aurora","mercury","venus",
        "mars","jupiter","saturn","uranus","neptune","pluto","ceres","eris","sedna","chiron",
    ],
    "nature": [
        "storm","thunder","lightning","blizzard","typhoon","tornado","hurricane","monsoon",
        "drought","wildfire","avalanche","earthquake","volcano","tsunami","glacier","iceberg",
        "tundra","taiga","steppe","savanna","prairie","wetland","mangrove","estuary","delta",
        "canyon","gorge","ravine","cliff","plateau","mesa","dune","oasis","spring","geyser",
        "waterfall","rapid","whirlpool","eddy","current","tide","wave","surge","coral","reef",
        "kelp","algae","lichen","moss","fern","sequoia","redwood","cypress","juniper","spruce",
        "thistle","nettle","reed","clover","heather","gorse","primrose","bluebell","snowdrop",
    ],
    "animal": [
        "wolf","fox","raven","owl","eagle","hawk","falcon","condor","pelican","albatross",
        "flamingo","penguin","puffin","osprey","kestrel","lion","tiger","panther","jaguar",
        "leopard","cheetah","lynx","puma","ocelot","serval","caracal","bear","grizzly","polar",
        "arctic","timber","iberian","maned","coyote","jackal","dhole","dingo","raccoon","otter",
        "badger","wolverine","marten","fisher","mink","ermine","ferret","mongoose","meerkat",
        "whale","dolphin","porpoise","orca","narwhal","beluga","dugong","manatee","shark","ray",
        "swordfish","marlin","barracuda","tuna","salmon","cobra","mamba","viper","python","boa",
        "gecko","iguana","monitor","komodo","chameleon","anole","skink",
    ],
    "food": [
        "matcha","saffron","cardamom","cinnamon","turmeric","paprika","cumin","coriander",
        "fennel","anise","clove","nutmeg","vanilla","cocoa","coffee","espresso","cappuccino",
        "latte","mocha","chai","mochi","tempura","ramen","udon","soba","pho","bibimbap",
        "kimchi","bulgogi","sushi","sashimi","nigiri","maki","temaki","onigiri","gyoza",
        "paella","risotto","gnocchi","fettuccine","linguine","tiramisu","cannoli","gelato",
        "macaron","croissant","brioche","churros","empanada","ceviche","guacamole","salsa",
        "tandoori","biryani","korma","masala","dal","paneer","samosa","falafel","hummus",
        "tabbouleh","shawarma","kebab","dolma","tzatziki",
    ],
    "sport": [
        "sprint","marathon","triathlon","decathlon","biathlon","pentathlon","slalom","downhill",
        "halfpipe","velodrome","peloton","breakaway","drafting","climbing","judo","karate",
        "taekwondo","aikido","wrestling","boxing","surfing","kitesurfing","windsurfing",
        "bouldering","toprope","archery","fencing","shooting","equestrian","dressage","rowing",
        "kayaking","canoeing","rafting","sailing","yachting","polo","lacrosse","cricket",
        "rugby","handball","volleyball","basketball","football","soccer","hockey","baseball",
        "tennis","badminton","squash","racquetball","pingpong","padel","pickleball","frisbee",
    ],
    "science": [
        "neutron","proton","electron","photon","quark","lepton","hadron","boson","fermion",
        "gluon","graviton","axion","neutrino","muon","tauon","entropy","enthalpy","catalyst",
        "substrate","enzyme","polymer","monomer","isomer","enantiomer","osmosis","diffusion",
        "convection","conduction","radiation","induction","quantum","relativity","uncertainty",
        "superposition","entanglement","decoherence","plasma","condensate","superconductor",
        "semiconductor","genome","proteome","metabolome","transcriptome","epigenome",
        "mitosis","meiosis","apoptosis","autophagy","neuron","synapse","axon","dendrite",
        "myelin","cortex","hippocampus","amygdala","algorithm","recursion","polymorphism",
    ],
    "music": [
        "allegro","andante","adagio","presto","vivace","moderato","larghetto","lento",
        "fortissimo","pianissimo","mezzo","forte","piano","crescendo","diminuendo","staccato",
        "legato","tenuto","marcato","fermata","tremolo","vibrato","glissando","arpeggio",
        "chord","cadence","interval","octave","semitone","tritone","sonata","concerto",
        "symphony","overture","prelude","fugue","cantata","nocturne","etude","ballade",
        "rhapsody","intermezzo","caprice","riff","groove","lick","hook","bridge","chorus",
        "blues","jazz","reggae","ska","funk","soul","gospel","swing","bebop","ambient",
        "techno","house","trance","dubstep","hardcore","grunge","metal","punk","indie",
    ],
    "game": [
        "respawn","nexus","rune","glyph","cipher","arcane","invoke","summon","conjure",
        "phantom","wraith","specter","revenant","shade","banshee","lich","necromancer",
        "paladin","crusader","templar","inquisitor","arbiter","sentinel","guardian","warden",
        "assassin","rogue","shadow","stalker","lurker","predator","hunter","tracker",
        "berserker","barbarian","marauder","ravager","destroyer","obliterator","annihilator",
        "mage","wizard","sorcerer","warlock","witch","shaman","druid","elementalist",
        "archer","ranger","sniper","marksman","sharpshooter","gunslinger","rifleman",
        "healer","cleric","priest","oracle","prophet","seer","mystic","sage","scholar",
        "tank","bruiser","vanguard","bulwark","bastion","fortress","citadel","rampart",
    ],
    "pirate": [
        "buccaneer","corsair","privateer","marauder","plunderer","pillager","raider",
        "swashbuckler","cutthroat","scoundrel","rogue","brigand","outlaw","bandit",
        "anchor","compass","sextant","astrolabe","galleon","frigate","brigantine","schooner",
        "sloop","ketch","mainsail","foresail","jibsail","topsail","spanker","mizzen",
        "starboard","larboard","windward","leeward","stern","bow","keel","hull",
        "doubloon","treasure","booty","plunder","loot","spoils","prize","bounty",
        "kraken","leviathan","siren","mermaid","selkie","kelpie","charybdis","scylla",
        "jollyroger","cutlass","flintlock","cannon",
    ],
    "cyber": [
        "overflow","exploit","payload","shellcode","rootkit","malware","ransomware","spyware",
        "keylogger","trojan","botnet","worm","virus","backdoor","dropper","loader","stager",
        "socket","packet","frame","datagram","protocol","cipher","hash","digest","entropy",
        "heap","stack","kernel","userland","syscall","interrupt","hook","injection","hijack",
        "spoofing","sniffing","fuzzing","fuzzer","scanner","crawler","proxy","tunnel","pivot",
        "lateral","escalate","persist","evade","obfuscate","bytecode","opcode","disassemble",
        "decompile","unpack","decrypt","patch","beacon","cobalt","stager","reflective",
        "hollow","process","thread","token","impersonate","kerberos","ntlm","lsass","shadow",
    ],
    "magic": [
        "arcanum","grimoire","sigil","rune","glyph","ward","seal","bind","curse","hex",
        "charm","enchant","bewitch","beguile","glamour","illusion","phantasm","mirage",
        "abjuration","conjuration","divination","enchantment","evocation","necromancy",
        "transmutation","astral","ethereal","liminal","planar","dimensional","temporal",
        "cauldron","chalice","athame","wand","staff","orb","crystal","mirror","candle",
        "solstice","equinox","sabbat","esbat","coven","circle","pentacle","triquetra",
        "elemental","earth","water","fire","air","spirit","void","shadow","light",
        "druid","wicca","shaman","mystic","seer","oracle","prophet","sibyl","pythia",
        "alchemy","elixir","quintessence","azoth","tarot","ogham","kabbalah","geomancy",
    ],
    "dark": [
        "void","abyss","shade","dusk","umbra","penumbra","eclipse","midnight","twilight",
        "gloom","murk","shadow","darkness","obscure","obscurity","opaque","dim","dusky",
        "noir","sable","pitch","jet","coal","ebony","onyx","raven","crow","nightfall",
        "nightshade","nightcrawler","nightmare","wraith","specter","phantom","ghost","shade",
        "revenant","banshee","lich","necromancer","undead","cursed","damned","forsaken",
        "fallen","broken","shattered","hollow","empty","barren","desolate","wasteland",
        "ruin","decay","entropy","oblivion","nothing","null","zero","dead","death","end",
    ],
    "fire": [
        "ember","blaze","inferno","ash","cinder","spark","flame","ignite","kindle","torch",
        "pyre","conflagration","wildfire","bonfire","campfire","hearth","forge","furnace",
        "kiln","crucible","molten","magma","lava","volcano","eruption","pyroclast","tephra",
        "scorch","sear","char","brand","burn","incinerate","immolate","combust","smolder",
        "flicker","glimmer","glow","radiate","phosphor","incandescent","luminous","fiery",
        "ardent","fervent","blazing","scorching","searing","torrid","sweltering","broiling",
        "hellfire","dragonfire","solar","nova","supernova","plasma","fusion","fission",
    ],
    "ice": [
        "frost","glacial","arctic","frozen","permafrost","tundra","snowflake","blizzard",
        "sleet","hail","icicle","glacier","iceberg","floe","pack","shelf","cap","sheet",
        "cryogenic","absolute","zero","kelvin","celsius","frigid","gelid","freezing","polar",
        "boreal","subarctic","alpine","subalpine","montane","snowline","treeline","frostline",
        "permafrost","cryosphere","cryogenic","cryonics","cryopreservation","cryotherapy",
        "hypothermia","frostbite","snowblind","whiteout","avalanche","icestorm","snowstorm",
        "crystal","quartz","diamond","sapphire","aquamarine","topaz","zircon","moonstone",
    ],
    "ocean": [
        "abyss","tide","coral","drift","current","surge","swell","breaker","whitecap",
        "tsunami","tidal","wave","spray","foam","brine","salt","kelp","reef","atoll","shoal",
        "depth","fathom","league","knot","nautical","maritime","pelagic","benthic","abyssal",
        "hadal","neritic","littoral","intertidal","subtidal","supratidal","estuary","lagoon",
        "fjord","sound","strait","channel","passage","cove","bay","gulf","sea","ocean",
        "pacific","atlantic","indian","arctic","southern","mediterranean","caribbean","coral",
        "whale","dolphin","shark","octopus","jellyfish","squid","nautilus","cuttlefish",
    ],
    "storm": [
        "gale","surge","squall","typhoon","cyclone","vortex","maelstrom","tempest","deluge",
        "downpour","cloudburst","torrent","cascade","torrent","flood","inundation","overflow",
        "billow","eddy","whirlpool","whorl","spiral","helix","gyration","rotation","revolution",
        "turbulence","convection","updraft","downdraft","windshear","microburst","derecho",
        "haboob","sirocco","mistral","tramontane","bora","foehn","chinook","scirocco","levante",
        "ponente","gregale","libeccio","ostro","tramontana","etesian","meltemi","shamal",
        "harmattan","simoom","khamsin","haboob","dust","storm","sandstorm","blizzard","whiteout",
    ],
    "viking": [
        "ragnar","bjorn","sigurd","freyr","gunnar","leif","eric","ivar","rollo","halfdan",
        "olaf","hakon","sven","thorvald","gudrid","eirik","floki","ragnhild","ingrid","astrid",
        "valhalla","asgard","midgard","jotunheim","niflheim","muspelheim","alfheim","svartalfheim",
        "yggdrasil","bifrost","mjolnir","gungnir","draupnir","gleipnir","skidbladnir","naglfar",
        "berserker","huscarl","jarl","chieftain","hersir","thrall","karle","drengr","vikingr",
        "longship","drakkar","knorr","snekkja","karfi","faering","langskip","skiplag",
        "skald","rune","futhark","blot","seidr","galdr","volva","norns","wyrd","orlog",
    ],
    "samurai": [
        "ronin","katana","bushido","kensei","shogun","daimyo","hatamoto","bannerman",
        "seppuku","harakiri","iaido","kenjutsu","battojutsu","ninjutsu","taijutsu","bojutsu",
        "naginata","yari","tetsubo","kanabo","tanto","wakizashi","nodachi","odachi","tachi",
        "kabuto","menpo","kote","suneate","haidate","sode","nodowa","kikko","haramaki",
        "zen","rectitude","courage","benevolence","respect","honesty","honor",
        "loyalty","devotion","sincerity","wisdom","compassion","justice","righteousness",
        "sakura","torii","shrine","temple","dojo","tatami","shoji","fusuma","engawa",
    ],
    "aztec": [
        "quetzal","coatl","xochitl","tonatiuh","tlaloc","huitzilopochtli","quetzalcoatl",
        "tezcatlipoca","xipe","coatlicue","chalchiuhtlicue","tlazolteotl","xochiquetzal",
        "tenochtitlan","teotihuacan","tlacopan","texcoco","cholula","xochimilco","tlatelolco",
        "jaguar","eagle","serpent","sun","moon","earth","water","fire","wind","rain","lightning",
        "obsidian","jade","turquoise","gold","feather","cacao","maize","agave","copal","rubber",
        "macuahuitl","atlatl","tepoztopilli","chimalli","tlahuiztli","xiuhuitzolli","cozcatl",
        "calpulli","altepetl","tlatoani","cihuacoatl","huey","pochteca","tameme",
    ],
    "celtic": [
        "druide","ogham","brigid","lugh","dagda","morrigan","cernunnos","danu","tuatha",
        "fionn","cuchulainn","conchobar","medb","fergus","diarmuid","grainne","ossian","bran",
        "camelot","avalon","tintagel","glastonbury","stonehenge","avebury","newgrange","tara",
        "samhain","imbolc","beltane","lughnasadh","ostara","yule","mabon","litha","lammas",
        "triskele","triquetra","knotwork","spirals","labyrinth","maze","mandala","pattern",
        "eire","alba","cymru","breizh","kernow","mannin","galicia","asturias","brittany",
        "clan","tuath","tribe","sept","family","kinship","loyalty","honor","bravery","valor",
    ],
    "egyptian": [
        "ankh","kha","nefret","amun","pharaoh","sphinx","pyramid","obelisk","papyrus","lotus",
        "scarab","cobra","falcon","ibis","jackal","crocodile","hippo","cat","lion","ram",
        "cartouche","hieroglyph","demotic","coptic","cuneiform","scroll","tablet","stele",
        "canopic","ushabti","amulet","talisman","charm","spell","curse","blessing","prayer",
        "nile","delta","flood","silt","black","land","red","desert","duat","amduat","book",
        "dead","weighing","heart","feather","maat","truth","justice","balance","harmony",
        "thebes","memphis","heliopolis","karnak","luxor","edfu","dendera","abydos","saqqara",
    ],
    "roman": [
        "acer","cato","draco","lucius","marcus","gaius","publius","quintus","titus","julius",
        "augustus","tiberius","caligula","claudius","nero","vespasian","domitian",
        "nerva","trajan","hadrian","antoninus","commodus","septimius","caracalla",
        "legion","cohort","century","maniple","turma","ala","vexillation","auxilia","limitanei",
        "gladius","pilum","scutum","lorica","galea","caligae","paludamentum","sagum","cucullus",
        "forum","basilica","circus","amphitheater","theater","baths","aqueduct","road","bridge",
        "senate","consul","praetor","quaestor","censor","tribune","dictator","imperator","caesar",
    ],
    "spartan": [
        "leonidas","agis","lysander","brasidas","pausanias","cleomenes","archidamus","agesilaus",
        "laconia","sparta","peloponnese","taygetos","eurotas","parnon","malea","matapan",
        "phalanx","hoplite","aspis","dory","xiphos","kopis","sarissa","xyston","javelin",
        "agoge","krypteia","syssitia","kleros","helot","perioikoi","spartan","lacedaemon",
        "battle","thermopylae","plataea","mantinea","leuctra","sellasia","megalopolis",
        "molon","labe","shield","arete","kleos","time","moira","xenia","eunomia",
        "sophrosyne","andreia","phronesis",
    ],
    "gemstones": [
        "diamond","ruby","emerald","sapphire","amethyst","topaz","opal","pearl","jade","onyx",
        "garnet","tourmaline","aquamarine","alexandrite","spinel","tanzanite","zircon","citrine",
        "peridot","malachite","turquoise","lapis","lazuli","moonstone","sunstone","labradorite",
        "amazonite","chrysocolla","rhodonite","rhodochrosite","kunzite","hiddenite","tsavorite",
        "demantoid","andradite","grossular","hessonite","spessartine","almandine","pyrope",
        "uvarovite","paraiba","indicolite","verdelite","rubellite","watermelon","achroite",
        "benitoite","painite","musgravite","grandidierite","jeremejevite","serendibite","taaffeite",
    ],
    "metals": [
        "titanium","tungsten","osmium","iridium","cobalt","vanadium","chromium","manganese",
        "niobium","molybdenum","ruthenium","rhodium","palladium","rhenium","hafnium","tantalum",
        "platinum","gold","silver","iron","copper","zinc","tin","lead","aluminum","magnesium",
        "calcium","sodium","potassium","lithium","beryllium","scandium","yttrium","zirconium",
        "bismuth","antimony","tellurium","selenium","arsenic","germanium","gallium","indium",
        "thallium","mercury","cadmium","strontium","barium","radium","francium","cesium",
        "rubidium","lanthanum","cerium","praseodymium","neodymium","samarium","europium",
    ],
    "colorsen": [
        "crimson","scarlet","vermillion","carmine","burgundy","maroon","cherry","rose","blush",
        "salmon","coral","tangerine","amber","ochre","gold","khaki","chartreuse","lime","olive",
        "emerald","teal","cyan","azure","cobalt","sapphire","indigo","violet","lavender","mauve",
        "lilac","periwinkle","amethyst","plum","eggplant","magenta","fuchsia","cerise","pink",
        "ivory","cream","beige","ecru","linen","bisque","wheat","tan","bronze","copper",
        "mahogany","sienna","umber","sepia","taupe","grey","charcoal","slate","pewter","silver",
        "platinum","white","snow","pearl","alabaster","chalk","bone","eggshell",
    ],
    "colorsfr": [
        "cramoisi","ecarlate","vermillon","carmin","bordeaux","marron","cerise","rose","saumon",
        "corail","orange","ambre","ocre","or","kaki","citron","lime","olive","emeraude","sarcelle",
        "cyan","azur","cobalt","saphir","indigo","violet","lavande","mauve","lilas","pervenche",
        "amethyste","prune","magenta","fuchsia","ivoire","creme","beige","ecru",
        "lin","ble","bisque","bronze","cuivre","acajou","sienne","ombre","sepia","taupe",
        "gris","charbon","ardoise","etain","argent","platine","blanc","neige","perle","albatre",
        "craie","os","coquille","nacre","lait","nuage","brume","brouillard","fumee",
    ],
    "emotions": [
        "wrath","grief","bliss","dread","angst","envy","spite","lust","pride","sloth","greed",
        "gluttony","despair","euphoria","melancholy","nostalgia","serenity","ecstasy",
        "terror","anxiety","panic","phobia","paranoia","obsession","mania","hysteria","apathy",
        "indifference","stoicism","equanimity","tranquility","contentment","satisfaction","joy",
        "elation","exhilaration","rapture","fervor","passion","ardor","zeal","enthusiasm","vigor",
        "courage","valor","bravery","audacity","tenacity","resilience","fortitude","perseverance",
        "compassion","empathy","sympathy","kindness","generosity","gratitude","humility","mercy",
    ],
    "philosophy": [
        "stoic","axiom","logos","ethos","pathos","pragma","techne","episteme","phronesis",
        "arete","eudaimonia","aponia","ataraxia","apatheia","katalepsis","synkatathesis",
        "epoche","skeptic","cynic","epicurean","peripatetic","platonic","aristotelian",
        "socratic","presocratic","sophist","sophistry","dialectic","dialectics","rhetoric",
        "ontology","epistemology","metaphysics","ethics","aesthetics","logic","axiology",
        "phenomenology","hermeneutics","existentialism","nihilism","absurdism","pragmatism",
        "empiricism","rationalism","idealism","materialism","dualism","monism","pluralism",
        "determinism","libertarianism","compatibilism","consequentialism","deontology","virtue",
    ],
    "duality": [
        "yin","yang","dusk","dawn","chaos","order","light","dark","fire","ice","sun","moon",
        "earth","sky","life","death","war","peace","love","hate","creation","destruction",
        "alpha","omega","begin","end","first","last","north","south","east","west","above","below",
        "rise","fall","ascend","descend","wax","wane","bloom","wither","birth","day","night",
        "good","evil","truth","lie","real","fake","solid","void","full","empty","loud","silent",
        "fast","slow","hot","cold","wet","dry","hard","soft","sharp","blunt","bright","dim",
        "macro","micro","cosmos","quantum","infinite","finite","eternal","mortal","divine","human",
    ],
    "pronounceable": [
        "kova","zara","nelo","tavi","mira","sefa","daro","lenu","piko","vane","relo","tuva",
        "mako","seli","devo","kira","namo","telo","vari","muse","sako","deli","keva","runo",
        "palo","temi","vora","melo","saki","kano","remi","toki","varu","luka","niko","taro",
        "sena","vela","miko","dako","reni","nova","luna","aria","echo","iris","eden","orin",
        "asha","zion","nara","kaia","mila","lena","vera","cleo","demi","emma","faye","gaia",
        "hana","isla","jade","lila",
    ],
    "brandable": [
        "stripe","slack","zoom","snap","vine","bump","drift","float","glide","hover","launch",
        "pivot","scale","shift","spark","surge","swipe","sync","trend","vibe","warp","wave",
        "blend","boost","bridge","burst","click","cloud","crash","crux","dash","data","edge",
        "flow","flux","frame","fresh","fuse","gain","grid","grip","grow","hack","hash","heap",
        "hub","hyper","idea","input","intel","key","knot","layer","lean","lens","lever","link",
        "loop","map","mesh","meta","mint","mix","node","norm","null","open","ops","orbit","page",
        "parse","path","peak","pipe","pixel","plan","platform","plug","point","post","prime","probe",
    ],
    "gamer": [
        "frag","noob","pwned","gg","ez","rekt","grind","loot","gear","raid","boss","tank",
        "dps","heal","buff","nerf","patch","meta","carry","feed","tilt","flame","toxic","smurf",
        "aimbot","wallhack","spinbot","rage","quit","dc","lag","ping","fps","ms","ttk","hs",
        "clutch","ace","eco","rush","peek","hold","rotate","flank","lurk","anchor","entry",
        "fragger","igl","awper","rifler","support","flex","main","one","trick","otp","hardstuck",
        "diamond","platinum","gold","silver","bronze","iron","master","grandmaster","challenger",
        "mythic","immortal","radiant","predator","apex","eagle","guardian","crusader","archon",
    ],
}

THEMES_EXTRA = {
    "ninja": ["shadow","stealth","silent","blade","dagger","shuriken","kunai","katana","scroll",
        "hide","strike","vanish","ghost","phantom","dark","moon","night","veil","mask","cloak",
        "mist","fog","smoke","wind","swift","quick","fatal","deadly","lethal","secret"],
    "gladiator": ["arena","colosseum","sand","blood","glory","victory","champion","warrior",
        "shield","sword","spear","net","trident","helmet","armor","battle","fight","duel",
        "crowd","roar","lion","tiger","beast","slave","free","roman","empire","death","life"],
    "dragon": ["scale","claw","fang","wing","fire","roar","flight","nest","hoard","gold",
        "treasure","ancient","elder","wyrm","drake","wyvern","serpent","coil","tail","breath",
        "smoke","ember","ash","cinder","inferno","blaze","scorch","char","burn","ignite"],
    "witch": ["hex","curse","spell","brew","potion","cauldron","herb","moon","night","shadow",
        "raven","crow","cat","familiar","coven","circle","candle","flame","smoke","incense",
        "crystal","orb","mirror","tarot","pentacle","sigil","rune","charm","enchant","bewitch"],
    "demon": ["inferno","abyss","void","chaos","dark","shadow","curse","dread","terror","fear",
        "malice","spite","wrath","fury","rage","hate","vengeance","doom","ruin","destroy",
        "corrupt","taint","blight","plague","pestilence","famine","war","death","hell","fire"],
    "angel": ["light","grace","divine","holy","sacred","pure","heaven","cloud","wing","halo",
        "glory","radiance","luminous","celestial","ethereal","spirit","soul","peace","love",
        "mercy","compassion","charity","faith","hope","truth","wisdom","justice","valor","virtue"],
    "forest": ["oak","pine","birch","maple","cedar","sequoia","redwood","grove","thicket","glade",
        "meadow","clearing","canopy","understory","shrub","fern","moss","lichen","mushroom","spore",
        "root","bark","branch","leaf","needle","cone","acorn","seed","bloom","flower"],
    "desert": ["sand","dune","oasis","mirage","heat","sun","cactus","scorpion","snake","lizard",
        "hawk","vulture","camel","nomad","tribe","caravan","spice","salt","stone","rock",
        "canyon","gorge","mesa","plateau","badland","wasteland","barren","arid","dry","dust"],
    "space": ["cosmos","nebula","galaxy","quasar","pulsar","neutron","black","hole","event",
        "horizon","singularity","wormhole","stargate","portal","void","vacuum","plasma","ion",
        "photon","electron","proton","quantum","relativity","gravity","orbit","trajectory","vector"],
    "ocean2": ["deep","abyss","trench","mariana","hadal","benthic","pelagic","abyssal","midnight",
        "twilight","sunlight","epipelagic","mesopelagic","bathypelagic","abyssopelagic","hadalpelagic",
        "coral","reef","atoll","shoal","bank","seamount","ridge","rift","basin"],
    "storm2": ["cyclone","typhoon","hurricane","tornado","waterspout","haboob","derecho","squall",
        "gale","tempest","maelstrom","vortex","whirlwind","dust","devil","sandstorm","blizzard",
        "snowsquall","ice","storm","thunderstorm","lightning","thunder","hail","sleet","freezing"],
    "lore": ["legend","myth","tale","saga","epic","ballad","chronicle","annals","tome","codex",
        "grimoire","scroll","tablet","inscription","relic","artifact","totem","idol","effigy",
        "prophecy","oracle","vision","dream","omen","portent","sign","wonder","miracle","mystery"],
    "mage": ["arcane","mystic","esoteric","occult","eldritch","arcanum","grimoire","tome","scroll",
        "spell","rune","glyph","sigil","ward","seal","binding","summon","conjure","invoke","banish",
        "shield","barrier","veil","shroud","cloak","illude","glamour","enchant","bewitch"],
    "assassin2": ["silent","swift","deadly","fatal","lethal","precise","accurate","calculated",
        "cold","ruthless","merciless","relentless","unstoppable","shadow","ghost","phantom","wraith",
        "specter","shade","darkness","night","void","nothing","nowhere","everywhere","unseen"],
    "warlock": ["pact","bargain","deal","contract","soul","power","dark","eldritch","arcane",
        "forbidden","cursed","tainted","corrupted","twisted","warped","broken","shattered","void",
        "chaos","entropy","destruction","obliteration","annihilation","devastation","ruin","doom"],
}
THEMES.update(THEMES_EXTRA)

# ── NETTOYAGE ─────────────────────────────────────────────────────────────────
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def is_valid(name):
    if not (2 <= len(name) <= 32): return False
    if not re.match(r'^[a-z0-9][a-z0-9_]*[a-z0-9]$', name): return False
    if '__' in name: return False
    return True


def is_valid_vanity(code):
    return bool(re.match(r'^[a-z0-9\-]{2,32}$', code))


# ── CHARGEMENT DICOS ──────────────────────────────────────────────────────────
def load_wordlist(path):
    if not os.path.exists(path): return []
    words = set()
    with open(path, encoding="utf-8", errors="ignore") as f:
        if path.endswith(".json"):
            import json
            try:
                lines = json.load(f)
            except Exception as ex:
                print(f"[WARN] {path} illisible : {ex}")
                return []
        else:
            lines = f
        for line in lines:
            w = strip_accents(str(line).strip().lower())
            if re.match(r'^[a-z]{3,20}$', w):
                words.add(w)
    return list(words)


def load_cities(path):
    cities = set()
    if not os.path.exists(path): return []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                name = row.get("name", "").strip()
                if not name: continue
                cleaned = re.sub(r'[^a-z]', '', strip_accents(name.lower()))
                if 3 <= len(cleaned) <= 20:
                    cities.add(cleaned)
    except Exception as e:
        print(f"[WARN] villes : {e}")
    return list(cities)


def load_cities_by_country(path):
    """Retourne un dict {country_code_lower: [villes]} depuis le CSV world-cities."""
    result = {}
    if not os.path.exists(path): return result
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                name    = row.get("name", "").strip()
                country = row.get("country", "").strip().lower()
                if not name or not country: continue
                cleaned = re.sub(r'[^a-z]', '', strip_accents(name.lower()))
                if 3 <= len(cleaned) <= 20:
                    result.setdefault(country, set()).add(cleaned)
    except Exception as e:
        print(f"[WARN] villes_by_country : {e}")
    return {k: list(v) for k, v in result.items()}


print("[*] Chargement des dicos...")
_loaded_fr     = load_wordlist("words_fr.json")
_loaded_en     = load_wordlist("words_en.txt")
_loaded_cities = load_cities("words_cities.csv")

BUILTIN_FR = ["lune","soleil","etoile","ciel","nuage","brume","orage","tonnerre","eclair",
    "pluie","neige","givre","glace","vent","tempete","montagne","vallee","desert","foret",
    "ocean","mer","lac","riviere","cascade","vague","ile","falaise","caverne","roche","flamme",
    "fleur","rose","lys","chene","pin","bouleau","loup","renard","corbeau","chouette","aigle"]
BUILTIN_EN = ["moon","sun","star","sky","cloud","mist","storm","thunder","lightning","rain",
    "snow","frost","ice","wind","gale","mountain","valley","desert","forest","ocean","sea",
    "lake","river","waterfall","wave","island","cliff","cave","rock","flame","flower","rose"]

ALL_FR = _loaded_fr if _loaded_fr else BUILTIN_FR
ALL_EN = _loaded_en if _loaded_en else BUILTIN_EN

FAMOUS_CITIES = [
    "paris","london","berlin","tokyo","rome","madrid","barcelona","amsterdam","vienna","prague",
    "budapest","stockholm","oslo","copenhagen","zurich","geneva","moscow","istanbul","dubai","cairo",
    "sydney","melbourne","toronto","montreal","miami","boston","chicago","seattle","denver","phoenix",
    "singapore","bangkok","seoul","osaka","kyoto","taipei","hongkong","shanghai","beijing","delhi",
    "mumbai","lyon","marseille","bordeaux","toulouse","nice","nantes","strasbourg","milan","florence",
    "venice","naples","lisbon","porto","athens","brussels","antwerp","hamburg","munich","frankfurt",
    "cologne","warsaw","bucharest","sofia","zagreb","helsinki","riga","vilnius","tallinn","reykjavik",
    "dublin","edinburgh","glasgow","manchester","birmingham","liverpool","leeds","bristol","cardiff","belfast",
    "vancouver","calgary","ottawa","quebec","lagos","nairobi","accra","dakar","casablanca",
    "marrakech","tunis","algiers","johannesburg","capetown","pretoria","abuja","addisababa","kampala",
]
_famous_set = set(FAMOUS_CITIES)
if _loaded_cities:
    ALL_CITIES = FAMOUS_CITIES + [c for c in _loaded_cities if c not in _famous_set]
else:
    ALL_CITIES = FAMOUS_CITIES

LANGS = {
    "de": ["wald","stein","berg","fluss","see","mond","sonne","wind","feuer","wasser","erde",
           "wolf","fuchs","adler","eule","bar","lowe","tiger","rabe","schlange","sturm","blitz",
           "nebel","frost","glut","asche","dunkel","licht","schatten","geist","seele","traum"],
    "es": ["luna","sol","viento","fuego","agua","tierra","lobo","aguila","cuervo","sombra",
           "noche","alba","tormenta","rayo","trueno","montana","rio","lago","mar","bosque",
           "desierto","hielo","nieve","bruma","niebla","humo","llama","ceniza","polvo","roca"],
    "it": ["luna","sole","vento","fuoco","acqua","terra","lupo","aquila","corvo","ombra",
           "notte","alba","tempesta","fulmine","tuono","montagna","fiume","lago","mare","bosco",
           "deserto","ghiaccio","neve","nebbia","fumo","fiamma","cenere","polvere","roccia","luce"],
    "pt": ["lua","sol","vento","fogo","agua","terra","lobo","aguia","corvo","sombra",
           "noite","alba","tempestade","raio","trovao","montanha","rio","lago","mar","floresta",
           "deserto","gelo","neve","neblina","fumaca","chama","cinza","poeira","rocha","luz"],
    "nl": ["maan","zon","wind","vuur","water","aarde","wolf","adelaar","raaf","schaduw",
           "nacht","dageraad","storm","bliksem","donder","berg","rivier","meer","zee","bos",
           "woestijn","ijs","sneeuw","mist","rook","vlam","as","stof","rots","licht"],
    "pl": ["ksiezyc","slonce","wiatr","ogien","woda","ziemia","wilk","orel","kruk","cien",
           "noc","swit","burza","piorun","grzmot","gora","rzeka","jezioro","morze","las",
           "pustynia","lod","snieg","mgla","dym","plomien","popiol","pyl","skala","swiatlo"],
    "sv": ["mane","sol","vind","eld","vatten","jord","varg","orn","korp","skugga",
           "natt","gryning","storm","blixt","aska","berg","flod","sjo","hav","skog",
           "oken","is","sno","dimma","rok","flamma","damm","klippa","ljus"],
    "no": ["mane","sol","vind","ild","vann","jord","ulv","orn","ravn","skygge",
           "natt","gry","storm","lyn","torden","fjell","elv","innsjo","hav","skog",
           "oken","is","sno","take","rok","flamme","aske","stov","klippe","lys"],
    "jp": ["tsuki","hoshi","kaze","hi","mizu","uchi","sora","yama","kawa","umi",
           "mori","shiro","kuroi","aoi","aka","midori","kiiro","kage","hikari",
           "katana","ninja","samurai","ronin","shogun","dojo","sakura","fuji","oni","tengu"],
    "ko": ["dal","byul","baram","bul","mul","san","gang","bada","hanal","areum",
           "bidam","cheon","earth","black","white","blue","red","green","shadow","light"],
    "ar": ["nour","badr","fajr","leil","qamar","najm","rih","bahr","jabal","sahara",
           "asad","namir","saqr","dhi","iblis","jinn","marid","ifrit","silat","ghoul"],
    "ru": ["luna","zvezda","veter","ogon","voda","les","more","gora","reka","noch",
           "volya","sila","dukh","volk","orel","medved","lion","tigr","zmey","feniks"],
}

print(f"[*] Prêt — FR:{len(ALL_FR):,} EN:{len(ALL_EN):,} Villes:{len(ALL_CITIES):,}")
if not _loaded_fr:
    print("[WARN] Dico FR non chargé : seuls 41 mots de secours sont utilisés.")

# ── VANITY BLACKLIST ──────────────────────────────────────────────────────────
VANITY_BLACKLIST = set([
    "discord","discordapp","discordnitro","nitro","nitrogift","gift","clyde","wumpus",
    "everyone","here","admin","administrator","moderator","mod","staff","owner","support",
    "help","official","team","bot","bots","google","youtube","twitter","facebook",
    "instagram","tiktok","snapchat","twitch","netflix","spotify","apple","microsoft",
    "amazon","meta","whatsapp","telegram","reddit","roblox","minecraft","fortnite",
    "valorant","steam","epic","riot","blizzard","activision","ubisoft","bethesda",
    "rockstar","porn","sex","xxx","nsfw","hack","hacker","crack","cheat","drug","drugs",
    "kill","murder","terrorist","isis","nazi","fbi","cia","nsa","interpol","police",
    "government","president","free","giveaway","airdrop","crypto","nft","bitcoin",
    "ethereum","scam","phishing","malware","virus","api","app","apps","web","www",
    "mail","email","login","signup","register","verify","account","billing","terms",
    "privacy","safety","security","payments","new","news","download","update","invite",
])


def is_vanity_allowed(code):
    code = code.lower()
    if code in VANITY_BLACKLIST: return False
    for banned in VANITY_BLACKLIST:
        if banned in code and len(banned) >= 5: return False
    return True


# ── TRANSFORMS ────────────────────────────────────────────────────────────────
AESTHETIC_MAP = {"a":"4","e":"3","i":"1","o":"0","s":"5","l":"1","t":"7","g":"9","b":"8"}


def to_aesthetic(word):
    variants = {word}
    full = word
    for k, v in AESTHETIC_MAP.items(): full = full.replace(k, v)
    if full != word and is_valid(full): variants.add(full)
    for i, c in enumerate(word):
        if c in AESTHETIC_MAP:
            v = word[:i] + AESTHETIC_MAP[c] + word[i+1:]
            if is_valid(v): variants.add(v)
    return list(variants)


def to_leet(word):
    return word.translate(str.maketrans("aeiost", "431057"))


def to_reverse(word):
    return word[::-1]


def to_underscore(word):
    if len(word) >= 4:
        mid = len(word) // 2
        return word[:mid] + "_" + word[mid:]
    return word


# ── BUILD POOL (corrigé : plus de set() reconstruit à chaque itération) ───────
def build_pool(word_list, n=100, min_len=3, max_len=16,
               aesthetic=False, leet=False, reverse=False, underscore=False,
               preserve_order=False):
    solo = [w for w in word_list if min_len <= len(w) <= max_len and is_valid(w)]
    if not solo:
        return []
    if not preserve_order:
        random.shuffle(solo)
    pool = set(solo[:n])

    if aesthetic:
        for w in solo[:n // 2]:
            for v in to_aesthetic(w):
                if is_valid(v): pool.add(v)
    if leet:
        for w in solo[:n // 2]:
            v = to_leet(w)
            if is_valid(v): pool.add(v)
    if reverse:
        for w in solo[:n // 2]:
            v = to_reverse(w)
            if is_valid(v): pool.add(v)
    if underscore:
        for w in solo[:n // 2]:
            v = to_underscore(w)
            if is_valid(v): pool.add(v)

    solo_set = set(solo)
    solo_valid = [p for p in pool if '_' not in p and p in solo_set]
    valid_set = set(solo_valid)
    combos = []
    if len(solo_valid) < n:
        pairs_src = random.sample(solo, min(120, len(solo)))
        for a, b in itertools.combinations(pairs_src, 2):
            if len(combos) >= n * 2: break
            if 5 <= len(a) + len(b) <= max_len:
                combos.append(f"{a}{b}")
                combos.append(f"{a}_{b}")
        random.shuffle(combos)

    extras = [p for p in pool if p not in valid_set and is_valid(p)]
    result = solo_valid + extras + [c for c in combos if is_valid(c)]
    return result[:n]


async def build_pool_async(*args, **kwargs):
    """build_pool dans un thread : ne bloque plus le bot."""
    return await asyncio.to_thread(build_pool, *args, **kwargs)


# ── CHECK PSEUDO ──────────────────────────────────────────────────────────────
async def check_available(session, username):
    if not USER_TOKEN:
        return None
    url = "https://discord.com/api/v9/users/@me/pomelo-attempt"
    try:
        async with session.post(url, json={"username": username},
                headers=get_user_headers(), timeout=aiohttp.ClientTimeout(total=5)) as r:
            body = await r.text()
            print(f"[DEBUG] pomelo {username} → {r.status} {body[:120]}", flush=True)
            if r.status == 200:
                STATS["checked"] += 1
                import json as _json
                try:
                    data = _json.loads(body)
                except Exception:
                    data = {}
                return not data.get("taken", True)
            elif r.status == 401:
                return "INVALID_TOKEN"
            elif r.status == 429:
                retry = float(r.headers.get("Retry-After", 3))
                try:
                    import json as _j
                    retry = float(_j.loads(body).get("retry_after", retry))
                except Exception:
                    pass
                retry = min(retry, 60)  # cap à 60s max pour éviter les blocages trop longs
                RATE["until"] = time.time() + retry
                print(f"[DEBUG] pomelo RATE_LIMITED — cooldown {retry:.1f}s", flush=True)
                return "RATE_LIMITED"
    except Exception as ex:
        print(f"[DEBUG] pomelo exception: {ex}", flush=True)
    return None


# ── CHECK VANITY ──────────────────────────────────────────────────────────────
async def check_vanity(session, code):
    url = f"https://discord.com/api/v9/invites/{code}"
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"},
                timeout=aiohttp.ClientTimeout(total=5)) as r:
            if r.status == 404:
                STATS["checked"] += 1
                return True
            elif r.status == 200:
                STATS["checked"] += 1
                return False
            elif r.status == 429:
                retry = float(r.headers.get("Retry-After", 2))
                await asyncio.sleep(retry)
                return None
    except Exception:
        pass
    return None


# ── EMBED HELPER ──────────────────────────────────────────────────────────────
def make_embed(title="", desc="", color=C["dark"], footer="meanings", description=None):
    if description is not None:
        desc = description
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text=f"meanings · {footer}")
    return e


def result_embed(found, scanned, flag, label, color, is_vanity=False):
    fmt = "discord.gg/{}" if is_vanity else "{}"
    kind = "vanity" if is_vanity else "pseudo"
    if not found:
        return make_embed(f"{flag}  Aucun {kind}", "> Tous pris. Relance.", C["error"], f"{scanned} scannés")
    lines = "\n".join(f"> `{fmt.format(p)}`" for p in found)
    e = discord.Embed(
        title=f"{flag}  {len(found)} {kind}{'s' if len(found) > 1 else ''} dispo{'s' if len(found) > 1 else ''}",
        description=lines, color=color)
    e.set_footer(text=f"meanings · {scanned} scannés · {len(ALL_FR):,} FR · {len(ALL_EN):,} EN")
    return e


def token_missing_embed():
    return discord.Embed(
        title="❌  USER_TOKEN manquant",
        description=("> Le scan de pseudos nécessite la variable `USER_TOKEN`.\n"
                     "> Configure-la sur Railway → Variables."),
        color=C["error"])


# ── SCAN ENGINE ───────────────────────────────────────────────────────────────
async def _scan_engine(candidates, max_results, msg, flag, label, color,
                       check_fn, is_vanity=False, ctx=None, speed=None):
    if speed is None:
        speed = CONFIG["check_delay"]
    if not is_vanity and check_fn == check_available and not USER_TOKEN:
        try: await msg.edit(embed=token_missing_embed())
        except Exception: pass
        return [], 0
    wait = RATE["until"] - time.time()
    if not is_vanity and check_fn == check_available and wait > 0:
        try:
            await msg.edit(embed=make_embed("⏳  Limite Discord",
                f"> Checks de pseudos bloqués encore ~`{int(wait)}s`.\n> Les commandes `vanity` ne sont pas touchées.", C["warn"]))
        except Exception: pass
        return [], 0

    found = []
    checked = 0
    invalid = False
    limited = False
    sem = asyncio.Semaphore(CONFIG["parallel"])

    async def check_one(session, target):
        nonlocal checked, invalid, limited
        if invalid or limited or len(found) >= max_results:
            return
        async with sem:
            if invalid or limited or len(found) >= max_results:
                return
            await asyncio.sleep(speed)
            result = await check_fn(session, target)
            if result == "INVALID_TOKEN":
                invalid = True
                return
            if result == "RATE_LIMITED":
                limited = True
                return
            checked += 1
            if result is True:
                found.append(target)
                STATS["found"] += 1
                if ctx:
                    LEADERBOARD[ctx.author.id] += 1
                    HISTORY[ctx.author.id].append({
                        "pseudo": target, "ts": time.time(), "available": True, "vanity": is_vanity})
                if len(found) % 3 == 0 or len(found) == 1:
                    fmt = "discord.gg/{}" if is_vanity else "{}"
                    lines = "\n".join(f"> `{fmt.format(p)}`" for p in found)
                    e = discord.Embed(
                        title=f"{flag}  {len(found)} trouvé{'s' if len(found) > 1 else ''} · {checked} vérifiés",
                        description=lines, color=color)
                    e.set_footer(text=f"meanings · scan {label} en cours...")
                    try: await msg.edit(embed=e)
                    except Exception: pass

    async with aiohttp.ClientSession() as session:
        tasks = []
        for target in candidates:
            if invalid or limited or len(found) >= max_results: break
            tasks.append(asyncio.create_task(check_one(session, target)))
            if len(tasks) >= CONFIG["parallel"] * 4:
                await asyncio.gather(*tasks); tasks = []
        if tasks:
            await asyncio.gather(*tasks)

    return found[:max_results], checked


async def run_scan(ctx, word_list, label, color, flag,
                   limit=MAX_RESULTS, min_len=3, max_len=16,
                   aesthetic=False, leet=False, underscore=False, speed=None):
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    if speed is None: speed = CONFIG["check_delay"]
    limit = max(1, min(limit, 30))
    n = min(max(limit * 6, 30), 200)
    STATS["scans"] += 1
    msg = await ctx.send(embed=make_embed(description=f"```\n⏳  Génération — {label}...\n```", footer="scan en cours"))
    try:
        candidates = await build_pool_async(word_list, n, min_len, max_len, aesthetic, leet, False, underscore)
    except Exception as ex:
        print(f"[ERREUR] build_pool : {ex}", flush=True)
        await msg.edit(embed=make_embed("❌  Erreur", f"> `{ex}`", C["error"])); return
    found, checked = await _scan_engine(candidates, limit, msg, flag, label, color, check_available, False, ctx, speed)
    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit Discord active — réessaie dans ~`{remaining}s`.\n> (logs `[DEBUG] pomelo` pour détails)"
                if remaining > 0 else
                "> Token invalide ou expiré — vérifie `USER_TOKEN`.\n> Ou rate limit dépassée, réessaie dans quelques secondes.")
        await msg.edit(embed=discord.Embed(
            title="❌  Token refusé ou limite Discord",
            description=desc,
            color=C["error"])); return
    await msg.edit(embed=result_embed(found, checked, flag, label, color))


async def run_vanity_scan(ctx, word_list, label, color, flag,
                          limit=MAX_RESULTS, min_len=3, max_len=16, speed=None,
                          preserve_order=False):
    if speed is None: speed = CONFIG["check_delay"]
    limit = max(1, min(limit, 30))
    n = min(max(limit * 6, 30), 200)
    STATS["scans"] += 1
    msg = await ctx.send(embed=make_embed(description=f"```\n⏳  Vanity — {label}...\n```", footer="scan en cours"))
    try:
        raw = await build_pool_async(word_list, n * 2, min_len, max_len, preserve_order=preserve_order)
    except Exception as ex:
        print(f"[ERREUR] build_pool : {ex}", flush=True)
        await msg.edit(embed=make_embed("❌  Erreur", f"> `{ex}`", C["error"])); return
    candidates = [c for c in raw if is_vanity_allowed(c)][:n]
    found, checked = await _scan_engine(candidates, limit, msg, flag, label, color, check_vanity, True, ctx, speed)
    await msg.edit(embed=result_embed(found, checked, flag, label, color, is_vanity=True))


# ── BOT ───────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
_watch_started = False


@bot.event
async def on_ready():
    global TOTAL_CMDS, _watch_started
    TOTAL_CMDS = len(bot.commands)
    print(f"[*] {bot.user} connecté — meanings v4.0 — {TOTAL_CMDS} commandes")
    if not _watch_started:
        _watch_started = True
        bot.loop.create_task(watch_loop())


@bot.event
async def on_command(ctx):
    STATS["commands"] += 1


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
        await ctx.send(embed=make_embed("⚠️  Argument invalide", f"> {error}", C["warn"])); return
    traceback.print_exception(type(error), error, error.__traceback__)


# ═══════════════════════════════════════════════════════════════════════════════
#  🔢 LONGUEUR EXACTE — len3 à len12 (aliases 3c / 3l)
# ═══════════════════════════════════════════════════════════════════════════════

def _len_cmd(exact):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        if not USER_TOKEN:
            await ctx.send(embed=token_missing_embed()); return
        flag   = {3:"⚡",4:"👑",5:"🔥",6:"✨",7:"💎",8:"🌟",9:"🎯",10:"🏆",11:"📌",12:"🎪"}.get(exact, "🔢")
        color  = {3:C["og"],4:C["og"],5:C["short"],6:C["short"],7:C["mix"],8:C["mix"],
                  9:C["fr"],10:C["fr"],11:C["en"],12:C["en"]}.get(exact, C["info"])
        rarity = {3:"🔴 Extrêmement rares",4:"🟠 Très rares",5:"🟡 Rares",
                  6:"🟢 Peu communs",7:"🔵 Communs"}.get(exact, "⚪ Fréquents")
        limit_real = max(1, min(limit, 30))
        # pool beaucoup plus large — les longueurs rares (9-12) ont peu de mots-clés exacts
        n = min(max(limit_real * 20, 300), 1000)
        STATS["scans"] += 1
        msg = await ctx.send(embed=make_embed(
            description=f"```\n🔢  Scan {exact} chars exactement...\n{rarity}\n```",
            footer=f"scan {exact}C en cours"))

        def build():
            mixed = ALL_FR + ALL_EN
            # 1. mots de longueur exacte dans les dicos
            pool = list({w for w in mixed if len(w) == exact and is_valid(w)})
            seen = set(pool)

            # 2. combos a+b et b+a de longueur exacte
            short = [w for w in mixed if 2 <= len(w) <= exact - 2 and is_valid(w)]
            random.shuffle(short)
            for a, b in itertools.combinations(short[:500], 2):
                for combo in (a + b, b + a):
                    if len(combo) == exact and combo not in seen and is_valid(combo):
                        pool.append(combo)
                        seen.add(combo)
                if len(pool) >= n * 2:
                    break

            # 3. fallback alphabétique — génère des strings a-z de longueur exacte
            #    garantit un pool plein même pour len9-12 où les dicos sont creux
            if len(pool) < n:
                chars = list("abcdefghijklmnopqrstuvwxyz")
                attempts = 0
                while len(pool) < n and attempts < n * 50:
                    attempts += 1
                    candidate = "".join(random.choices(chars, k=exact))
                    if candidate not in seen and is_valid(candidate):
                        pool.append(candidate)
                        seen.add(candidate)

            random.shuffle(pool)
            return pool[:n]

        candidates = await asyncio.to_thread(build)
        found, checked = await _scan_engine(candidates, limit_real, msg, flag,
                                            f"{exact}C", color, check_available, False, ctx)
        if found:
            lines = "\n".join(f"> `{p}`" for p in found)
            e = discord.Embed(
                title=f"{flag}  {len(found)} pseudo{'s' if len(found) > 1 else ''} {exact} chars",
                description=f"> **{rarity}**\n\n{lines}", color=color)
            e.set_footer(text=f"meanings · {checked} scannés · {exact} chars exactement")
        else:
            remaining = max(0, int(RATE["until"] - time.time()))
            desc = (f"> Rate limit Discord — réessaie dans ~`{remaining}s`." if remaining > 0
                    else f"> {rarity}\n> Relance pour réessayer.")
            e = make_embed(f"{flag}  Aucun pseudo {exact}C", desc,
                           C["warn"] if remaining > 0 else C["error"],
                           f"{checked} scannés")
        await msg.edit(embed=e)
    return _inner


for _n in range(3, 13):
    _f = _len_cmd(_n)
    bot.command(name=f"len{_n}")(_f)
    bot.command(name=f"{_n}c")(_len_cmd(_n))
    bot.command(name=f"{_n}l")(_len_cmd(_n))


# ═══════════════════════════════════════════════════════════════════════════════
#  🔀 COMBOS LETTRES+CHIFFRES / CHIFFRES+LETTRES (4→8 chars)
#  +combo4   → 4 chars : lettres+chiffres mélangés (ex: ab12, x9kz)
#  +combo4l  → 4 lettres uniquement         (ex: abcd)
#  +combo4d  → 4 chiffres uniquement        (ex: 1234)
#  +combo5   → 5 chars mixtes, etc.
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_combo(length: int, mode: str, n: int) -> list:
    """
    Génère n combinaisons uniques de longueur `length`.
    mode : 'alpha'  → a-z seulement
           'digit'  → 0-9 seulement
           'alnum'  → a-z + 0-9 mélangés
           'letter_num' → commence par lettres, finit par chiffres (ex: abc12)
           'num_letter' → commence par chiffres, finit par lettres (ex: 12abc)
    """
    alpha  = list("abcdefghijklmnopqrstuvwxyz")
    digit  = list("0123456789")
    alnum  = alpha + digit
    seen   = set()
    result = []
    max_tries = n * 30

    for _ in range(max_tries):
        if len(result) >= n:
            break
        if mode == "alpha":
            w = "".join(random.choices(alpha, k=length))
        elif mode == "digit":
            w = "".join(random.choices(digit, k=length))
        elif mode == "alnum":
            w = "".join(random.choices(alnum, k=length))
        elif mode == "letter_num":
            # moitié lettres | moitié chiffres  (arrondi vers lettres)
            nl = (length + 1) // 2
            nd = length - nl
            w = "".join(random.choices(alpha, k=nl)) + "".join(random.choices(digit, k=nd))
        elif mode == "num_letter":
            nd = length // 2
            nl = length - nd
            w = "".join(random.choices(digit, k=nd)) + "".join(random.choices(alpha, k=nl))
        else:
            w = "".join(random.choices(alnum, k=length))

        if w not in seen and is_valid(w):
            seen.add(w)
            result.append(w)

    return result


def _make_combo_cmd(length: int, mode: str, flag: str, label: str, color_key: str):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        if not USER_TOKEN:
            await ctx.send(embed=token_missing_embed()); return
        limit_real = max(1, min(limit, 30))
        n = max(limit_real * 20, 400)
        STATS["scans"] += 1
        msg = await ctx.send(embed=make_embed(
            description=f"```\n{flag}  {label} — génération...\n```",
            footer=f"{label.lower()} scan"))
        candidates = await asyncio.to_thread(_gen_combo, length, mode, n)
        found, checked = await _scan_engine(
            candidates, limit_real, msg, flag, label, C[color_key], check_available, False, ctx)
        if not found and checked == 0:
            remaining = max(0, int(RATE["until"] - time.time()))
            desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                    else "> Token invalide ou expiré.")
            await msg.edit(embed=discord.Embed(
                title="❌  Token refusé ou limite Discord", description=desc, color=C["error"]))
            return
        if found:
            lines = "\n".join(f"> `{p}`" for p in found)
            e = discord.Embed(
                title=f"{flag}  {len(found)} pseudo{'s' if len(found)>1 else ''} · {label}",
                description=lines, color=C[color_key])
            e.set_footer(text=f"meanings · {checked} scannés · {length} chars exactement")
        else:
            e = make_embed(f"{flag}  Aucun pseudo {label}",
                           f"> Relance pour réessayer.", C["error"], f"{checked} scannés")
        await msg.edit(embed=e)
    _inner.__doc__ = f"Scan {label}. Usage: +{label.lower().replace(' ','')} [nombre]"
    return _inner


# Tableau : (longueur, mode, flag, label, couleur)
_COMBO_CMDS = []
for _cl in range(4, 9):   # 4 → 8 chars
    _COMBO_CMDS += [
        (f"combo{_cl}",   _cl, "alnum",       "🔀", f"COMBO{_cl}",   "og"),
        (f"combo{_cl}l",  _cl, "alpha",        "🔡", f"COMBO{_cl}L",  "mix"),
        (f"combo{_cl}d",  _cl, "digit",        "🔢", f"COMBO{_cl}D",  "fr"),
        (f"combo{_cl}ln", _cl, "letter_num",   "🔣", f"COMBO{_cl}LN", "cyber"),
        (f"combo{_cl}nl", _cl, "num_letter",   "🔣", f"COMBO{_cl}NL", "cyber"),
    ]

for _cmd_name, _cl, _mode, _flag, _label, _col in _COMBO_CMDS:
    bot.command(name=_cmd_name)(_make_combo_cmd(_cl, _mode, _flag, _label, _col))


# ═══════════════════════════════════════════════════════════════════════════════
#  🇫🇷 🇬🇧 🌐 SCANS PAR DICTIONNAIRE (nom, source, label, couleur, flag, options)
# ═══════════════════════════════════════════════════════════════════════════════

def _fr_mix():
    return random.sample(ALL_FR, min(300, len(ALL_FR))) + random.sample(ALL_EN, min(300, len(ALL_EN)))


_DICT_SCANS = [
    ("meaningfr",  lambda: ALL_FR, "FR", "fr", "🇫🇷", {}),
    ("meaningfr2", lambda: random.sample(ALL_FR, min(500, len(ALL_FR))), "FR²", "fr", "🇫🇷", {}),
    ("frshort",    lambda: ALL_FR, "FR SHORT", "short", "⚡🇫🇷", {"min_len": 3, "max_len": 5}),
    ("frlong",     lambda: ALL_FR, "FR LONG", "fr", "📏🇫🇷", {"min_len": 8, "max_len": 16}),
    ("fraesthetic",lambda: ALL_FR, "FR AESTHETIC", "aesthetic", "✨🇫🇷", {"aesthetic": True}),
    ("frleet",     lambda: ALL_FR, "FR L33T", "cyber", "💻🇫🇷", {"leet": True}),
    ("meaningen",  lambda: ALL_EN, "EN", "en", "🇬🇧", {}),
    ("meaningen2", lambda: random.sample(ALL_EN, min(500, len(ALL_EN))), "EN²", "en", "🇬🇧", {}),
    ("enshort",    lambda: ALL_EN, "EN SHORT", "short", "⚡🇬🇧", {"min_len": 3, "max_len": 5}),
    ("enlong",     lambda: ALL_EN, "EN LONG", "en", "📏🇬🇧", {"min_len": 8, "max_len": 16}),
    ("enaesthetic",lambda: ALL_EN, "EN AESTHETIC", "aesthetic", "✨🇬🇧", {"aesthetic": True}),
    ("enleet",     lambda: ALL_EN, "EN L33T", "cyber", "💻🇬🇧", {"leet": True}),
    ("meaningmix", _fr_mix, "MIX", "mix", "🌐", {}),
    ("short",      lambda: ALL_FR + ALL_EN, "SHORT", "short", "⚡", {"min_len": 3, "max_len": 5}),
    ("medium",     lambda: ALL_FR + ALL_EN, "MEDIUM", "mix", "📐", {"min_len": 5, "max_len": 8}),
    ("long",       lambda: ALL_FR + ALL_EN, "LONG", "fr", "📏", {"min_len": 8, "max_len": 16}),
    ("og",         lambda: [w for w in ALL_FR + ALL_EN if re.match(r'^[a-z]{4,6}$', w)], "OG", "og", "👑", {"min_len": 4, "max_len": 6}),
    ("og3",        lambda: [w for w in ALL_FR + ALL_EN if len(w) == 3], "OG3", "og", "👑⚡", {"min_len": 3, "max_len": 3}),
    ("aesthetic",  lambda: ALL_FR + ALL_EN, "AESTHETIC", "aesthetic", "✨", {"aesthetic": True}),
    ("leet",       lambda: ALL_FR + ALL_EN, "L33T", "cyber", "💻", {"leet": True}),
    ("underscore", lambda: ALL_FR + ALL_EN, "UNDERSCORE", "mix", "〰️", {"underscore": True}),
    ("turbo",      lambda: ALL_FR + ALL_EN, "TURBO", "neon", "⚡⚡", {"speed": 0.1}),
    ("snail",      lambda: ALL_FR + ALL_EN, "SNAIL", "stats", "🐌", {"speed": 1.0}),
    ("hyper",      lambda: ALL_FR + ALL_EN, "HYPER", "neon", "🚀", {"speed": 0.15}),
    ("flash",      lambda: ALL_FR + ALL_EN, "FLASH", "og", "⚡", {"speed": 0.2}),
    ("rapid",      lambda: ALL_FR + ALL_EN, "RAPID", "check", "🏃", {"speed": 0.25}),
    ("crawl",      lambda: ALL_FR + ALL_EN, "CRAWL", "stats", "🐢", {"speed": 2.0}),
    ("checkrare",  lambda: ALL_FR + ALL_EN, "RARE", "og", "💎", {"min_len": 3, "max_len": 5}),
    # multilingues
    ("meaningde", lambda: LANGS["de"], "DE", "mix", "🇩🇪", {}),
    ("meaninges", lambda: LANGS["es"], "ES", "fr", "🇪🇸", {}),
    ("meaningit", lambda: LANGS["it"], "IT", "en", "🇮🇹", {}),
    ("meaningpt", lambda: LANGS["pt"], "PT", "nature", "🇵🇹", {}),
    ("meaningnl", lambda: LANGS["nl"], "NL", "ocean", "🇳🇱", {}),
    ("meaningpl", lambda: LANGS["pl"], "PL", "cyber", "🇵🇱", {}),
    ("meaningsv", lambda: LANGS["sv"], "SV", "ice", "🇸🇪", {}),
    ("meaningno", lambda: LANGS["no"], "NO", "viking", "🇳🇴", {}),
    ("meaningjp", lambda: LANGS["jp"], "JP", "samurai", "🇯🇵", {}),
    ("meaningko", lambda: LANGS["ko"], "KO", "neon", "🇰🇷", {}),
    ("meaningar", lambda: LANGS["ar"], "AR", "desert", "🇸🇦", {}),
    ("meaningru", lambda: LANGS["ru"], "RU", "ice", "🇷🇺", {}),
    # identités
    ("streamer", lambda: ["live","stream","clip","highlight","vod","chat","sub","raid","hype","train",
        "pog","lul","kek","omegalul","trihard","pepehands","pepelaugh","sadge","catjam",
        "copium","hopium","monkas","pepega","widepeepo","booba","nodders","nodge"], "STREAMER", "neon", "📺", {}),
    ("artist", lambda: ["canvas","brush","stroke","palette","sketch","draft","ink","line","curve","shape",
        "color","hue","tone","shade","tint","pigment","dye","stain","wash","blot",
        "abstract","surreal","realist","impressionist","expressionist","minimalist","maximalist"], "ARTIST", "color", "🎨", {}),
    ("hacker", lambda: THEMES["cyber"], "HACKER", "cyber", "👾", {}),
    ("developer", lambda: ["code","hack","debug","compile","deploy","push","pull","merge","fork","clone",
        "commit","branch","patch","hotfix","refactor","rebase","stash","diff","blame","grep",
        "sudo","chmod","bash","shell","script","kernel","daemon","thread","stack","heap"], "DEVELOPER", "cyber", "💻", {}),
    ("designer", lambda: ["pixel","vector","raster","gradient","blend","layer","mask","clip","path","anchor",
        "bezier","curve","font","serif","sans","mono","kerning","tracking","leading","weight",
        "grid","column","gutter","margin","padding","whitespace","contrast","ratio","scale","rhythm"], "DESIGNER", "aesthetic", "✏️", {}),
    ("creator", lambda: THEMES["brandable"], "CREATOR", "og", "✨", {}),
]


def _dict_cmd(src, label, color, flag, opts):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        await run_scan(ctx, src(), label, C[color], flag, limit, **opts)
    return _inner


for _name, _src, _label, _color, _flag, _opts in _DICT_SCANS:
    bot.command(name=_name)(_dict_cmd(_src, _label, _color, _flag, _opts))


# ── Scans à taille de pool fixe ───────────────────────────────────────────────

def _sized_cmd(size, flag, label, color, speed=None):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        if not USER_TOKEN:
            await ctx.send(embed=token_missing_embed()); return
        limit = max(1, min(limit, 30))
        STATS["scans"] += 1
        msg = await ctx.send(embed=make_embed(description=f"```\n{flag}  {label} — {size} candidats...\n```", footer=label.lower()))
        candidates = await build_pool_async(ALL_FR + ALL_EN, size, 3, 16)
        found, checked = await _scan_engine(candidates, limit, msg, flag, label, C[color], check_available, False, ctx, speed)
        await msg.edit(embed=result_embed(found, checked, flag, label, C[color]))
    return _inner


for _name, _size, _flag, _label, _color, _speed in [
    ("deep", 200, "🔬", "DEEP", "mix", None),
    ("burst", 50, "💥", "BURST", "neon", 0.1),
    ("mega", 300, "💪", "MEGA", "neon", None),
    ("ultra", 400, "⚡", "ULTRA", "og", None),
    ("blitz", 100, "⚡⚡", "BLITZ", "neon", 0.05),
]:
    bot.command(name=_name)(_sized_cmd(_size, _flag, _label, _color, _speed))


# ═══════════════════════════════════════════════════════════════════════════════
#  🔢 SCANS 4 CHARS — lettres + chiffres (a-z, 0-9) → 36^4 = 1 679 616 combos
# ═══════════════════════════════════════════════════════════════════════════════

_CHARS_ALPHA  = list("abcdefghijklmnopqrstuvwxyz")
_CHARS_DIGIT  = list("0123456789")
_CHARS_ALNUM  = _CHARS_ALPHA + _CHARS_DIGIT  # 36 chars → 36^4 = 1 679 616

def _gen_4c_random(n: int, charset=None) -> list:
    """Génère n combinaisons 4-chars aléatoires sans répétition (charset=alnum par défaut)."""
    cs = charset or _CHARS_ALNUM
    seen = set()
    result = []
    max_tries = n * 20
    for _ in range(max_tries):
        if len(result) >= n:
            break
        combo = "".join(random.choices(cs, k=4))
        if combo not in seen:
            seen.add(combo)
            result.append(combo)
    return result


def _gen_4c_chunk(offset: int, size: int, charset=None) -> list:
    """Retourne un slice déterministe de toutes les combos 4-chars (pour sweep exhaustif)."""
    cs = charset or _CHARS_ALNUM
    base = len(cs)
    result = []
    for i in range(offset, min(offset + size, base ** 4)):
        tmp, combo = i, []
        for _ in range(4):
            combo.append(cs[tmp % base])
            tmp //= base
        result.append("".join(reversed(combo)))
    return result


@bot.command(name="4calnum")
async def cmd_4c(ctx, limit: int = MAX_RESULTS):
    """Scan aléatoire de pseudos 4 chars (a-z + 0-9). Usage: +4calnum [nombre]"""
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 30))
    STATS["scans"] += 1
    n_candidates = max(limit * 10, 200)
    candidates = _gen_4c_random(n_candidates)
    msg = await ctx.send(embed=make_embed(
        description=f"```\n🔢  4C RANDOM — {n_candidates} candidats...\n```",
        footer="4c scan"))
    found, checked = await _scan_engine(
        candidates, limit, msg, "🔢", "4C RANDOM", C["og"], check_available, False, ctx)
    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                else "> Token invalide ou expiré.")
        await msg.edit(embed=discord.Embed(title="❌  Token refusé ou limite Discord",
                                           description=desc, color=C["error"]))
        return
    await msg.edit(embed=result_embed(found, checked, "🔢", "4C RANDOM", C["og"]))


@bot.command(name="4cletters")
async def cmd_4cletters(ctx, limit: int = MAX_RESULTS):
    """Scan aléatoire 4 chars lettres seulement (a-z). Usage: +4cletters [nombre]"""
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 30))
    STATS["scans"] += 1
    candidates = _gen_4c_random(max(limit * 10, 200), _CHARS_ALPHA)
    msg = await ctx.send(embed=make_embed(
        description="```\n🔡  4C LETTERS — scan...\n```", footer="4cletters"))
    found, checked = await _scan_engine(
        candidates, limit, msg, "🔡", "4C LETTERS", C["og"], check_available, False, ctx)
    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                else "> Token invalide ou expiré.")
        await msg.edit(embed=discord.Embed(title="❌  Token refusé ou limite Discord",
                                           description=desc, color=C["error"]))
        return
    await msg.edit(embed=result_embed(found, checked, "🔡", "4C LETTERS", C["og"]))


@bot.command(name="4cdigits")
async def cmd_4cdigits(ctx, limit: int = MAX_RESULTS):
    """Scan aléatoire 4 chars chiffres seulement (0-9). Usage: +4cdigits [nombre]"""
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 30))
    STATS["scans"] += 1
    candidates = _gen_4c_random(max(limit * 10, 200), _CHARS_DIGIT)
    msg = await ctx.send(embed=make_embed(
        description="```\n🔢  4C DIGITS — scan...\n```", footer="4cdigits"))
    found, checked = await _scan_engine(
        candidates, limit, msg, "🔢", "4C DIGITS", C["og"], check_available, False, ctx)
    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                else "> Token invalide ou expiré.")
        await msg.edit(embed=discord.Embed(title="❌  Token refusé ou limite Discord",
                                           description=desc, color=C["error"]))
        return
    await msg.edit(embed=result_embed(found, checked, "🔢", "4C DIGITS", C["og"]))


# ── SWEEPS EXHAUSTIFS (4, 5, 6 caractères — a-z + 0-9) ───────────────────────
# 4C : 38^4 = 2 085 136 (a-z 0-9 _ .) · 5C : 36^5 = 60 466 176 · 6C : 36^6 = 2 176 782 336
# Les combos sont générées à la volée à partir d'un offset (aucune liste géante en RAM).
SWEEP_CHUNK  = 1000   # combos testées par commande
SWEEP_LENGTHS = (4, 5, 6)
# Alphabet complet autorisé par Discord pour un pseudo : a-z, 0-9, "_" et "."
# (règle Discord : pas deux "." consécutifs → ces combos sont ignorées automatiquement)
_CHARS_FULL = _CHARS_ALNUM + ["_", "."]          # 38 chars → 38^4 = 2 085 136 combos brutes
SWEEP_CHARSETS = {4: _CHARS_FULL, 5: _CHARS_ALNUM, 6: _CHARS_ALNUM}
_SWEEP_STATE = {n: {"offset": 0, "total": len(SWEEP_CHARSETS[n]) ** n} for n in SWEEP_LENGTHS}
_4C_SWEEP_STATE = _SWEEP_STATE[4]  # compat


def _gen_chunk(offset: int, size: int, length: int, charset=None) -> list:
    """Slice déterministe de toutes les combos de `length` chars (ordre aaaa, aaab, ...)."""
    cs = charset or _CHARS_ALNUM
    base = len(cs)
    result = []
    for i in range(offset, min(offset + size, base ** length)):
        tmp, combo = i, []
        for _ in range(length):
            combo.append(cs[tmp % base])
            tmp //= base
        result.append("".join(reversed(combo)))
    return result


def _gen_valid_chunk(offset: int, size: int, length: int, charset) -> tuple:
    """Comme _gen_chunk mais ignore les pseudos invalides (".." consécutifs).
    Retourne (mots, index_bruts) pour pouvoir avancer le pointeur exactement."""
    words, idxs = [], []
    base = len(charset)
    for i in range(offset, min(offset + size, base ** length)):
        tmp, combo = i, []
        for _ in range(length):
            combo.append(charset[tmp % base])
            tmp //= base
        w = "".join(reversed(combo))
        if ".." in w:
            continue
        words.append(w); idxs.append(i)
    return words, idxs


def _sweep_word(offset: int, length: int) -> str:
    cs = SWEEP_CHARSETS[length]
    if offset >= len(cs) ** length:
        return "-"
    words, _ = _gen_valid_chunk(offset, 50, length, cs)
    return words[0] if words else "-"


async def _run_sweep(ctx, length: int, arg=None):
    state = _SWEEP_STATE[length]
    total = state["total"]

    # +Ncfull reset
    if arg and arg.lower() == "reset":
        state["offset"] = 0
        await ctx.send(embed=make_embed(f"✅  {length}C reset",
            f"> Sweep remis à zéro. `+{length}cfull` reprend depuis `{'a' * length}`.", C["check"]))
        return

    # +Ncfull [nombre]
    try:
        limit = int(arg) if arg else CONFIG["max_results"]
    except ValueError:
        await ctx.send(embed=make_embed("⚠️  Argument invalide",
            f"> Utilise `+{length}cfull [nombre]` ou `+{length}cfull reset`.", C["warn"]))
        return

    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 30))

    offset = state["offset"]
    if offset >= total:
        await ctx.send(embed=make_embed("✅  Sweep terminé",
            f"> Toutes les `{total:,}` combos ont été parcourues.\n> Utilise `+{length}cfull reset` pour recommencer.",
            C["check"]))
        return

    candidates, idxs = _gen_valid_chunk(offset, SWEEP_CHUNK, length, SWEEP_CHARSETS[length])
    if not candidates:   # tranche entièrement invalide : on la saute
        state["offset"] = min(total, offset + SWEEP_CHUNK)
        await ctx.send(embed=make_embed("⏭️  Tranche ignorée",
            "> Aucune combinaison valide dans cette tranche, relance la commande.", C["warn"]))
        return
    STATS["scans"] += 1
    pct = offset / total * 100
    msg = await ctx.send(embed=make_embed(
        description=f"```\n🗺️  {length}C FULL — offset {offset:,}/{total:,} ({pct:.4f}%)...\n```",
        footer=f"{length}cfull sweep"))
    found, checked = await _scan_engine(
        candidates, limit, msg, "🗺️", f"{length}C FULL", C["og"], check_available, False, ctx)

    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                else "> Token invalide ou expiré.")
        await msg.edit(embed=discord.Embed(title="❌  Token refusé ou limite Discord",
                                           description=desc, color=C["error"]))
        return

    # On n'avance que de ce qui a réellement été vérifié (plus de saut à la fin).
    state["offset"] = (idxs[min(checked, len(idxs)) - 1] + 1) if checked else offset
    new_pct = state["offset"] / total * 100
    e = result_embed(found, checked, "🗺️", f"{length}C FULL", C["og"])
    e.set_footer(text=f"meanings · sweep {state['offset']:,}/{total:,} ({new_pct:.4f}%) — +{length}cfull pour continuer")
    await msg.edit(embed=e)


def _make_sweep_cmds(length: int):
    async def _full(ctx, arg: str = None):
        await _run_sweep(ctx, length, arg)

    async def _reset(ctx):
        await _run_sweep(ctx, length, "reset")

    _full.__doc__ = f"Sweep exhaustif {length}C (toutes combos valides). Usage: +{length}cfull [nombre] | +{length}cfull reset"
    _reset.__doc__ = f"Remet le sweep {length}C à zéro."
    bot.command(name=f"{length}cfull")(_full)
    bot.command(name=f"{length}creset")(_reset)


for _n in SWEEP_LENGTHS:
    _make_sweep_cmds(_n)


# ── SWEEP UNIQUE 2 → 6 CARACTÈRES (alphabet complet, ~3,09 milliards) ───────────
ALL_LENGTHS = (2, 3, 4, 5, 6)
_ALL_SIZES  = [len(_CHARS_FULL) ** n for n in ALL_LENGTHS]
_ALL_STATE  = {"offset": 0, "total": sum(_ALL_SIZES)}   # 3 092 313 004 combos brutes


def _all_locate(offset: int):
    """offset global → (longueur, offset local, début global de cette longueur)."""
    base = 0
    for n, size in zip(ALL_LENGTHS, _ALL_SIZES):
        if offset < base + size:
            return n, offset - base, base
        base += size
    return None, 0, base


async def _run_allsweep(ctx, arg=None):
    total = _ALL_STATE["total"]

    if arg and arg.lower() == "reset":
        _ALL_STATE["offset"] = 0
        await ctx.send(embed=make_embed("✅  ALL reset",
            "> Sweep remis à zéro. `+allfull` reprend depuis `aa`.", C["check"]))
        return

    try:
        limit = int(arg) if arg else CONFIG["max_results"]
    except ValueError:
        await ctx.send(embed=make_embed("⚠️  Argument invalide",
            "> Utilise `+allfull [nombre]` ou `+allfull reset`.", C["warn"]))
        return

    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 30))

    offset = _ALL_STATE["offset"]
    length, local, base = _all_locate(offset)
    if length is None:
        await ctx.send(embed=make_embed("✅  Sweep terminé",
            f"> Toutes les `{total:,}` combos ont été parcourues.\n> Utilise `+allfull reset` pour recommencer.",
            C["check"]))
        return

    # une tranche ne chevauche jamais deux longueurs différentes
    size = min(SWEEP_CHUNK, len(_CHARS_FULL) ** length - local)
    candidates, idxs = _gen_valid_chunk(local, size, length, _CHARS_FULL)
    if not candidates:
        _ALL_STATE["offset"] = offset + size
        await ctx.send(embed=make_embed("⏭️  Tranche ignorée",
            "> Aucune combinaison valide dans cette tranche, relance la commande.", C["warn"]))
        return

    STATS["scans"] += 1
    pct = offset / total * 100
    msg = await ctx.send(embed=make_embed(
        description=f"```\n🗺️  ALL FULL — {length} chars — offset {offset:,}/{total:,} ({pct:.5f}%)...\n```",
        footer="allfull sweep"))
    found, checked = await _scan_engine(
        candidates, limit, msg, "🗺️", "ALL FULL", C["og"], check_available, False, ctx)

    if not found and checked == 0:
        remaining = max(0, int(RATE["until"] - time.time()))
        desc = (f"> Rate limit — réessaie dans ~`{remaining}s`." if remaining > 0
                else "> Token invalide ou expiré.")
        await msg.edit(embed=discord.Embed(title="❌  Token refusé ou limite Discord",
                                           description=desc, color=C["error"]))
        return

    if checked:
        _ALL_STATE["offset"] = base + idxs[min(checked, len(idxs)) - 1] + 1
    new_off = _ALL_STATE["offset"]
    e = result_embed(found, checked, "🗺️", "ALL FULL", C["og"])
    e.set_footer(text=f"meanings · sweep {new_off:,}/{total:,} ({new_off / total * 100:.5f}%) — +allfull pour continuer")
    await msg.edit(embed=e)


@bot.command(name="allfull", aliases=["megafull"])
async def cmd_allfull(ctx, arg: str = None):
    """Sweep unique 2→6 caractères (a-z 0-9 _ .) ~3,09 milliards. Usage: +allfull [nombre] | +allfull reset"""
    await _run_allsweep(ctx, arg)


@bot.command(name="allreset")
async def cmd_allreset(ctx):
    """Remet le sweep +allfull à zéro."""
    await _run_allsweep(ctx, "reset")


@bot.command(name="sweepstatus", aliases=["4cstatus", "5cstatus", "6cstatus"])
async def cmd_sweepstatus(ctx):
    """Progression des sweeps exhaustifs 4C / 5C / 6C."""
    e = discord.Embed(title="🗺️  Sweeps — Statut", color=C["og"])
    for n in SWEEP_LENGTHS:
        st = _SWEEP_STATE[n]
        pct = st["offset"] / st["total"] * 100
        e.add_field(name=f"{n} caractères",
                    value=f"`{st['offset']:,}` / `{st['total']:,}` ({pct:.4f}%)\nProchain : `{_sweep_word(st['offset'], n)}`",
                    inline=False)
    off, tot = _ALL_STATE["offset"], _ALL_STATE["total"]
    ln, _, _ = _all_locate(off)
    e.add_field(name="ALL (2 à 6 caractères)",
                value=f"`{off:,}` / `{tot:,}` ({off / tot * 100:.5f}%)\nLongueur en cours : `{ln or '-'}`",
                inline=False)
    await ctx.send(embed=e)


@bot.command(name="lucky")
async def cmd_lucky(ctx):
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    candidates = await build_pool_async(ALL_FR + ALL_EN, 30, 3, 10)
    msg = await ctx.send(embed=make_embed(description="```\n🍀  Lucky search...\n```", footer="lucky"))
    async with aiohttp.ClientSession() as session:
        for t in candidates:
            r = await check_available(session, t)
            if r in ("INVALID_TOKEN", "RATE_LIMITED"): break
            if r is True:
                await msg.edit(embed=discord.Embed(title="🍀  Lucky !", description=f"> `{t}` est libre !", color=C["lucky"]))
                return
            await asyncio.sleep(CHECK_DELAY)
    await msg.edit(embed=make_embed("🍀  Pas de chance", "Relance.", C["error"], "lucky"))


@bot.command(name="luckyvanity")
async def cmd_luckyvanity(ctx):
    raw = await build_pool_async(ALL_FR + ALL_EN, 50, 3, 10)
    candidates = [c for c in raw if is_vanity_allowed(c)]
    msg = await ctx.send(embed=make_embed(description="```\n🍀  Lucky vanity...\n```", footer="lucky vanity"))
    async with aiohttp.ClientSession() as session:
        for t in candidates:
            if await check_vanity(session, t) is True:
                await msg.edit(embed=discord.Embed(title="🍀  Lucky vanity !", description=f"> `discord.gg/{t}` libre !", color=C["lucky"]))
                return
            await asyncio.sleep(CHECK_DELAY)
    await msg.edit(embed=make_embed("🍀  Pas de chance", "Relance.", C["error"], "lucky vanity"))


@bot.command(name="vanitylucky")
async def cmd_vanitylucky(ctx):
    await cmd_luckyvanity(ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  🎨 THÈMES (pseudos)  — (commande, clé THEMES, label, couleur, flag)
# ═══════════════════════════════════════════════════════════════════════════════

_THEME_SCANS = [
    ("mythologie","mythologie","MYTHOLOGIE","myth","⚡🏛️"), ("astro","astro","ASTRO","astro","🔭"),
    ("nature","nature","NATURE","nature","🌿"), ("animal","animal","ANIMAL","animal","🐾"),
    ("food","food","FOOD","food","🍜"), ("sport","sport","SPORT","sport","🏆"),
    ("science","science","SCIENCE","science","⚗️"), ("music","music","MUSIC","music","🎵"),
    ("game","game","GAME","game","🎮"), ("pirate","pirate","PIRATE","pirate","🏴‍☠️"),
    ("cyber","cyber","CYBER","cyber","💻"), ("magic","magic","MAGIC","magic","🔮"),
    ("dark","dark","DARK","dark2","🌑"), ("fire","fire","FIRE","fire","🔥"),
    ("ice","ice","ICE","ice","❄️"), ("ocean","ocean","OCEAN","ocean","🌊"),
    ("storm","storm","STORM","storm","⛈️"), ("viking","viking","VIKING","viking","⚔️"),
    ("samurai","samurai","SAMURAI","samurai","🗡️"), ("aztec","aztec","AZTEC","aztec","🏔️"),
    ("celtic","celtic","CELTIC","celtic","🍀"), ("egyptian","egyptian","EGYPTIAN","egyptian","𓂀"),
    ("roman","roman","ROMAN","roman","⚔️"), ("spartan","spartan","SPARTAN","war","🛡️"),
    ("gemstones","gemstones","GEMS","gem","💎"), ("metals","metals","METALS","metal","🔩"),
    ("colorsen","colorsen","COLORS EN","color","🎨"), ("colorsfr","colorsfr","COLORS FR","color","🎨"),
    ("emotions","emotions","EMOTIONS","aesthetic","💭"), ("philosophy","philosophy","PHILOSOPHY","myth","📜"),
    ("duality","duality","DUALITY","mix","☯️"), ("pronounceable","pronounceable","PRONOUNCEABLE","info","🗣️"),
    ("brandable","brandable","BRANDABLE","stats","🚀"), ("gamer","gamer","GAMER","game","🎮"),
    ("ninja","ninja","NINJA","ninja","🥷"), ("gladiator","gladiator","GLADIATOR","war","⚔️"),
    ("dragon","dragon","DRAGON","fire","🐉"), ("witch","witch","WITCH","magic","🧙"),
    ("demon","demon","DEMON","dark2","👿"), ("angel","angel","ANGEL","color","👼"),
    ("forest","forest","FOREST","forest","🌲"), ("desert","desert","DESERT","desert","🏜️"),
    ("space","space","SPACE","space","🚀"), ("lore","lore","LORE","myth","📜"),
    ("mage","mage","MAGE","magic","🧙‍♂️"), ("warlock","warlock","WARLOCK","dark2","🔮"),
]


def _theme_cmd(key, label, color, flag):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        await run_scan(ctx, THEMES[key], label, C[color], flag, limit)
    return _inner


for _name, _key, _label, _color, _flag in _THEME_SCANS:
    bot.command(name=_name)(_theme_cmd(_key, _label, _color, _flag))


# ═══════════════════════════════════════════════════════════════════════════════
#  🔗 VANITY URLs
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="vanityfr")
async def cmd_vanityfr(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, ALL_FR, "FR", C["fr"], "🇫🇷", limit)


@bot.command(name="vanityen")
async def cmd_vanityen(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, ALL_EN, "EN", C["en"], "🇬🇧", limit)


@bot.command(name="vanitymix")
async def cmd_vanitymix(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, _fr_mix(), "MIX", C["mix"], "🌐", limit)


@bot.command(name="vanitycity")
async def cmd_vanitycity(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, ALL_CITIES, "CITY", C["city"], "🌍", limit, preserve_order=True)


@bot.command(name="vanityshort")
async def cmd_vanityshort(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, ALL_FR + ALL_EN + ALL_CITIES, "SHORT", C["short"], "⚡", limit, min_len=3, max_len=5)


@bot.command(name="vanityog")
async def cmd_vanityog(ctx, limit: int = MAX_RESULTS):
    og = [w for w in ALL_FR + ALL_EN if re.match(r'^[a-z]{4,6}$', w)]
    await run_vanity_scan(ctx, og, "OG", C["og"], "👑", limit, min_len=4, max_len=6)


@bot.command(name="vanitycolor")
async def cmd_vanitycolor(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["colorsen"] + THEMES["colorsfr"], "COLOR", C["color"], "🎨", limit)


@bot.command(name="vanitycolors")
async def cmd_vanitycolors(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["colorsen"] + THEMES["colorsfr"], "COLORS", C["color"], "🎨", limit)


def _vanity_sized(size, flag, label, color):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        limit = max(1, min(limit, 30))
        STATS["scans"] += 1
        msg = await ctx.send(embed=make_embed(description=f"```\n{flag}  Vanity {label}...\n```", footer=f"vanity{label.lower()}"))
        raw = await build_pool_async(ALL_FR + ALL_EN, size, 3, 16)
        candidates = [c for c in raw if is_vanity_allowed(c)]
        found, checked = await _scan_engine(candidates, limit, msg, flag, f"VANITY {label}", C[color], check_vanity, True, ctx)
        await msg.edit(embed=result_embed(found, checked, flag, f"VANITY {label}", C[color], is_vanity=True))
    return _inner


bot.command(name="vanitymega")(_vanity_sized(300, "💪", "MEGA", "neon"))
bot.command(name="vanitydeep")(_vanity_sized(200, "🔬", "DEEP", "mix"))

# (commande, clé THEMES, label, couleur, flag)
_VANITY_THEMES = [
    ("vanitymyth","mythologie","MYTH","myth","🏛️"), ("vanitymythologie","mythologie","MYTHOLOGIE","myth","🏛️"),
    ("vanityastro","astro","ASTRO","astro","🔭"), ("vanitygame","game","GAME","game","🎮"),
    ("vanitynature","nature","NATURE","nature","🌿"), ("vanitydark","dark","DARK","dark2","🌑"),
    ("vanityfire","fire","FIRE","fire","🔥"), ("vanityice","ice","ICE","ice","❄️"),
    ("vanitystorm","storm","STORM","storm","⛈️"), ("vanityocean","ocean","OCEAN","ocean","🌊"),
    ("vanityforest","forest","FOREST","forest","🌲"), ("vanitydesert","desert","DESERT","desert","🏜️"),
    ("vanitymetal","metals","METAL","metal","🔩"), ("vanitymetals","metals","METALS","metal","🔩"),
    ("vanitygem","gemstones","GEM","gem","💎"), ("vanitygemstones","gemstones","GEMS","gem","💎"),
    ("vanityanimal","animal","ANIMAL","animal","🐾"), ("vanityfood","food","FOOD","food","🍜"),
    ("vanitysport","sport","SPORT","sport","🏆"), ("vanitymusic","music","MUSIC","music","🎵"),
    ("vanitypirate","pirate","PIRATE","pirate","🏴‍☠️"), ("vanitycyber","cyber","CYBER","cyber","💻"),
    ("vanitymagic","magic","MAGIC","magic","🔮"), ("vanityviking","viking","VIKING","viking","⚔️"),
    ("vanitysamurai","samurai","SAMURAI","samurai","🗡️"), ("vanityspace","astro","SPACE","space","🚀"),
    ("vanityninja","ninja","NINJA","ninja","🥷"), ("vanitydragon","dragon","DRAGON","fire","🐉"),
    ("vanitywitch","witch","WITCH","magic","🧙"), ("vanitydemon","demon","DEMON","dark2","👿"),
    ("vanityangel","angel","ANGEL","color","👼"), ("vanityforest2","forest","FOREST","forest","🌲"),
    ("vanitydesert2","desert","DESERT","desert","🏜️"), ("vanityspace2","space","SPACE","space","🚀"),
    ("vanitydruid","celtic","DRUID","nature","🌿"), ("vanitywarlock","warlock","WARLOCK","dark2","🔮"),
    ("vanitylore","lore","LORE","myth","📜"), ("vanitymage","mage","MAGE","magic","🧙‍♂️"),
    ("vanityassassin","assassin2","ASSASSIN","dark2","🗡️"), ("vanitygladiator","gladiator","GLADIATOR","war","⚔️"),
    ("vanityspartan2","spartan","SPARTAN","war","🛡️"), ("vanityroman2","roman","ROMAN","roman","⚔️"),
    ("vanityviking2","viking","VIKING","viking","⚔️"), ("vanitysamurai2","samurai","SAMURAI","samurai","🗡️"),
    ("vanitycyber2","cyber","CYBER","cyber","💻"), ("vanityaztec","aztec","AZTEC","aztec","🏔️"),
    ("vanityceltic","celtic","CELTIC","celtic","🍀"), ("vanityegyptian","egyptian","EGYPTIAN","egyptian","𓂀"),
    ("vanityphilosophy","philosophy","PHILOSOPHY","myth","📜"), ("vanityemotions","emotions","EMOTIONS","aesthetic","💭"),
    ("vanityscience","science","SCIENCE","science","⚗️"), ("vanitygamer","gamer","GAMER","game","🎮"),
    ("vanityduality","duality","DUALITY","mix","☯️"), ("vanitygladiator2","gladiator","GLADIATOR","war","⚔️"),
    ("vanitydragon2","dragon","DRAGON","fire","🐉"), ("vanitywitch2","witch","WITCH","magic","🧙"),
    ("vanitydemon2","demon","DEMON","dark2","👿"), ("vanityangel2","angel","ANGEL","color","👼"),
]


def _vanity_theme_cmd(key, label, color, flag):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        await run_vanity_scan(ctx, THEMES[key], label, C[color], flag, limit)
    return _inner


for _name, _key, _label, _color, _flag in _VANITY_THEMES:
    bot.command(name=_name)(_vanity_theme_cmd(_key, _label, _color, _flag))


# ═══════════════════════════════════════════════════════════════════════════════
#  🎲 GÉNÉRATEURS / PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

async def _pool_scan(ctx, pool, limit, flag, label, color, intro, footer, n=80):
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    STATS["scans"] += 1
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description=f"```\n{flag}  {intro}...\n```", footer=footer))
    found, checked = await _scan_engine(pool[:n], max(1, min(limit, 30)), msg, flag, label, C[color], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, flag, label, C[color]))


@bot.command(name="adjnoun")
async def cmd_adjnoun(ctx, limit: int = MAX_RESULTS):
    adjs = ["dark","cold","bright","swift","dead","wild","free","bold","iron","steel",
            "black","white","red","blue","gold","silver","shadow","silent","fierce","brave"]
    nouns = ["wolf","blade","storm","fire","void","soul","heart","mind","eye","hand",
             "fist","claw","wing","horn","flame","stone","river","mountain","forest","ocean"]
    pool = [x for a in adjs for n in nouns for x in (f"{a}{n}", f"{a}_{n}") if is_valid(x)]
    await _pool_scan(ctx, pool, limit, "🎲", "ADJ+NOUN", "mix", "Génération adj+noun", "adjnoun")


@bot.command(name="coloranimal")
async def cmd_coloranimal(ctx, limit: int = MAX_RESULTS):
    colors = ["red","blue","black","white","grey","gold","silver","dark","bright","shadow",
              "iron","steel","midnight","crimson","azure","emerald","violet","amber","jade","coral"]
    animals = ["wolf","fox","bear","eagle","hawk","raven","owl","lion","tiger","dragon",
               "serpent","phoenix","lynx","panther","falcon","cobra","viper","shark","whale","orca"]
    pool = [f"{c}{a}" for c in colors for a in animals if is_valid(f"{c}{a}")]
    await _pool_scan(ctx, pool, limit, "🎨", "COLOR+ANIMAL", "color", "Génération couleur+animal", "coloranimal")


@bot.command(name="doubleword")
async def cmd_doubleword(ctx, limit: int = MAX_RESULTS):
    shorts = [w for w in ALL_FR + ALL_EN if 3 <= len(w) <= 5]
    random.shuffle(shorts)
    pool = []
    for a, b in itertools.combinations(shorts[:60], 2):
        combo = f"{a}{b}"
        if is_valid(combo) and len(combo) <= 10: pool.append(combo)
        if len(pool) >= 150: break
    await _pool_scan(ctx, pool, limit, "🔀", "DOUBLE WORD", "mix", "Génération double mots", "doubleword")


@bot.command(name="prefixword")
async def cmd_prefixword(ctx, limit: int = MAX_RESULTS):
    prefixes = ["neo","pro","ultra","hyper","super","mega","meta","omni","poly","mono",
                "anti","auto","bio","geo","micro","macro","cyber","techno","electro"]
    words = random.sample([w for w in ALL_EN if 3 <= len(w) <= 7], 30)
    pool = [f"{p}{w}" for p in prefixes for w in words if is_valid(f"{p}{w}")]
    await _pool_scan(ctx, pool, limit, "🔡", "PREFIX+WORD", "cyber", "Génération préfixe+mot", "prefixword")


@bot.command(name="wordsuffix")
async def cmd_wordsuffix(ctx, limit: int = MAX_RESULTS):
    suffixes = ["ify","ize","ism","ist","ite","oid","eon","ion","ark","ard","ling","ward",
                "less","ness","ful","able","ible","ive","ous","al"]
    words = random.sample([w for w in ALL_EN if 3 <= len(w) <= 7], 30)
    pool = [f"{w}{s}" for s in suffixes for w in words if is_valid(f"{w}{s}")]
    await _pool_scan(ctx, pool, limit, "🔠", "WORD+SUFFIX", "info", "Génération mot+suffixe", "wordsuffix")


@bot.command(name="wordnumber")
async def cmd_wordnumber(ctx, limit: int = MAX_RESULTS):
    words = random.sample([w for w in ALL_FR + ALL_EN if 4 <= len(w) <= 10], 100)
    pool = [f"{w}{n}" for w in words for n in ["1","2","3","7","0","00","01","69","77","99","x","xx"] if is_valid(f"{w}{n}")]
    await _pool_scan(ctx, pool, limit, "🔢", "MOT+CHIFFRE", "mix", "Génération mot+chiffre", "wordnumber")


@bot.command(name="novowel")
async def cmd_novowel(ctx, limit: int = MAX_RESULTS):
    pool = [w for w in ALL_FR + ALL_EN if not any(c in 'aeiou' for c in w) and is_valid(w)]
    await _pool_scan(ctx, pool, limit, "🔤", "NO VOWEL", "cyber", "Scan sans voyelles", "novowel")


@bot.command(name="palindrome")
async def cmd_palindrome(ctx, limit: int = MAX_RESULTS):
    pool = []
    for w in ALL_FR + ALL_EN:
        if w == w[::-1] and is_valid(w): pool.append(w)
        elif 3 <= len(w) <= 5:
            for pal in (w + w[::-1], w + w[-2::-1]):
                if is_valid(pal): pool.append(pal)
    await _pool_scan(ctx, pool, limit, "🔄", "PALINDROME", "aesthetic", "Scan palindromes", "palindrome")


@bot.command(name="mirror")
async def cmd_mirror(ctx, limit: int = MAX_RESULTS):
    words = random.sample([w for w in ALL_FR + ALL_EN if 3 <= len(w) <= 4], 100)
    pool = [w + w[::-1] for w in words if is_valid(w + w[::-1])]
    await _pool_scan(ctx, pool, limit, "🪞", "MIRROR", "mix", "Scan miroir", "mirror")


@bot.command(name="double")
async def cmd_double(ctx, limit: int = MAX_RESULTS):
    words = random.sample([w for w in ALL_FR + ALL_EN if 3 <= len(w) <= 4], 100)
    pool = [x for w in words for x in (w + w, w + "_" + w) if is_valid(x)]
    await _pool_scan(ctx, pool, limit, "✌️", "DOUBLE", "mix", "Scan double mots", "double")


@bot.command(name="initials")
async def cmd_initials(ctx, limit: int = MAX_RESULTS):
    base = random.sample(ALL_EN, min(200, len(ALL_EN)))
    pool = []
    for _ in range(400):
        a, b = random.choice(string.ascii_lowercase), random.choice(string.ascii_lowercase)
        combo = f"{a}{b}{random.choice(base)}"
        if a != b and is_valid(combo) and len(combo) <= 8: pool.append(combo)
    await _pool_scan(ctx, pool, limit, "🔡", "INITIALES", "info", "Scan initiales", "initials")


# ═══════════════════════════════════════════════════════════════════════════════
#  🔍 CHECK DIRECT
# ═══════════════════════════════════════════════════════════════════════════════

def _usage(cmd):
    return make_embed("❌  Usage", f"> `+{cmd}`", C["error"])


@bot.command(name="check")
async def cmd_check(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("check <pseudo>")); return
    mot = mot.lower().strip()
    if not is_valid(mot):
        await ctx.send(embed=make_embed("⚠️  Invalide", f"> `{mot}` invalide.", C["warn"])); return
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {mot}...\n```", footer="check"))
    async with aiohttp.ClientSession() as session:
        result = await check_available(session, mot)
    if result is True:
        e = discord.Embed(title="✅  Disponible", description=f"> `{mot}` est libre !", color=C["check"])
    elif result is False:
        e = discord.Embed(title="❌  Pris", description=f"> `{mot}` est utilisé.", color=C["error"])
    elif result == "RATE_LIMITED":
        e = make_embed("⏳  Limite Discord", f"> Réessaie dans ~`{int(max(0, RATE['until'] - time.time()))}s`.", C["warn"])
    else:
        e = make_embed("⚠️  Erreur", "> Réessaie.", C["warn"])
    e.set_footer(text=f"meanings · check · {mot}")
    await msg.edit(embed=e)


@bot.command(name="available")
async def cmd_available(ctx, *, mot: str = None):
    await cmd_check(ctx, mot=mot)


@bot.command(name="checkvanity")
async def cmd_checkvanity(ctx, *, code: str = None):
    if not code:
        await ctx.send(embed=_usage("checkvanity <code>")); return
    code = code.lower().strip()
    if not is_valid_vanity(code):
        await ctx.send(embed=make_embed("⚠️  Code invalide", "", C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check discord.gg/{code}...\n```", footer="check vanity"))
    async with aiohttp.ClientSession() as session:
        result = await check_vanity(session, code)
    if result is True:
        e = discord.Embed(title="✅  Vanity disponible", description=f"> `discord.gg/{code}` libre !", color=C["check"])
    elif result is False:
        e = discord.Embed(title="❌  Vanity pris", description=f"> `discord.gg/{code}` utilisé.", color=C["error"])
    else:
        e = make_embed("⚠️  Erreur", "> Réessaie.", C["warn"])
    e.set_footer(text=f"meanings · checkvanity · {code}")
    await msg.edit(embed=e)


def _status(r, bad="⚠️"):
    return "✅" if r is True else "❌" if r is False else bad


@bot.command(name="checkall")
async def cmd_checkall(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("checkall <mot>")); return
    mot = mot.lower().strip()
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check pseudo + vanity {mot}...\n```", footer="checkall"))
    async with aiohttp.ClientSession() as session:
        r_pseudo = await check_available(session, mot) if (is_valid(mot) and USER_TOKEN) else None
        await asyncio.sleep(0.3)
        r_vanity = await check_vanity(session, mot) if is_valid_vanity(mot) else None
    lbl = lambda r: "✅ libre" if r is True else "❌ pris" if r is False else "⚠️ indisponible"
    e = discord.Embed(title=f"🔍  Check all — `{mot}`", color=C["info"])
    e.add_field(name="👤  Pseudo Discord", value=f"> {lbl(r_pseudo)}", inline=True)
    e.add_field(name="🔗  discord.gg/" + mot, value=f"> {lbl(r_vanity)}", inline=True)
    e.set_footer(text="meanings · checkall")
    await msg.edit(embed=e)


@bot.command(name="taken")
async def cmd_taken(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("taken <pseudo>")); return
    mot = mot.lower().strip()
    if not is_valid(mot):
        await ctx.send(embed=make_embed("⚠️  Invalide", "", C["warn"])); return
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Vérifie si {mot} est pris...\n```", footer="taken"))
    async with aiohttp.ClientSession() as session:
        result = await check_available(session, mot)
    if result is False:
        e = discord.Embed(title="✅  Oui, pris", description=f"> `{mot}` est bien utilisé par quelqu'un.", color=C["warn"])
    elif result is True:
        e = discord.Embed(title="❌  Non, disponible", description=f"> `{mot}` n'est PAS pris — il est libre !", color=C["check"])
    else:
        e = make_embed("⚠️  Erreur", "> Réessaie.", C["warn"])
    e.set_footer(text=f"meanings · taken · {mot}")
    await msg.edit(embed=e)


@bot.command(name="checkstats")
async def cmd_checkstats(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("checkstats <pseudo>")); return
    mot = mot.lower().strip()
    length = len(mot)
    has_num = bool(re.search(r'\d', mot))
    has_under = '_' in mot
    vowels = sum(1 for c in mot if c in 'aeiou')
    consonants = length - vowels - mot.count('_') - sum(1 for c in mot if c.isdigit())
    rarity = {3:"🔴 Extrêmement rare",4:"🟠 Très rare",5:"🟡 Rare",6:"🟢 Peu commun",7:"🔵 Commun"}.get(length, "⚪ Fréquent")
    score = max(0, 100 - (length - 3) * 8 - (10 if has_num else 0) - (5 if has_under else 0))
    style = []
    if re.match(r'^[a-z]+$', mot): style.append("lettres seulement")
    if has_num: style.append("contient des chiffres")
    if has_under: style.append("contient underscore")
    if length <= 4: style.append("OG")
    if vowels == 0: style.append("sans voyelles")
    e = discord.Embed(title=f"📊  Analyse de `{mot}`", color=C["info"])
    e.add_field(name="📏  Longueur", value=f"`{length} chars`", inline=True)
    e.add_field(name="⭐  Score OG", value=f"`{score}/100`", inline=True)
    e.add_field(name="💎  Rareté", value=f"`{rarity}`", inline=True)
    e.add_field(name="🔤  Voyelles", value=f"`{vowels}`", inline=True)
    e.add_field(name="🔡  Consonnes", value=f"`{consonants}`", inline=True)
    e.add_field(name="🎨  Style", value="\n".join(f"> {s}" for s in style) or "> standard", inline=False)
    e.set_footer(text="meanings · checkstats — utilisez +check pour vérifier la dispo")
    await ctx.send(embed=e)


@bot.command(name="checkscore")
async def cmd_checkscore(ctx, *, mot: str = None):
    await cmd_checkstats(ctx, mot=mot)


async def _check_many(ctx, items, check_fn, fmt, title, footer):
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {len(items)} entrées...\n```", footer=footer))
    results = {}
    async with aiohttp.ClientSession() as session:
        for w in items:
            results[w] = await check_fn(session, w)
            await asyncio.sleep(CHECK_DELAY)
    lines = [f"> {_status(r)} `{fmt.format(w)}`" for w, r in results.items()]
    e = discord.Embed(title=title, description="\n".join(lines), color=C["info"])
    e.set_footer(text=f"meanings · {footer}")
    await msg.edit(embed=e)


@bot.command(name="checklist")
async def cmd_checklist(ctx, *, mots: str = None):
    if not mots:
        await ctx.send(embed=_usage("checklist mot1 mot2 mot3")); return
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    words = [w.lower().strip() for w in mots.split() if is_valid(w.lower().strip())][:10]
    if not words:
        await ctx.send(embed=make_embed("⚠️  Aucun mot valide", "", C["warn"])); return
    await _check_many(ctx, words, check_available, "{}", f"🔍  Check liste — {len(words)} pseudos", "checklist")


@bot.command(name="checkbulk")
async def cmd_checkbulk(ctx, *, mots: str = None):
    await cmd_checklist(ctx, mots=mots)


@bot.command(name="checklistvanity")
async def cmd_checklistvanity(ctx, *, mots: str = None):
    if not mots:
        await ctx.send(embed=_usage("checklistvanity code1 code2")); return
    codes = [c.lower().strip() for c in mots.split() if is_valid_vanity(c.lower().strip())][:10]
    if not codes:
        await ctx.send(embed=make_embed("⚠️  Aucun code valide", "", C["warn"])); return
    await _check_many(ctx, codes, check_vanity, "discord.gg/{}", f"🔍  Check vanity liste — {len(codes)}", "checklist vanity")


@bot.command(name="checkrandom")
async def cmd_checkrandom(ctx, limit: int = 5):
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    limit = max(1, min(limit, 10))
    words = [w for w in random.sample(ALL_FR + ALL_EN, min(30, len(ALL_FR) + len(ALL_EN))) if is_valid(w)][:limit]
    await _check_many(ctx, words, check_available, "{}", "🎲  Check aléatoire", "checkrandom")


@bot.command(name="recheck")
async def cmd_recheck(ctx):
    mine = [(k, w) for k, ws in WATCHLIST.items() for w in ws if w["user_id"] == ctx.author.id]
    if not mine:
        await ctx.send(embed=make_embed("👀  Watchlist vide", "> Rien à rechequer.", C["info"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Recheck de {len(mine)} entrée(s)...\n```", footer="recheck"))
    freed = []
    async with aiohttp.ClientSession() as session:
        for key, _w in mine:
            is_v = key.startswith("vanity:")
            target = key[7:] if is_v else (key[6:] if key.startswith("snipe:") else key)
            result = await (check_vanity if is_v else check_available)(session, target)
            await asyncio.sleep(0.5)
            if result is True:
                freed.append((key, is_v, target))
    if freed:
        lines = [f"> ✅ `{'discord.gg/' + t if v else t}` est libre !" for k, v, t in freed]
        e = discord.Embed(title=f"🔔  {len(freed)} libéré(s) !", description="\n".join(lines), color=C["check"])
        for key, _, _ in freed:
            WATCHLIST.pop(key, None)
    else:
        e = make_embed("👀  Rien de libéré", "Toujours pris. Réessaie plus tard.", C["warn"], "recheck")
    e.set_footer(text="meanings · recheck")
    await msg.edit(embed=e)


@bot.command(name="snipe")
async def cmd_snipe(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("snipe <pseudo>")); return
    mot = mot.lower().strip()
    key = f"snipe:{mot}"
    WATCHLIST.setdefault(key, []).append({"user_id": ctx.author.id, "channel_id": ctx.channel.id, "type": "snipe"})
    e = discord.Embed(title="🎯  Snipe activé",
        description=f"> `{mot}` surveillé toutes les **30 minutes**.\n> Tu seras pingé immédiatement.", color=C["lucky"])
    e.set_footer(text="meanings · snipe · +unwatch pour annuler")
    await ctx.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
#  🎨 STYLE / OUTILS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="style")
async def cmd_style(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("style <mot>")); return
    mot = mot.lower().strip()
    variants = {}
    ae = [v for v in to_aesthetic(mot) if is_valid(v) and v != mot]
    lt, rv, un = to_leet(mot), to_reverse(mot), to_underscore(mot)
    if ae: variants["✨ aesthetic"] = ae[:3]
    if is_valid(lt) and lt != mot: variants["💻 l33t"] = [lt]
    if is_valid(rv) and rv != mot: variants["🔄 reverse"] = [rv]
    if is_valid(un) and un != mot: variants["〰️ underscore"] = [un]
    if not variants:
        await ctx.send(embed=make_embed("⚠️  Aucune variante", "", C["warn"])); return
    lines = [f"> `{mot}` → variantes :\n"]
    for label, vs in variants.items():
        for v in vs: lines.append(f"> {label} → `{v}`")
    e = discord.Embed(title="🎨  Variantes style", description="\n".join(lines), color=C["aesthetic"])
    e.set_footer(text="meanings · style — +check pour vérifier la dispo")
    await ctx.send(embed=e)


@bot.command(name="combine")
async def cmd_combine(ctx, mot1: str = None, mot2: str = None):
    if not mot1 or not mot2:
        await ctx.send(embed=_usage("combine mot1 mot2")); return
    a, b = mot1.lower().strip(), mot2.lower().strip()
    cands = [f"{a}{b}", f"{b}{a}", f"{a}_{b}", f"{b}_{a}", f"{a}{b[:3]}", f"{a[:3]}{b}", f"{a[0]}{b}", f"{a}{b[0]}"]
    combos = [x for x in dict.fromkeys(cands) if is_valid(x)]
    if not combos:
        await ctx.send(embed=make_embed("⚠️  Aucune combo valide", "", C["warn"])); return
    e = discord.Embed(title=f"🔀  Combos `{a}` × `{b}`", description="\n".join(f"> `{c}`" for c in combos), color=C["mix"])
    e.set_footer(text="meanings · combine — +check pour vérifier")
    await ctx.send(embed=e)


@bot.command(name="suggest")
async def cmd_suggest(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("suggest <mot>")); return
    mot = mot.lower().strip()

    def work():
        s = set()
        for w in ALL_FR + ALL_EN:
            if (w.startswith(mot[:3]) or mot[:4] in w) and w != mot and is_valid(w): s.add(w)
            if len(s) >= 40: break
        r = list(s)
        random.shuffle(r)
        return r[:15]

    result = await asyncio.to_thread(work)
    e = discord.Embed(title=f"💡  Suggestions pour `{mot}`",
                      description="\n".join(f"> `{w}`" for w in result) or "> Aucune suggestion.", color=C["info"])
    e.set_footer(text="meanings · suggest — +check pour vérifier")
    await ctx.send(embed=e)


@bot.command(name="from")
async def cmd_from(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("from <mot>")); return
    mot = mot.lower().strip()
    base = random.sample(ALL_FR + ALL_EN, min(500, len(ALL_FR) + len(ALL_EN)))
    pool = set()
    for w in base:
        for x in (f"{mot}{w}", f"{w}{mot}", f"{mot}_{w}", f"{w}_{mot}"):
            if is_valid(x) and len(x) <= 16: pool.add(x)
        if len(pool) >= 30: break
    result = list(pool)
    random.shuffle(result)
    e = discord.Embed(title=f"🔗  Pseudos depuis `{mot}`",
                      description="\n".join(f"> `{p}`" for p in result[:15]) or "> Aucun résultat.", color=C["mix"])
    e.set_footer(text="meanings · from — +check pour vérifier")
    await ctx.send(embed=e)


async def _affix_scan(ctx, pool, flag, label):
    if not pool:
        await ctx.send(embed=make_embed("⚠️  Aucun mot", f"> Aucun candidat pour `{label}`.", C["warn"])); return
    random.shuffle(pool)
    await _pool_scan(ctx, pool, MAX_RESULTS, flag, label, "info", f"Scan {label} ({min(len(pool), 60)} candidats)", "affix scan", n=60)


@bot.command(name="prefix")
async def cmd_prefix_search(ctx, *, pfx: str = None):
    if not pfx:
        await ctx.send(embed=_usage("prefix <préfixe>")); return
    pfx = pfx.lower().strip()
    await _affix_scan(ctx, [w for w in ALL_FR + ALL_EN if w.startswith(pfx) and is_valid(w)], "🔡", f"PREFIX:{pfx}")


@bot.command(name="suffix")
async def cmd_suffix_search(ctx, *, sfx: str = None):
    if not sfx:
        await ctx.send(embed=_usage("suffix <suffixe>")); return
    sfx = sfx.lower().strip()
    await _affix_scan(ctx, [w for w in ALL_FR + ALL_EN if w.endswith(sfx) and is_valid(w)], "🔠", f"SUFFIX:{sfx}")


@bot.command(name="contains")
async def cmd_contains(ctx, *, letters: str = None):
    if not letters:
        await ctx.send(embed=_usage("contains <lettres>")); return
    letters = letters.lower().strip()
    await _affix_scan(ctx, [w for w in ALL_FR + ALL_EN if letters in w and is_valid(w)], "🔍", f"CONTAINS:{letters}")


# ═══════════════════════════════════════════════════════════════════════════════
#  👀 WATCH
# ═══════════════════════════════════════════════════════════════════════════════

def _target_of(key):
    if key.startswith("vanity:"): return key[7:]
    if key.startswith("snipe:"):  return key[6:]
    return key


@bot.command(name="watch")
async def cmd_watch(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("watch <pseudo>")); return
    mot = mot.lower().strip()
    lst = WATCHLIST.setdefault(mot, [])
    if any(w["user_id"] == ctx.author.id for w in lst):
        await ctx.send(embed=make_embed("⚠️  Déjà surveillé", f"> Tu surveilles déjà `{mot}`.", C["warn"])); return
    lst.append({"user_id": ctx.author.id, "channel_id": ctx.channel.id, "type": "pseudo"})
    e = discord.Embed(title="👀  Surveillance activée",
        description=f"> `{mot}` surveillé.\n> Ping dès qu'il se libère.", color=C["watch"])
    e.set_footer(text="meanings · watch · check environ toutes les 6h")
    await ctx.send(embed=e)


@bot.command(name="watchvanity")
async def cmd_watchvanity(ctx, *, code: str = None):
    if not code:
        await ctx.send(embed=_usage("watchvanity <code>")); return
    code = code.lower().strip()
    lst = WATCHLIST.setdefault(f"vanity:{code}", [])
    if any(w["user_id"] == ctx.author.id for w in lst):
        await ctx.send(embed=make_embed("⚠️  Déjà surveillé", "", C["warn"])); return
    lst.append({"user_id": ctx.author.id, "channel_id": ctx.channel.id, "type": "vanity"})
    e = discord.Embed(title="👀  Vanity surveillé", description=f"> `discord.gg/{code}` surveillé.", color=C["watch"])
    e.set_footer(text="meanings · watchvanity")
    await ctx.send(embed=e)


@bot.command(name="unwatch")
async def cmd_unwatch(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("unwatch <pseudo>")); return
    mot = mot.lower().strip()
    removed = False
    for key in (mot, f"vanity:{mot}", f"snipe:{mot}"):
        if key in WATCHLIST:
            before = len(WATCHLIST[key])
            WATCHLIST[key] = [w for w in WATCHLIST[key] if w["user_id"] != ctx.author.id]
            if len(WATCHLIST[key]) < before: removed = True
            if not WATCHLIST[key]: del WATCHLIST[key]
    e = make_embed("🗑️  Supprimé", f"> `{mot}` retiré.", C["stats"]) if removed else \
        make_embed("⚠️  Introuvable", f"> `{mot}` pas dans ta watchlist.", C["warn"])
    await ctx.send(embed=e)


@bot.command(name="watchlist")
async def cmd_watchlist(ctx):
    mine = []
    for key, watchers in WATCHLIST.items():
        if any(w["user_id"] == ctx.author.id for w in watchers):
            paused = key in WATCH_PAUSED
            icon = "⏸️" if paused else ("🎯" if key.startswith("snipe:") else ("🔗" if key.startswith("vanity:") else "👤"))
            if key.startswith("vanity:"): mine.append(f"> {icon}  `discord.gg/{key[7:]}`")
            elif key.startswith("snipe:"): mine.append(f"> {icon}  `{key[6:]}` (snipe 30min)")
            else: mine.append(f"> {icon}  `{key}`")
    if not mine:
        e = make_embed("📋  Watchlist vide", "> `+watch <pseudo>` pour ajouter.", C["info"])
    else:
        e = discord.Embed(title=f"📋  Watchlist — {len(mine)} entrée{'s' if len(mine) > 1 else ''}",
            description="\n".join(mine), color=C["watch"])
        e.set_footer(text="meanings · +unwatch pour supprimer · +recheck pour vérifier maintenant")
    await ctx.send(embed=e)


@bot.command(name="watchpause")
async def cmd_watchpause(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("watchpause <pseudo>")); return
    mot = mot.lower().strip()
    for key in (mot, f"vanity:{mot}", f"snipe:{mot}"):
        WATCH_PAUSED.add(key)
    await ctx.send(embed=make_embed("⏸️  Surveillance en pause", f"> `{mot}` ne sera plus checké jusqu'à `+watchresume {mot}`.", C["warn"]))


@bot.command(name="watchresume")
async def cmd_watchresume(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("watchresume <pseudo>")); return
    mot = mot.lower().strip()
    for key in (mot, f"vanity:{mot}", f"snipe:{mot}"):
        WATCH_PAUSED.discard(key)
    await ctx.send(embed=make_embed("▶️  Surveillance reprise", f"> `{mot}` est à nouveau surveillé.", C["check"]))


@bot.command(name="watchstatus")
async def cmd_watchstatus(ctx):
    mine = [k for k, ws in WATCHLIST.items() if any(w["user_id"] == ctx.author.id for w in ws)]
    if not mine:
        await ctx.send(embed=make_embed("👀  Watchlist vide", "", C["info"])); return
    lines = []
    for key in mine:
        status = "⏸️ en pause" if key in WATCH_PAUSED else "✅ actif"
        interval = "30min" if key.startswith("snipe:") else "6h"
        lines.append(f"> {status} `{_target_of(key)}` — check toutes les {interval}")
    e = discord.Embed(title="👀  Statut watchlist", description="\n".join(lines), color=C["watch"])
    e.set_footer(text="meanings · watchstatus")
    await ctx.send(embed=e)


@bot.command(name="watchcount")
async def cmd_watchcount(ctx):
    mine = sum(1 for ws in WATCHLIST.values() for w in ws if w["user_id"] == ctx.author.id)
    total = sum(len(ws) for ws in WATCHLIST.values())
    e = discord.Embed(title="👀  Compteur watchlist", color=C["info"])
    e.add_field(name="Tes surveillances", value=f"`{mine}`", inline=True)
    e.add_field(name="Total bot", value=f"`{total}`", inline=True)
    e.set_footer(text="meanings · watchcount")
    await ctx.send(embed=e)


@bot.command(name="watchexport")
async def cmd_watchexport(ctx):
    mine = [_target_of(k) for k, ws in WATCHLIST.items() if any(w["user_id"] == ctx.author.id for w in ws)]
    if not mine:
        await ctx.send(embed=make_embed("📋  Watchlist vide", "", C["info"])); return
    e = discord.Embed(title="📤  Export watchlist", description="```\n" + "\n".join(mine) + "\n```", color=C["info"])
    e.set_footer(text="meanings · watchexport")
    await ctx.send(embed=e)


async def watch_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(1800)
        if not WATCHLIST: continue
        try:
            async with aiohttp.ClientSession() as session:
                for key in list(WATCHLIST.keys()):
                    if key not in WATCHLIST or key in WATCH_PAUSED: continue
                    is_v = key.startswith("vanity:")
                    is_s = key.startswith("snipe:")
                    target = _target_of(key)
                    if not is_s and random.random() > 1 / 12:  # watch normal ≈ toutes les 6h
                        continue
                    result = await (check_vanity if is_v else check_available)(session, target)
                    await asyncio.sleep(1)
                    if result is True:
                        for w in WATCHLIST.pop(key, []):
                            try:
                                channel = bot.get_channel(w["channel_id"])
                                if channel:
                                    fmt = f"discord.gg/{target}" if is_v else target
                                    e = discord.Embed(title="🔔  Libéré !",
                                        description=f"<@{w['user_id']}> → `{fmt}` est disponible !", color=C["check"])
                                    e.set_footer(text="meanings · watchlist")
                                    await channel.send(embed=e)
                            except Exception as ex:
                                print(f"[WARN] notif watch : {ex}", flush=True)
        except Exception as ex:
            print(f"[WARN] watch_loop : {ex}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  ⭐ FAVORIS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="fav")
async def cmd_fav(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("fav <pseudo>")); return
    mot = mot.lower().strip()
    if mot in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Déjà en favori", "", C["warn"])); return
    if len(FAVORITES[ctx.author.id]) >= 20:
        await ctx.send(embed=make_embed("⚠️  Limite", "Max 20 favoris.", C["warn"])); return
    FAVORITES[ctx.author.id].append(mot)
    e = discord.Embed(title="⭐  Ajouté", description=f"> `{mot}` sauvegardé.", color=C["lucky"])
    e.set_footer(text="meanings · +favlist pour voir · +checkfavs pour vérifier")
    await ctx.send(embed=e)


@bot.command(name="unfav")
async def cmd_unfav(ctx, *, mot: str = None):
    if not mot:
        await ctx.send(embed=_usage("unfav <pseudo>")); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas trouvé", "", C["warn"])); return
    FAVORITES[ctx.author.id].remove(mot)
    FAV_NOTES[ctx.author.id].pop(mot, None)
    FAV_TAGS[ctx.author.id].pop(mot, None)
    await ctx.send(embed=make_embed("🗑️  Supprimé", f"> `{mot}` retiré.", C["stats"]))


@bot.command(name="favlist")
async def cmd_favlist(ctx):
    favs = FAVORITES[ctx.author.id]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide", "> +fav <pseudo> pour ajouter.", C["info"])); return
    lines = []
    for p in favs:
        tag = FAV_TAGS[ctx.author.id].get(p, "")
        note = FAV_NOTES[ctx.author.id].get(p, "")
        line = f"> `{p}`"
        if tag: line += f"  🏷️ {tag}"
        if note: line += f"  — _{note}_"
        lines.append(line)
    e = discord.Embed(title=f"⭐  Favoris — {len(favs)}", description="\n".join(lines), color=C["lucky"])
    e.set_footer(text="meanings · +checkfavs pour vérifier la dispo")
    await ctx.send(embed=e)


@bot.command(name="checkfavs")
async def cmd_checkfavs(ctx):
    favs = list(FAVORITES[ctx.author.id])
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide", "", C["info"])); return
    if not USER_TOKEN:
        await ctx.send(embed=token_missing_embed()); return
    await _check_many(ctx, favs, check_available, "{}", "⭐  Check favoris", "checkfavs")


@bot.command(name="favnote")
async def cmd_favnote(ctx, mot: str = None, *, note: str = None):
    if not mot or not note:
        await ctx.send(embed=_usage("favnote <pseudo> <note>")); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas en favori", "Ajoute d'abord avec +fav.", C["warn"])); return
    FAV_NOTES[ctx.author.id][mot] = note
    await ctx.send(embed=make_embed("📝  Note ajoutée", f"> `{mot}` → _{note}_", C["info"]))


@bot.command(name="favtag")
async def cmd_favtag(ctx, mot: str = None, *, tag: str = None):
    if not mot or not tag:
        await ctx.send(embed=_usage("favtag <pseudo> <tag>")); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas en favori", "", C["warn"])); return
    FAV_TAGS[ctx.author.id][mot] = tag.lower()
    await ctx.send(embed=make_embed("🏷️  Tag ajouté", f"> `{mot}` tagué `{tag}`", C["info"]))


@bot.command(name="favfilter")
async def cmd_favfilter(ctx, *, tag: str = None):
    if not tag:
        await ctx.send(embed=_usage("favfilter <tag>")); return
    tag = tag.lower().strip()
    favs = [p for p in FAVORITES[ctx.author.id] if FAV_TAGS[ctx.author.id].get(p, "") == tag]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Aucun favori", f"> Aucun favori avec le tag `{tag}`.", C["warn"])); return
    e = discord.Embed(title=f"⭐  Favoris — tag `{tag}`", description="\n".join(f"> `{p}`" for p in favs), color=C["lucky"])
    e.set_footer(text="meanings · favfilter")
    await ctx.send(embed=e)


@bot.command(name="favexport")
async def cmd_favexport(ctx):
    favs = FAVORITES[ctx.author.id]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide", "", C["info"])); return
    e = discord.Embed(title=f"📤  Export favoris — {len(favs)}", description="```\n" + "\n".join(favs) + "\n```", color=C["lucky"])
    e.set_footer(text="meanings · favexport")
    await ctx.send(embed=e)


@bot.command(name="favclear")
async def cmd_favclear(ctx):
    n = len(FAVORITES[ctx.author.id])
    if not n:
        await ctx.send(embed=make_embed("⭐  Vide", "", C["info"])); return
    FAVORITES[ctx.author.id].clear()
    FAV_NOTES[ctx.author.id].clear()
    FAV_TAGS[ctx.author.id].clear()
    await ctx.send(embed=make_embed("🗑️  Favoris vidés", f"> {n} favori(s) supprimé(s).", C["stats"]))


# ═══════════════════════════════════════════════════════════════════════════════
#  📊 STATS PERSO & SERVEUR
# ═══════════════════════════════════════════════════════════════════════════════

def _my_rank(uid):
    rank = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)
    return next((i + 1 for i, x in enumerate(rank) if x[0] == uid), None)


def _my_watch(uid):
    return sum(1 for ws in WATCHLIST.values() for w in ws if w["user_id"] == uid)


@bot.command(name="mystats")
async def cmd_mystats(ctx):
    hist = HISTORY[ctx.author.id]
    found = sum(1 for h in hist if h["available"])
    vanity_found = sum(1 for h in hist if h["available"] and h.get("vanity"))
    e = discord.Embed(title=f"📊  Mes stats — {ctx.author.display_name}", color=C["profile"])
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.add_field(name="✅  Trouvés total", value=f"`{found}`", inline=True)
    e.add_field(name="👤  Pseudos", value=f"`{found - vanity_found}`", inline=True)
    e.add_field(name="🔗  Vanity", value=f"`{vanity_found}`", inline=True)
    e.add_field(name="🏆  Rang", value=f"`#{_my_rank(ctx.author.id) or '?'}`", inline=True)
    e.add_field(name="⭐  Favoris", value=f"`{len(FAVORITES[ctx.author.id])}`", inline=True)
    e.add_field(name="👀  Watchlist", value=f"`{_my_watch(ctx.author.id)}`", inline=True)
    e.set_footer(text="meanings · mystats")
    await ctx.send(embed=e)


@bot.command(name="myprofile")
async def cmd_myprofile(ctx):
    hist = HISTORY[ctx.author.id]
    found = sum(1 for h in hist if h["available"])
    favs = FAVORITES[ctx.author.id]
    best = None
    for h in hist:
        if h["available"] and (best is None or len(h["pseudo"]) < len(best)): best = h["pseudo"]
    e = discord.Embed(title=f"👤  Profil — {ctx.author.display_name}", color=C["profile"])
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.add_field(name="✅  Total trouvés", value=f"`{found}`", inline=True)
    e.add_field(name="🏆  Rang", value=f"`#{_my_rank(ctx.author.id) or '?'}`", inline=True)
    e.add_field(name="⭐  Favoris", value=f"`{len(favs)}`", inline=True)
    e.add_field(name="👀  Watchlist", value=f"`{_my_watch(ctx.author.id)}`", inline=True)
    e.add_field(name="🏅  Meilleur pseudo", value=f"`{best}`" if best else "`—`", inline=True)
    if favs:
        e.add_field(name="⭐  Derniers favoris", value="\n".join(f"> `{p}`" for p in favs[-3:]), inline=False)
    e.set_footer(text="meanings · myprofile")
    await ctx.send(embed=e)


@bot.command(name="mybest")
async def cmd_mybest(ctx):
    hist = [h for h in HISTORY[ctx.author.id] if h["available"]]
    if not hist:
        await ctx.send(embed=make_embed("🏅  Aucun trouvé", "Lance un scan d'abord.", C["info"])); return
    best = min(hist, key=lambda h: len(h["pseudo"]))
    e = discord.Embed(title="🏅  Ton meilleur pseudo trouvé",
        description=f"> `{best['pseudo']}` — {len(best['pseudo'])} chars", color=C["og"])
    e.set_footer(text="meanings · mybest")
    await ctx.send(embed=e)


@bot.command(name="myrank")
async def cmd_myrank(ctx):
    r = _my_rank(ctx.author.id)
    if r is None:
        await ctx.send(embed=make_embed("🏆  Pas encore classé", "Lance un scan pour entrer dans le classement.", C["info"])); return
    e = discord.Embed(title="🏆  Ton rang",
        description=f"> **#{r}** avec `{LEADERBOARD[ctx.author.id]}` pseudos trouvés", color=C["og"])
    e.set_footer(text="meanings · myrank")
    await ctx.send(embed=e)


@bot.command(name="history")
async def cmd_history(ctx):
    hist = HISTORY[ctx.author.id][-20:]
    if not hist:
        await ctx.send(embed=make_embed("📜  Historique vide", "Lance un scan.", C["info"])); return
    lines = []
    for h in reversed(hist[-15:]):
        icon = "✅" if h["available"] else "❌"
        pfx = "discord.gg/" if h.get("vanity") else ""
        ts = datetime.fromtimestamp(h["ts"]).strftime("%H:%M")
        lines.append(f"> {icon} `{pfx}{h['pseudo']}` — {ts}")
    e = discord.Embed(title=f"📜  Historique — {len(hist)} entrées", description="\n".join(lines), color=C["info"])
    e.set_footer(text="meanings · history")
    await ctx.send(embed=e)


@bot.command(name="myhistory")
async def cmd_myhistory(ctx):
    await cmd_history(ctx)


@bot.command(name="leaderboard")
async def cmd_leaderboard(ctx):
    if not LEADERBOARD:
        await ctx.send(embed=make_embed("🏆  Vide", "Pas encore de scans.", C["info"])); return
    top = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    lines = []
    for i, (uid, count) in enumerate(top):
        try:
            name = (await bot.fetch_user(uid)).display_name
        except Exception:
            name = f"User#{uid}"
        lines.append(f"> {medals[i]} **{name}** — `{count}` trouvés")
    e = discord.Embed(title="🏆  Leaderboard", description="\n".join(lines), color=C["og"])
    e.set_footer(text="meanings · leaderboard")
    await ctx.send(embed=e)


@bot.command(name="serverleaderboard")
async def cmd_serverleaderboard(ctx):
    await cmd_leaderboard(ctx)


@bot.command(name="mytime")
async def cmd_mytime(ctx):
    hist = HISTORY[ctx.author.id]
    if not hist:
        await ctx.send(embed=make_embed("📜  Aucun historique", "Lance un scan.", C["info"])); return
    first = datetime.fromtimestamp(hist[0]["ts"]).strftime("%d/%m/%Y %H:%M")
    last = datetime.fromtimestamp(hist[-1]["ts"]).strftime("%d/%m/%Y %H:%M")
    e = discord.Embed(title="⏱️  Ton activité", color=C["profile"])
    e.add_field(name="📅  Premier scan", value=f"`{first}`", inline=True)
    e.add_field(name="📅  Dernier scan", value=f"`{last}`", inline=True)
    e.add_field(name="📊  Total entries", value=f"`{len(hist)}`", inline=True)
    e.set_footer(text="meanings · mytime")
    await ctx.send(embed=e)


@bot.command(name="myscore")
async def cmd_myscore(ctx):
    found = sum(1 for h in HISTORY[ctx.author.id] if h["available"])
    e = discord.Embed(title="🏆  Ton score", color=C["og"])
    e.add_field(name="⭐  Score", value=f"`{found * 10} pts`", inline=True)
    e.add_field(name="🏆  Rang", value=f"`#{_my_rank(ctx.author.id) or '?'}`", inline=True)
    e.add_field(name="✅  Trouvés", value=f"`{found}`", inline=True)
    e.set_footer(text="meanings · myscore")
    await ctx.send(embed=e)


@bot.command(name="serverstats")
async def cmd_serverstats(ctx):
    e = discord.Embed(title="📊  Stats serveur", color=C["stats"])
    e.add_field(name="🔍  Scans", value=f"`{STATS['scans']:,}`", inline=True)
    e.add_field(name="✅  Trouvés", value=f"`{STATS['found']:,}`", inline=True)
    e.add_field(name="📡  Checks", value=f"`{STATS['checked']:,}`", inline=True)
    e.add_field(name="👀  Watch actifs", value=f"`{sum(len(ws) for ws in WATCHLIST.values())}`", inline=True)
    e.add_field(name="⭐  Favoris total", value=f"`{sum(len(v) for v in FAVORITES.values())}`", inline=True)
    e.add_field(name="📜  Historique", value=f"`{sum(len(v) for v in HISTORY.values())}`", inline=True)
    e.add_field(name="🏆  Chasseurs", value=f"`{len(LEADERBOARD)}`", inline=True)
    e.set_footer(text="meanings · serverstats")
    await ctx.send(embed=e)


@bot.command(name="globalstats")
async def cmd_globalstats(ctx):
    await cmd_serverstats(ctx)


@bot.command(name="serverrecord")
async def cmd_serverrecord(ctx):
    if not LEADERBOARD:
        await ctx.send(embed=make_embed("🏆  Aucun record", "Pas encore de scans.", C["info"])); return
    best_user = max(LEADERBOARD, key=LEADERBOARD.get)
    try:
        name = (await bot.fetch_user(best_user)).display_name
    except Exception:
        name = f"User#{best_user}"
    best_pseudo = None
    for h in HISTORY.get(best_user, []):
        if h["available"] and (best_pseudo is None or len(h["pseudo"]) < len(best_pseudo)): best_pseudo = h["pseudo"]
    e = discord.Embed(title="🏆  Record serveur", color=C["og"])
    e.add_field(name="👑  Meilleur chasseur", value=f"> **{name}** — `{LEADERBOARD[best_user]}` trouvés", inline=False)
    if best_pseudo:
        e.add_field(name="🏅  Plus court pseudo", value=f"> `{best_pseudo}` ({len(best_pseudo)} chars)", inline=False)
    e.set_footer(text="meanings · serverrecord")
    await ctx.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
#  📊 INFOS BOT
# ═══════════════════════════════════════════════════════════════════════════════

def _uptime():
    up = int(time.time() - START_TIME)
    return up // 3600, (up % 3600) // 60, up % 60


@bot.command(name="stats")
async def cmd_stats(ctx):
    h, m, _ = _uptime()
    e = discord.Embed(title="📊  meanings — statistiques", color=C["stats"])
    e.add_field(name="🔍  Scans", value=f"`{STATS['scans']:,}`", inline=True)
    e.add_field(name="✅  Trouvés", value=f"`{STATS['found']:,}`", inline=True)
    e.add_field(name="📡  Checks", value=f"`{STATS['checked']:,}`", inline=True)
    e.add_field(name="⌨️  Commandes", value=f"`{STATS['commands']:,}`", inline=True)
    e.add_field(name="👀  Watchlist", value=f"`{len(WATCHLIST):,}`", inline=True)
    e.add_field(name="⏱️  Uptime", value=f"`{h}h {m}m`", inline=True)
    e.add_field(name="📚  Dicos", value=f"`{len(ALL_FR):,} FR · {len(ALL_EN):,} EN · {len(ALL_CITIES):,} villes`", inline=False)
    e.set_footer(text="meanings · stats")
    await ctx.send(embed=e)


@bot.command(name="botinfo")
async def cmd_botinfo(ctx):
    h, m, _ = _uptime()
    e = discord.Embed(title="🤖  meanings — infos", color=C["info"])
    e.add_field(name="📌  Version", value="`4.0`", inline=True)
    e.add_field(name="⏱️  Uptime", value=f"`{h}h {m}m`", inline=True)
    e.add_field(name="🏓  Latence", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    e.add_field(name="🇫🇷  FR", value=f"`{len(ALL_FR):,}`", inline=True)
    e.add_field(name="🇬🇧  EN", value=f"`{len(ALL_EN):,}`", inline=True)
    e.add_field(name="🌍  Villes", value=f"`{len(ALL_CITIES):,}`", inline=True)
    e.add_field(name="🎨  Thèmes", value=f"`{len(THEMES)}`", inline=True)
    e.add_field(name="⚙️  Config",
        value=f"`PARALLEL={CONFIG['parallel']} · DELAY={CONFIG['check_delay']}s · MAX={CONFIG['max_results']}`", inline=False)
    e.set_footer(text="meanings v4.0")
    await ctx.send(embed=e)


@bot.command(name="ping")
async def cmd_ping(ctx):
    lat = round(bot.latency * 1000)
    color = C["check"] if lat < 100 else C["warn"] if lat < 300 else C["error"]
    await ctx.send(embed=discord.Embed(title="🏓  Pong !", description=f"> Latence : `{lat}ms`", color=color))


@bot.command(name="resetrate")
async def cmd_resetrate(ctx):
    """Reset manuel du cooldown 429 sur la route pomelo."""
    old = max(0, int(RATE["until"] - time.time()))
    RATE["until"] = 0.0
    if old > 0:
        desc = f"> Cooldown de `{old}s` annulé. Tu peux relancer tes scans."
    else:
        desc = "> Aucun cooldown actif — déjà libre."
    await ctx.send(embed=make_embed("✅  Rate reset", desc, C["check"]))


@bot.command(name="uptime")
async def cmd_uptime(ctx):
    h, m, s = _uptime()
    await ctx.send(embed=discord.Embed(title="⏱️  Uptime", description=f"> `{h}h {m}m {s}s`", color=C["info"]))


@bot.command(name="version")
async def cmd_version(ctx):
    e = discord.Embed(title="📌  Version", description=f"> `meanings v4.0`\n> {TOTAL_CMDS} commandes · {len(THEMES)} thèmes", color=C["info"])
    e.set_footer(text="meanings v4.0")
    await ctx.send(embed=e)


@bot.command(name="config")
async def cmd_config(ctx):
    e = discord.Embed(title="⚙️  Configuration actuelle", color=C["info"])
    e.add_field(name="🔢  MAX_RESULTS", value=f"`{CONFIG['max_results']}`", inline=True)
    e.add_field(name="⏱️  CHECK_DELAY", value=f"`{CONFIG['check_delay']}s`", inline=True)
    e.add_field(name="🔀  PARALLEL", value=f"`{CONFIG['parallel']}`", inline=True)
    e.set_footer(text="meanings · config · +setmax/setdelay/setparallel pour modifier (admin)")
    await ctx.send(embed=e)


@bot.command(name="apistatus")
async def cmd_apistatus(ctx):
    msg = await ctx.send(embed=make_embed(description="```\n🔎  Test API Discord...\n```", footer="apistatus"))
    t0 = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://discord.com/api/v9/gateway", timeout=aiohttp.ClientTimeout(total=5)) as r:
                lat = round((time.time() - t0) * 1000)
                if r.status == 200:
                    e = discord.Embed(title="✅  API Discord — OK", description=f"> Gateway : `{lat}ms`\n> Status : `{r.status}`", color=C["check"])
                else:
                    e = discord.Embed(title="⚠️  API Discord — Dégradée", description=f"> Status : `{r.status}`", color=C["warn"])
        except Exception as ex:
            e = make_embed("❌  API Discord — Hors ligne", f"> `{ex}`", C["error"])
    e.set_footer(text="meanings · apistatus")
    await msg.edit(embed=e)


@bot.command(name="status")
async def cmd_status(ctx):
    h, m, _ = _uptime()
    lat = round(bot.latency * 1000)
    color = C["check"] if lat < 100 else C["warn"] if lat < 300 else C["error"]
    e = discord.Embed(title="🟢  Bot en ligne", color=color)
    e.add_field(name="🏓  Latence", value=f"`{lat}ms`", inline=True)
    e.add_field(name="⏱️  Uptime", value=f"`{h}h {m}m`", inline=True)
    e.add_field(name="📊  Scans", value=f"`{STATS['scans']:,}`", inline=True)
    e.set_footer(text="meanings · status")
    await ctx.send(embed=e)


@bot.command(name="dico")
async def cmd_dico(ctx):
    total = len(ALL_FR) + len(ALL_EN) + len(ALL_CITIES)
    e = discord.Embed(title="📚  Dicos chargés", color=C["info"])
    e.add_field(name="🇫🇷  Français", value=f"`{len(ALL_FR):,} mots`", inline=True)
    e.add_field(name="🇬🇧  Anglais", value=f"`{len(ALL_EN):,} mots`", inline=True)
    e.add_field(name="🌍  Villes", value=f"`{len(ALL_CITIES):,}`", inline=True)
    e.add_field(name="📊  Total", value=f"`{total:,} entrées`", inline=False)
    e.set_footer(text="meanings · dico · +themes pour la liste des thèmes")
    await ctx.send(embed=e)


@bot.command(name="themes")
async def cmd_themes(ctx):
    names = sorted(THEMES.keys())
    lines = [f"> `+{n}`" for n in names]
    third = math.ceil(len(lines) / 3)
    e = discord.Embed(title=f"🎨  Thèmes disponibles — {len(names)}", color=C["info"])
    for i in range(3):
        chunk = lines[i * third:(i + 1) * third]
        if chunk: e.add_field(name="​", value="\n".join(chunk), inline=True)
    e.set_footer(text="meanings · themes · +<theme> pour scanner")
    await ctx.send(embed=e)


@bot.command(name="commands")
async def cmd_commands(ctx):
    e = discord.Embed(title=f"⌨️  Total commandes : {TOTAL_CMDS}", color=C["info"])
    for key, cat in HELP_CATEGORIES.items():
        e.add_field(name=f"{cat['emoji']} {cat['label']}", value=f"`{len(cat['cmds'])} cmds`", inline=True)
    e.set_footer(text="meanings · +helpall pour tout voir")
    await ctx.send(embed=e)


@bot.command(name="about")
async def cmd_about(ctx):
    h, m, _ = _uptime()
    e = discord.Embed(title="✦  meanings — About",
        description=("> Bot de recherche de pseudos et vanity Discord.\n"
                     f"> **{TOTAL_CMDS} commandes** · Préfixe `+`\n"
                     f"> `{len(ALL_FR):,}` mots FR · `{len(ALL_EN):,}` mots EN · `{len(ALL_CITIES):,}` villes\n"
                     f"> `{len(THEMES)}` thèmes · Uptime `{h}h {m}m`"), color=C["info"])
    e.set_footer(text="meanings v4.0 · +help pour l'aide")
    await ctx.send(embed=e)


@bot.command(name="ratelimit")
async def cmd_ratelimit(ctx):
    delay, parallel = CONFIG["check_delay"], CONFIG["parallel"]
    e = discord.Embed(title="⚡  Rate Limit Info", color=C["info"])
    e.add_field(name="⏱️  Délai", value=f"`{delay}s`", inline=True)
    e.add_field(name="🔀  Parallèle", value=f"`{parallel}`", inline=True)
    e.add_field(name="📊  Checks/min", value=f"~`{round(60 / delay * parallel)}`", inline=True)
    e.add_field(name="💡  Conseil", value="> Si tu vois des 429, utilise `+setdelay 0.5` ou `+snail`", inline=False)
    e.set_footer(text="meanings · ratelimit")
    await ctx.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
#  🛡️ ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

def is_owner(ctx):
    if ctx.author.id == OWNER_ID: return True
    return bool(ctx.guild and ctx.author.guild_permissions.administrator)


async def _deny(ctx):
    await ctx.send(embed=make_embed("❌  Admin only", "", C["error"]))


@bot.command(name="setmax")
async def cmd_setmax(ctx, n: int = None):
    if not is_owner(ctx): return await _deny(ctx)
    if not n or not (1 <= n <= 50):
        await ctx.send(embed=_usage("setmax <1-50>")); return
    CONFIG["max_results"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour", f"> MAX_RESULTS = `{n}`", C["admin"]))


@bot.command(name="setdelay")
async def cmd_setdelay(ctx, n: float = None):
    if not is_owner(ctx): return await _deny(ctx)
    if n is None or not (0.05 <= n <= 5.0):
        await ctx.send(embed=_usage("setdelay <0.05-5.0>")); return
    CONFIG["check_delay"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour", f"> CHECK_DELAY = `{n}s`", C["admin"]))


@bot.command(name="setparallel")
async def cmd_setparallel(ctx, n: int = None):
    if not is_owner(ctx): return await _deny(ctx)
    if not n or not (1 <= n <= 20):
        await ctx.send(embed=_usage("setparallel <1-20>")); return
    CONFIG["parallel"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour", f"> PARALLEL = `{n}`", C["admin"]))


@bot.command(name="resetstats")
async def cmd_resetstats(ctx):
    if not is_owner(ctx): return await _deny(ctx)
    STATS.update({"scans": 0, "found": 0, "checked": 0, "commands": 0})
    await ctx.send(embed=make_embed("✅  Stats réinitialisées", "", C["admin"]))


@bot.command(name="clearwatchlist")
async def cmd_clearwatchlist(ctx):
    if not is_owner(ctx): return await _deny(ctx)
    n = len(WATCHLIST)
    WATCHLIST.clear()
    await ctx.send(embed=make_embed("✅  Watchlist vidée", f"> {n} entrée(s) supprimée(s).", C["admin"]))


@bot.command(name="blacklistadd")
async def cmd_blacklistadd(ctx, *, mot: str = None):
    if not is_owner(ctx): return await _deny(ctx)
    if not mot:
        await ctx.send(embed=_usage("blacklistadd <mot>")); return
    VANITY_BLACKLIST.add(mot.lower().strip())
    await ctx.send(embed=make_embed("✅  Ajouté", f"> `{mot}` ajouté à la blacklist.", C["admin"]))


@bot.command(name="blacklistremove")
async def cmd_blacklistremove(ctx, *, mot: str = None):
    if not is_owner(ctx): return await _deny(ctx)
    if not mot:
        await ctx.send(embed=_usage("blacklistremove <mot>")); return
    VANITY_BLACKLIST.discard(mot.lower().strip())
    await ctx.send(embed=make_embed("✅  Retiré", f"> `{mot}` retiré de la blacklist.", C["admin"]))


@bot.command(name="blacklistshow")
async def cmd_blacklistshow(ctx):
    if not is_owner(ctx): return await _deny(ctx)
    items = sorted(VANITY_BLACKLIST)
    e = discord.Embed(title=f"🚫  Blacklist — {len(items)} mots",
        description=", ".join(f"`{w}`" for w in items[:50]), color=C["admin"])
    e.set_footer(text="meanings · blacklist")
    await ctx.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
#  ❓ HELP
# ═══════════════════════════════════════════════════════════════════════════════

def _lenrows():
    rar = {3:"🔴 Extrêmement rares",4:"🟠 Très rares",5:"🟡 Rares",6:"🟢 Peu communs",7:"🔵 Communs",8:"⚪ Fréquents"}
    return [(f"+len{n} [n] / +{n}c [n] / +{n}l [n]", f"Pseudos de {n} chars {rar.get(n, '')}".strip()) for n in range(3, 13)]


HELP_CATEGORIES = {
    "scan": {"emoji": "🔍", "label": "Scan Pseudos", "cmds": [
        ("+meaningfr [n]","Scan pseudos français"),("+meaningfr2 [n]","Scan FR — autre lot"),
        ("+frshort [n]","FR courts"),("+frlong [n]","FR longs"),("+fraesthetic [n]","FR aesthetic"),("+frleet [n]","FR l33t"),
        ("+meaningen [n]","Scan pseudos anglais"),("+meaningen2 [n]","Scan EN — autre lot"),
        ("+enshort [n]","EN courts"),("+enlong [n]","EN longs"),("+enaesthetic [n]","EN aesthetic"),("+enleet [n]","EN l33t"),
        ("+meaningmix [n]","Mix FR + EN"),("+short [n]","Courts"),("+medium [n]","Moyens"),("+long [n]","Longs"),
        ("+og [n]","OG 4-6 chars"),("+og3 [n]","OG 3 chars"),("+aesthetic [n]","Aesthetic"),("+leet [n]","L33t"),
        ("+underscore [n]","Underscore"),("+lucky","1 pseudo dispo"),("+turbo [n]","Ultra rapide"),
        ("+snail [n]","Lent"),("+burst [n]","50 candidats"),("+deep [n]","200 candidats"),
        ("+mega [n]","300 candidats"),("+ultra [n]","400 candidats"),("+blitz [n]","Vitesse max"),
        ("+hyper [n]","0.15s"),("+flash [n]","0.2s"),("+rapid [n]","0.25s"),("+crawl [n]","2s"),
        ("+checkrare [n]","Rares 3-5 chars"),
    ]},
    "longueur": {"emoji": "🔢", "label": "Longueur Exacte", "cmds": _lenrows()},
    "generation": {"emoji": "🎲", "label": "Générateurs & Patterns", "cmds": [
        ("+adjnoun [n]","adjectif+nom"),("+coloranimal [n]","couleur+animal"),("+doubleword [n]","mot+mot courts"),
        ("+prefixword [n]","préfixe+mot"),("+wordsuffix [n]","mot+suffixe"),("+wordnumber [n]","mot+chiffre"),
        ("+novowel [n]","sans voyelles"),("+palindrome [n]","palindromes"),("+mirror [n]","miroirs"),
        ("+double [n]","mot répété"),("+initials [n]","initiales"),
        ("+streamer [n]","streamer"),("+artist [n]","artiste"),("+hacker [n]","hacker"),
        ("+developer [n]","dev"),("+designer [n]","design"),("+creator [n]","créateur"),
    ]},
    "multilingue": {"emoji": "🌍", "label": "Multilingue", "cmds": [
        (f"+meaning{c} [n]", f"Pseudos {c.upper()}") for c in ("de","es","it","pt","nl","pl","sv","no","jp","ko","ar","ru")]},
    "themes": {"emoji": "🎨", "label": "Thèmes Pseudos", "cmds": [(f"+{t[0]} [n]", t[2].title()) for t in _THEME_SCANS]},
    "vanity": {"emoji": "🔗", "label": "Vanity URLs", "cmds": [
        ("+vanityfr [n]","FR"),("+vanityen [n]","EN"),("+vanitymix [n]","Mix"),("+vanitycity [n]","Villes"),
        ("+vanityshort [n]","Courts"),("+vanityog [n]","OG"),("+luckyvanity","1 vanity dispo"),
        ("+vanitymega [n]","300 candidats"),("+vanitydeep [n]","200 candidats"),("+vanitycolor [n]","Couleurs"),
    ] + [(f"+{t[0]} [n]", f"Vanity {t[2].title()}") for t in _VANITY_THEMES]},
    "check": {"emoji": "🔎", "label": "Check & Vérification", "cmds": [
        ("+check <pseudo>","Dispo d'un pseudo"),("+checkvanity <code>","Dispo d'une vanity"),
        ("+checkall <mot>","Pseudo ET vanity"),("+available <pseudo>","Alias de +check"),
        ("+taken <pseudo>","Pseudo PRIS ?"),("+checkstats <pseudo>","Analyse"),("+checkscore <pseudo>","Score OG"),
        ("+checklist mot1 mot2...","Jusqu'à 10 pseudos"),("+checkbulk ...","Alias checklist"),
        ("+checklistvanity code...","Jusqu'à 10 vanity"),("+checkrandom [n]","Aléatoires"),
        ("+recheck","Recheck watchlist"),("+snipe <pseudo>","Surveillance 30min"),
    ]},
    "outils": {"emoji": "🛠️", "label": "Outils & Génération", "cmds": [
        ("+style <mot>","Variantes style"),("+combine mot1 mot2","Combos"),("+suggest <mot>","Suggestions"),
        ("+from <mot>","Pseudos depuis un mot"),("+prefix <pfx>","Scan préfixe"),("+suffix <sfx>","Scan suffixe"),
        ("+contains <lettres>","Scan contenant"),
        ("+4cfull [n|reset]","Sweep 4 chars a-z 0-9 _ . (2,08 M)"),("+5cfull [n|reset]","Sweep 5 chars (60 M)"),
        ("+6cfull [n|reset]","Sweep 6 chars (2,18 Md)"),("+allfull [n|reset]","Sweep unique 2-6 chars (3,09 Md)"),("+sweepstatus","Progression des sweeps"),
    ]},
    "watch": {"emoji": "👀", "label": "Surveillance (Watch)", "cmds": [
        ("+watch <pseudo>","Surveille (6h)"),("+watchvanity <code>","Surveille une vanity"),
        ("+snipe <pseudo>","Surveille (30min)"),("+unwatch <pseudo>","Arrête"),("+watchlist","Ta watchlist"),
        ("+watchpause <pseudo>","Pause"),("+watchresume <pseudo>","Reprise"),("+watchstatus","Statut"),
        ("+watchcount","Compteur"),("+watchexport","Export"),("+recheck","Check immédiat"),
    ]},
    "favoris": {"emoji": "⭐", "label": "Favoris", "cmds": [
        ("+fav <pseudo>","Ajoute"),("+unfav <pseudo>","Retire"),("+favlist","Liste"),("+checkfavs","Check dispo"),
        ("+favnote <pseudo> <note>","Note"),("+favtag <pseudo> <tag>","Tag"),("+favfilter <tag>","Filtre"),
        ("+favexport","Export"),("+favclear","Vide tout"),
    ]},
    "stats": {"emoji": "📊", "label": "Stats Personnelles", "cmds": [
        ("+mystats","Stats"),("+myprofile","Profil"),("+mybest","Meilleur pseudo"),("+myrank","Rang"),
        ("+myscore","Score"),("+mytime","Activité"),("+history","Historique"),("+myhistory","Alias history"),
        ("+leaderboard","Top 10"),("+serverleaderboard","Alias leaderboard"),("+serverstats","Stats serveur"),
        ("+globalstats","Alias serverstats"),("+serverrecord","Record serveur"),
    ]},
    "bot": {"emoji": "🤖", "label": "Infos Bot", "cmds": [
        ("+stats","Stats globales"),("+botinfo","Infos"),("+ping","Latence"),("+uptime","Uptime"),
        ("+version","Version"),("+config","Config"),("+dico","Dicos"),("+themes","Thèmes"),
        ("+commands","Nb de commandes"),("+about","À propos"),("+ratelimit","Rate limit"),("+status","Statut"),
        ("+apistatus","API Discord"),("+help [cat]","Aide"),("+helpall","Tout"),
    ]},
    "admin": {"emoji": "🛡️", "label": "Admin", "cmds": [
        ("+setmax <n>","Max résultats"),("+setdelay <n>","Délai"),("+setparallel <n>","Parallèle"),
        ("+resetstats","Reset stats"),("+clearwatchlist","Vide watchlist"),("+blacklistadd <mot>","Blacklist +"),
        ("+blacklistremove <mot>","Blacklist -"),("+blacklistshow","Blacklist"),
    ]},
}


import difflib

# ── Style "Help" : accueil + menu déroulant, pages Précédent / Suivant ───────
_ARG_RE = re.compile(r"\s+(\[|<|mot\d|\S*\.\.\.).*$")


def _cmd_names(usage):
    """'+check <pseudo>' -> ['+check'] · '+len3 [n] / +3c [n]' -> ['+len3', '+3c']"""
    out = []
    for part in usage.split(" / "):
        n = _ARG_RE.sub("", part.strip()).strip()
        if n:
            out.append(n)
    return out or [usage.strip()]


def _chip_names(cat):
    seen, out = set(), []
    for usage, _ in cat["cmds"]:
        n = _cmd_names(usage)[0]
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _find_cmd(query):
    q = query.lower().lstrip("+").strip()
    for key, cat in HELP_CATEGORIES.items():
        for usage, desc in cat["cmds"]:
            names = [n.lstrip("+").lower() for n in _cmd_names(usage)]
            if q in names:
                return key, cat, usage, desc, _cmd_names(usage)
    return None


def _build_help_home_embed():
    lines = "\n".join(f"`{len(c['cmds']):02d}`  **{c['label']}**" for c in HELP_CATEGORIES.values())
    e = discord.Embed(
        title="Help - meanings",
        description=(
            "**Bienvenue dans le système d'aide de meanings !**\n\n"
            "Sélectionnez une catégorie ci-dessous pour découvrir toutes les commandes disponibles.\n"
            f"Commandes disponibles : `{TOTAL_CMDS}` · Préfixe : `+`\n\n"
            f"{lines}\n\n"
            "`+help <commande>` · `+help <catégorie>` · `+help all`"),
        color=C["info"])
    e.set_footer(text="✦ meanings")
    return e


def _pack(blocks, budget=3600):
    pages, cur = [], ""
    for b in blocks:
        if cur and len(cur) + len(b) + 2 > budget:
            pages.append(cur)
            cur = b
        else:
            cur = f"{cur}\n\n{b}" if cur else b
    if cur:
        pages.append(cur)
    return pages


def _build_cat_pages(key):
    """Catégorie détaillée : `usage` — description."""
    cat = HELP_CATEGORIES[key]
    lines = [f"`{u}` — {d}" for u, d in cat["cmds"]]
    pages, cur = [], ""
    for ln in lines:
        if cur and len(cur) + len(ln) + 1 > 3600:
            pages.append(cur)
            cur = ln
        else:
            cur = f"{cur}\n{ln}" if cur else ln
    if cur:
        pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        e = discord.Embed(title=f"{cat['emoji']}  {cat['label']} ({len(cat['cmds'])})", description=p, color=C["info"])
        e.set_footer(text=f"✦ {cat['label']} · page {i + 1}/{len(pages)}")
        out.append(e)
    return out


def _build_all_pages():
    """Toutes les catégories en listes de puces compactes (comme =help all)."""
    blocks = []
    for key, cat in HELP_CATEGORIES.items():
        total = len(cat["cmds"])
        chunks, cur = [], ""
        for n in _chip_names(cat):
            chip = f"`{n}`"
            add = chip if not cur else f", {chip}"
            if len(cur) + len(add) > 1500:
                chunks.append(cur)
                cur = chip
            else:
                cur += add
        if cur:
            chunks.append(cur)
        for i, ch in enumerate(chunks):
            blocks.append(f"**{cat['label']} ({total})**{' · suite' if i else ''}\n{ch}")
    pages = _pack(blocks)
    out = []
    for i, p in enumerate(pages):
        e = discord.Embed(title="Help - meanings", description=p, color=C["info"])
        e.set_footer(text=f"✦ Commandes · page {i + 1}/{len(pages)}")
        out.append(e)
    return out


class HelpSelect(discord.ui.Select):
    def __init__(self, current="home"):
        opts = [discord.SelectOption(label="Accueil", value="home", emoji="🏠", default=(current == "home"))]
        for k, c in HELP_CATEGORIES.items():
            opts.append(discord.SelectOption(label=c["label"][:100], value=k, emoji=c["emoji"],
                                             description=f"{len(c['cmds'])} commandes", default=(current == k)))
        super().__init__(placeholder="Accueil", min_values=1, max_values=1, options=opts[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        old = self.view
        val = self.values[0]
        if val == "home":
            embed, pages = _build_help_home_embed(), None
        else:
            pages = _build_cat_pages(val)
            embed = pages[0]
        new = HelpView(old.author_id, pages, 0, val)
        new.message = interaction.message
        old.stop()
        await interaction.response.edit_message(embed=embed, view=new)


class HelpView(discord.ui.View):
    def __init__(self, author_id, pages=None, page=0, current="home"):
        super().__init__(timeout=180)
        self.author_id, self.pages, self.page, self.message = author_id, pages, page, None
        self.add_item(HelpSelect(current))
        if pages and len(pages) > 1:
            self.prev = discord.ui.Button(label="Précédent", style=discord.ButtonStyle.secondary, row=1)
            self.next = discord.ui.Button(label="Suivant", style=discord.ButtonStyle.primary, row=1)
            self.prev.callback, self.next.callback = self._prev, self._next
            self.add_item(self.prev)
            self.add_item(self.next)
            self._sync()

    def _sync(self):
        self.prev.disabled = (self.page <= 0)
        self.next.disabled = (self.page >= len(self.pages) - 1)

    async def _prev(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        self._sync()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    async def _next(self, interaction: discord.Interaction):
        self.page = min(len(self.pages) - 1, self.page + 1)
        self._sync()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Ce menu n'est pas le tien — fais `+help` toi-même.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try: await self.message.edit(view=self)
            except Exception: pass


async def _send_help(ctx, embed, view):
    view.message = await ctx.send(embed=embed, view=view)


@bot.command(name="help")
async def cmd_help(ctx, *, query: str = None):
    if not query:
        await _send_help(ctx, _build_help_home_embed(), HelpView(ctx.author.id)); return
    q = query.strip().lower().lstrip("+")
    if q in ("all", "tout", "full"):
        pages = _build_all_pages()
        await _send_help(ctx, pages[0], HelpView(ctx.author.id, pages, 0, "home")); return
    if q in HELP_CATEGORIES:
        pages = _build_cat_pages(q)
        await _send_help(ctx, pages[0], HelpView(ctx.author.id, pages, 0, q)); return
    found = _find_cmd(q)
    if found:
        key, cat, usage, desc, names = found
        e = discord.Embed(title=f"Help - {names[0]}", color=C["info"])
        e.add_field(name="Usage", value=f"`{usage}`", inline=False)
        e.add_field(name="Description", value=desc or "—", inline=False)
        e.add_field(name="Catégorie", value=f"{cat['emoji']} {cat['label']} (`+help {key}`)", inline=False)
        if len(names) > 1:
            e.add_field(name="Alias", value=" · ".join(f"`{n}`" for n in names[1:]), inline=False)
        e.set_footer(text="✦ meanings · <> obligatoire · [] optionnel")
        await ctx.send(embed=e); return
    pool = list(HELP_CATEGORIES) + [n.lstrip("+") for c in HELP_CATEGORIES.values() for n in _chip_names(c)]
    close = difflib.get_close_matches(q, pool, n=5, cutoff=0.6)
    hint = ("\nPeut-être : " + " · ".join(f"`{x}`" for x in close)) if close else ""
    await ctx.send(embed=make_embed("❌  Commande introuvable",
        f"> Aucune commande ou catégorie nommée `{q}`.{hint}\n> `+help` pour l'accueil.", C["error"]))


@bot.command(name="helpall")
async def cmd_helpall(ctx, section: str = None, page: int = 1):
    if section and section.lower() in HELP_CATEGORIES:
        pages = _build_cat_pages(section.lower())
        pg = max(0, min(page - 1, len(pages) - 1))
        await _send_help(ctx, pages[pg], HelpView(ctx.author.id, pages, pg, section.lower())); return
    pages = _build_all_pages()
    pg = max(0, min(page - 1, len(pages) - 1))
    await _send_help(ctx, pages[pg], HelpView(ctx.author.id, pages, pg, "home"))


# ═══════════════════════════════════════════════════════════════════════════════
#  ⚡ AUTOSWEEP — Sweep continu +allfull sans relance manuelle
# ═══════════════════════════════════════════════════════════════════════════════

_AUTO_STATE = {
    "running":   False,
    "task":      None,
    "channel":   None,
    "chunk":     500,       # combos testées par itération interne
    "interval":  0.3,       # secondes entre chaque check (respecte rate limit)
    "report_every": 5,      # rapport Discord tous les N chunks
    "found_total": 0,
    "iter_count":  0,
    "start_ts":    0.0,
}


async def _autosweep_loop(channel, chunk_size: int):
    """Boucle principale — tourne jusqu'à _AUTO_STATE['running'] == False."""
    state     = _AUTO_STATE
    all_state = _ALL_STATE           # partagé avec +allfull
    total     = all_state["total"]
    found_session = []
    report_buf    = []

    while state["running"]:
        offset = all_state["offset"]

        # Sweep terminé
        if offset >= total:
            e = discord.Embed(
                title="✅  AutoSweep — Terminé !",
                description=(f"> Toutes les `{total:,}` combos ont été parcourues.\n"
                             f"> Pseudos trouvés cette session : `{state['found_total']}`\n"
                             f"> Utilise `+allreset` puis `+autosweep start` pour recommencer."),
                color=C["check"])
            try: await channel.send(embed=e)
            except Exception: pass
            state["running"] = False
            break

        # Rate limit global en cours → attente
        wait = RATE["until"] - time.time()
        if wait > 0:
            try:
                await channel.send(embed=make_embed(
                    "⏳  AutoSweep — Rate limit",
                    f"> Pause ~`{int(wait)}s` imposée par Discord.",
                    C["warn"]))
            except Exception: pass
            await asyncio.sleep(max(wait, 1))
            continue

        # Localise la tranche
        length, local, base = _all_locate(offset)
        if length is None:
            all_state["offset"] = total
            continue

        size = min(chunk_size, len(_CHARS_FULL) ** length - local)
        candidates, idxs = _gen_valid_chunk(local, size, length, _CHARS_FULL)
        if not candidates:
            all_state["offset"] = offset + size
            continue

        # Scan de la tranche
        found_chunk = []
        checked     = 0
        limited     = False
        sem = asyncio.Semaphore(CONFIG["parallel"])

        async def _check(session, target):
            nonlocal checked, limited
            if limited: return
            async with sem:
                if limited: return
                await asyncio.sleep(state["interval"])
                result = await check_available(session, target)
                if result == "RATE_LIMITED":
                    limited = True
                    return
                if result == "INVALID_TOKEN":
                    limited = True
                    return
                checked += 1
                if result is True:
                    found_chunk.append(target)
                    STATS["found"] += 1

        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(_check(session, t)) for t in candidates]
            await asyncio.gather(*tasks)

        # Avance le pointeur
        if checked:
            all_state["offset"] = base + idxs[min(checked, len(idxs)) - 1] + 1
        elif limited:
            # Bloqué → attente avant retry
            await asyncio.sleep(5)
            continue

        # Accumule résultats
        found_session.extend(found_chunk)
        report_buf.extend(found_chunk)
        state["found_total"] += len(found_chunk)
        state["iter_count"]  += 1

        # Rapport périodique
        if state["iter_count"] % state["report_every"] == 0 or found_chunk:
            new_off = all_state["offset"]
            pct     = new_off / total * 100
            elapsed = time.time() - state["start_ts"]
            speed   = new_off / elapsed if elapsed > 0 else 0

            eta_s   = int((total - new_off) / speed) if speed > 0 else 0
            eta_str = (f"{eta_s // 3600}h {(eta_s % 3600) // 60}m"
                       if eta_s < 86400 * 30 else "∞")

            lines = "\n".join(f"> `{p}`" for p in report_buf[-10:]) if report_buf else "> aucun nouveau"
            e = discord.Embed(
                title=f"🗺️  AutoSweep — {pct:.4f}%",
                description=lines,
                color=C["og"] if report_buf else C["dark"])
            e.add_field(name="Progression",
                        value=f"`{new_off:,}` / `{total:,}`", inline=True)
            e.add_field(name="Trouvés (session)",
                        value=f"`{state['found_total']}`", inline=True)
            e.add_field(name="Vitesse",
                        value=f"`{int(speed):,}` combos/s", inline=True)
            e.add_field(name="ETA",
                        value=f"`{eta_str}`", inline=True)
            e.set_footer(text="meanings · autosweep · +autosweep stop pour arrêter")
            try: await channel.send(embed=e)
            except Exception: pass
            report_buf.clear()

        # Petite respiration entre chunks
        await asyncio.sleep(0.1)

    state["running"] = False


@bot.command(name="autosweep")
async def cmd_autosweep(ctx, action: str = "status", chunk: int = 500):
    """
    Sweep continu automatique sur toutes les combos 2-6 chars.
    Usage:
      +autosweep start [chunk=500]  — démarre (chunk = combos/itération)
      +autosweep stop               — arrête
      +autosweep status             — progression live
    """
    action = action.lower()

    # ── START ──────────────────────────────────────────────────────────────────
    if action == "start":
        if not USER_TOKEN:
            await ctx.send(embed=token_missing_embed()); return
        if _AUTO_STATE["running"]:
            await ctx.send(embed=make_embed(
                "⚠️  Déjà en cours",
                "> AutoSweep tourne déjà. `+autosweep stop` pour l'arrêter.",
                C["warn"])); return

        chunk = max(50, min(chunk, 2000))
        _AUTO_STATE.update({
            "running":     True,
            "channel":     ctx.channel,
            "chunk":       chunk,
            "found_total": 0,
            "iter_count":  0,
            "start_ts":    time.time(),
        })
        _AUTO_STATE["task"] = asyncio.create_task(_autosweep_loop(ctx.channel, chunk))

        off  = _ALL_STATE["offset"]
        tot  = _ALL_STATE["total"]
        pct  = off / tot * 100
        await ctx.send(embed=discord.Embed(
            title="🚀  AutoSweep — Démarré",
            description=(f"> Chunk : `{chunk}` combos/itération\n"
                         f"> Reprise depuis `{off:,}` / `{tot:,}` (`{pct:.4f}%`)\n"
                         f"> Rapport toutes les `{_AUTO_STATE['report_every']}` itérations\n"
                         f"> `+autosweep stop` pour arrêter à tout moment"),
            color=C["check"]))

    # ── STOP ───────────────────────────────────────────────────────────────────
    elif action == "stop":
        if not _AUTO_STATE["running"]:
            await ctx.send(embed=make_embed("ℹ️  Pas en cours",
                "> AutoSweep n'est pas actif.", C["info"])); return

        _AUTO_STATE["running"] = False
        if _AUTO_STATE["task"]:
            _AUTO_STATE["task"].cancel()
            _AUTO_STATE["task"] = None

        off = _ALL_STATE["offset"]
        tot = _ALL_STATE["total"]
        await ctx.send(embed=discord.Embed(
            title="⏹️  AutoSweep — Arrêté",
            description=(f"> Progression sauvegardée : `{off:,}` / `{tot:,}` (`{off/tot*100:.4f}%`)\n"
                         f"> Pseudos trouvés : `{_AUTO_STATE['found_total']}`\n"
                         f"> `+autosweep start` pour reprendre."),
            color=C["warn"]))

    # ── STATUS ─────────────────────────────────────────────────────────────────
    elif action == "status":
        off     = _ALL_STATE["offset"]
        tot     = _ALL_STATE["total"]
        pct     = off / tot * 100
        running = _AUTO_STATE["running"]
        elapsed = time.time() - _AUTO_STATE["start_ts"] if running else 0
        speed   = off / elapsed if elapsed > 1 else 0
        eta_s   = int((tot - off) / speed) if speed > 0 else 0
        eta_str = (f"{eta_s // 3600}h {(eta_s % 3600) // 60}m"
                   if 0 < eta_s < 86400 * 30 else ("∞" if eta_s >= 86400 * 30 else "N/A"))

        e = discord.Embed(
            title=f"{'🟢' if running else '🔴'}  AutoSweep — {'En cours' if running else 'Arrêté'}",
            color=C["check"] if running else C["error"])
        e.add_field(name="Progression",
                    value=f"`{off:,}` / `{tot:,}` (`{pct:.4f}%`)", inline=False)
        e.add_field(name="Trouvés (session)",
                    value=f"`{_AUTO_STATE['found_total']}`", inline=True)
        e.add_field(name="ETA",
                    value=f"`{eta_str}`", inline=True)
        if running:
            e.add_field(name="Vitesse",
                        value=f"`{int(speed):,}` combos/s", inline=True)
        e.set_footer(text="meanings · +autosweep start | stop | status")
        await ctx.send(embed=e)

    else:
        await ctx.send(embed=make_embed("⚠️  Action inconnue",
            "> `+autosweep start [chunk]` · `+autosweep stop` · `+autosweep status`",
            C["warn"]))



# ═══════════════════════════════════════════════════════════════════════════════
#  🚀 LANCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

if not BOT_TOKEN:
    raise SystemExit("[ERREUR] Variable d'environnement BOT_TOKEN manquante.")
bot.run(BOT_TOKEN)
