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
import json
import csv
import math
from datetime import datetime, timedelta
from collections import defaultdict

# ── AUTO-SETUP ────────────────────────────────────────────────────────────────
_WORDLISTS = {
    "words_en.txt":     "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
    "words_fr.txt":     "https://raw.githubusercontent.com/Thecoolsim/French-Scrabble-ODS8/main/ODS8.txt",
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
OWNER_ID    = int(os.environ.get("OWNER_ID", "0"))

def get_user_headers():
    return {
        "Authorization": USER_TOKEN,
        "Content-Type":  "application/json",
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

USER_HEADERS = get_user_headers()  # backwards compat

# ── ÉTAT GLOBAL ───────────────────────────────────────────────────────────────
STATS        = {"scans": 0, "found": 0, "checked": 0, "commands": 0}
WATCHLIST    = {}
FAVORITES    = defaultdict(list)
HISTORY      = defaultdict(list)
LEADERBOARD  = defaultdict(int)
FAV_NOTES    = defaultdict(dict)   # user_id → {pseudo: note}
FAV_TAGS     = defaultdict(dict)   # user_id → {pseudo: tag}
WATCH_PAUSED = set()               # keys en pause
CONFIG       = {"max_results": MAX_RESULTS, "check_delay": CHECK_DELAY, "parallel": PARALLEL}

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
        "skald","rune","futhark","blot","seidr","galdr","volva","norns","wyrd","orlög",
    ],
    "samurai": [
        "ronin","katana","bushido","kensei","shogun","daimyo","hatamoto","bannerman",
        "seppuku","harakiri","iaido","kenjutsu","battojutsu","ninjutsu","taijutsu","bojutsu",
        "naginata","yari","tetsubo","kanabo","tanto","wakizashi","nodachi","odachi","tachi",
        "kabuto","menpō","dō","kote","suneate","haidate","sode","nodowa","kikko","haramaki",
        "zen","bushido","rectitude","courage","benevolence","respect","honesty","honor",
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
        "calpulli","altepetl","tlatoani","cihuacoatl","huey","tlatoani","pochteca","tameme",
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
        "augustus","tiberius","caligula","claudius","nero","vespasian","titus","domitian",
        "nerva","trajan","hadrian","antoninus","marcus","commodus","septimius","caracalla",
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
        "molon","labe","come","and","take","them","with","your","shield","or","on","it",
        "arete","kleos","time","moira","xenia","eunomia","sophrosyne","andreia","phronesis",
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
        "platinum","white","snow","pearl","alabaster","chalk","bone","eggshell","off","white",
    ],
    "colorsfr": [
        "cramoisi","ecarlate","vermillon","carmin","bordeaux","marron","cerise","rose","saumon",
        "corail","orange","ambre","ocre","or","kaki","citron","lime","olive","emeraude","sarcelle",
        "cyan","azur","cobalt","saphir","indigo","violet","lavande","mauve","lilas","pervenche",
        "amethyste","prune","magenta","fuchsia","cerise","rose","ivoire","creme","beige","ecru",
        "lin","blé","bisque","bronze","cuivre","acajou","sienne","ombre","sepia","taupe",
        "gris","charbon","ardoise","etain","argent","platine","blanc","neige","perle","albâtre",
        "craie","os","coquille","nacre","ivoire","lait","nuage","brume","brouillard","fumee",
    ],
    "emotions": [
        "wrath","grief","bliss","dread","angst","envy","spite","lust","pride","sloth","greed",
        "gluttony","wrath","despair","euphoria","melancholy","nostalgia","serenity","ecstasy",
        "terror","anxiety","panic","phobia","paranoia","obsession","mania","hysteria","apathy",
        "indifference","stoicism","equanimity","tranquility","contentment","satisfaction","joy",
        "elation","exhilaration","rapture","fervor","passion","ardor","zeal","enthusiasm","vigor",
        "courage","valor","bravery","audacity","tenacity","resilience","fortitude","perseverance",
        "compassion","empathy","sympathy","kindness","generosity","gratitude","humility","mercy",
    ],
    "philosophy": [
        "stoic","axiom","logos","ethos","pathos","pragma","techne","episteme","phronesis",
        "arete","eudaimonia","aponia","ataraxia","apatheia","katalepsis","synkatathesis",
        "epoché","epoche","skeptic","cynic","epicurean","peripatetic","platonic","aristotelian",
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
        "rise","fall","ascend","descend","wax","wane","bloom","wither","birth","death","day","night",
        "good","evil","truth","lie","real","fake","solid","void","full","empty","loud","silent",
        "fast","slow","hot","cold","wet","dry","hard","soft","sharp","blunt","bright","dim",
        "macro","micro","cosmos","quantum","infinite","finite","eternal","mortal","divine","human",
    ],
    "pronounceable": [
        "kova","zara","nelo","tavi","mira","sefa","daro","lenu","piko","vane","relo","tuva",
        "mako","seli","devo","kira","namo","telo","vari","muse","sako","deli","keva","runo",
        "palo","temi","vora","melo","saki","devo","kano","remi","sefa","toki","varu","melo",
        "sako","deli","keva","runo","palo","temi","vora","melo","luka","niko","taro","sena",
        "vela","miko","dako","reni","palo","temi","vora","melo","saki","devo","kano","remi",
        "nova","luna","aria","echo","iris","eden","orin","asha","zion","nara","kaia","mila",
        "lena","vera","cleo","demi","emma","faye","gaia","hana","isla","jade","kira","lila",
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
    with open(path, encoding="utf-8", errors="ignore") as f:
        words = []
        for line in f:
            w = strip_accents(line.strip().lower())
            if re.match(r'^[a-z]{3,20}$', w):
                words.append(w)
    return list(set(words))

def load_cities(path):
    cities = []
    if not os.path.exists(path): return cities
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name","").strip()
                if not name: continue
                cleaned = re.sub(r'[^a-z]','', strip_accents(name.lower()))
                if 3 <= len(cleaned) <= 20:
                    cities.append(cleaned)
    except Exception as e:
        print(f"[WARN] villes : {e}")
    return list(set(cities))

print("[*] Chargement des dicos...")
_loaded_fr     = load_wordlist("words_fr.txt")
_loaded_en     = load_wordlist("words_en.txt")
_loaded_cities = load_cities("words_cities.csv")

BUILTIN_FR = ["lune","soleil","etoile","ciel","nuage","brume","orage","tonnerre","eclair",
    "pluie","neige","givre","glace","vent","tempete","montagne","vallee","desert","foret",
    "ocean","mer","lac","riviere","cascade","vague","ile","falaise","caverne","roche","flamme",
    "fleur","rose","lys","chene","pin","bouleau","loup","renard","corbeau","chouette","aigle"]
BUILTIN_EN = ["moon","sun","star","sky","cloud","mist","storm","thunder","lightning","rain",
    "snow","frost","ice","wind","gale","mountain","valley","desert","forest","ocean","sea",
    "lake","river","waterfall","wave","island","cliff","cave","rock","flame","flower","rose"]

ALL_FR     = _loaded_fr     if _loaded_fr     else BUILTIN_FR
ALL_EN     = _loaded_en     if _loaded_en     else BUILTIN_EN

BUILTIN_CITIES = [
    "paris","london","berlin","madrid","rome","milan","barcelona","amsterdam","vienna","zurich",
    "prague","warsaw","budapest","brussels","stockholm","oslo","copenhagen","helsinki","athens","lisbon",
    "tokyo","osaka","kyoto","seoul","beijing","shanghai","hongkong","singapore","bangkok","jakarta",
    "newyork","losangeles","chicago","houston","phoenix","seattle","boston","miami","dallas","denver",
    "toronto","montreal","vancouver","sydney","melbourne","brisbane","auckland","dubai","cairo","lagos",
    "moscow","istanbul","riyadh","karachi","mumbai","delhi","kolkata","dhaka","manila","taipei",
    "amsterdam","rotterdam","lyon","marseille","bordeaux","toulouse","nice","nantes","strasbourg",
    "munich","hamburg","frankfurt","cologne","dusseldorf","stuttgart","dresden","leipzig","nuremberg",
    "valencia","seville","bilbao","zaragoza","malaga","palma","granada","alicante","murcia","valladolid",
    "naples","turin","florence","venice","bologna","genoa","palermo","catania","bari","verona",
    "porto","coimbra","braga","aveiro","faro","funchal","setubal","amadora","almada","sintra",
    "zurich","geneva","basel","bern","lausanne","winterthur","lucerne","thun","chur","frauenfeld",
    "vienna","graz","linz","salzburg","innsbruck","klagenfurt","villach","wels","steyr","dornbirn",
    "brussels","antwerp","ghent","liege","bruges","namur","leuven","mons","aalst","mechelen",
    "stockholm","gothenburg","malmo","uppsala","vasteras","orebro","linkoping","helsingborg","jonkoping","norrkoping",
    "oslo","bergen","trondheim","stavanger","drammen","fredrikstad","kristiansand","sandnes","tromsoe","sarpsborg",
    "copenhagen","aarhus","odense","aalborg","esbjerg","horsens","randers","kolding","vejle","herning",
    "helsinki","espoo","tampere","vantaa","oulu","turku","jyvaskyla","lahti","kuopio","pori",
    "athens","thessaloniki","patras","heraklion","larissa","volos","rhodes","ioannina","chania","chalcis",
    "dubai","abudhabi","sharjah","ajman","ras","fujairah","umm","khor","kalba","dibba",
    "toronto","montreal","vancouver","calgary","edmonton","ottawa","winnipeg","quebec","hamilton","kitchener",
    "sydney","melbourne","brisbane","perth","adelaide","goldie","newcastle","canberra","hobart","darwin",
    "auckland","wellington","christchurch","hamilton","tauranga","napier","palmerston","dunedin","rotorua","whangarei",
    "cairo","alexandria","giza","shubra","luxor","aswan","port","suez","faiyum","zagazig",
    "lagos","kano","ibadan","abuja","port","benin","maiduguri","zaria","aba","jos",
    "nairobi","mombasa","kisumu","nakuru","eldoret","thika","malindi","kitale","garissa","kakamega",
    "accra","kumasi","tamale","takoradi","cape","koforidua","sunyani","ho","wa","bolgatanga",
    "dakar","thies","kaolack","saint","ziguinchor","diourbel","louga","tambacounda","kolda","matam",
    "casablanca","rabat","fes","marrakech","agadir","tangier","meknes","kenitra","tetouan","sale"
]
ALL_CITIES = _loaded_cities if _loaded_cities else BUILTIN_CITIES

# Dicos multilingues intégrés
LANGS = {
    "de": ["wald","stein","berg","fluss","see","mond","sonne","wind","feuer","wasser","erde",
           "wolf","fuchs","adler","eule","bär","löwe","tiger","rabe","schlange","sturm","blitz",
           "nebel","frost","glut","asche","dunkel","licht","schatten","geist","seele","traum"],
    "es": ["luna","sol","viento","fuego","agua","tierra","lobo","aguila","cuervo","sombra",
           "noche","alba","tormenta","rayo","trueno","montaña","rio","lago","mar","bosque",
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
           "oken","is","sno","dimma","rok","flamma","aska","damm","klippa","ljus"],
    "no": ["mane","sol","vind","ild","vann","jord","ulv","orn","ravn","skygge",
           "natt","gry","storm","lyn","torden","fjell","elv","innsjo","hav","skog",
           "oken","is","sno","take","rok","flamme","aske","stov","klippe","lys"],
}

print(f"[*] Prêt — FR:{len(ALL_FR):,} EN:{len(ALL_EN):,} Villes:{len(ALL_CITIES):,}")

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
    variants = set([word])
    full = word
    for k,v in AESTHETIC_MAP.items(): full = full.replace(k,v)
    if full != word and is_valid(full): variants.add(full)
    for i,c in enumerate(word):
        if c in AESTHETIC_MAP:
            v = word[:i] + AESTHETIC_MAP[c] + word[i+1:]
            if is_valid(v): variants.add(v)
    return list(variants)

def to_leet(word):
    return word.translate(str.maketrans("aeiost","431057"))

def to_reverse(word):
    return word[::-1]

def to_underscore(word):
    if len(word) >= 4:
        mid = len(word)//2
        return word[:mid] + "_" + word[mid:]
    return word

# ── BUILD POOL ────────────────────────────────────────────────────────────────
def build_pool(word_list, n=100, min_len=3, max_len=16,
               aesthetic=False, leet=False, reverse=False, underscore=False):
    solo = [w for w in word_list if min_len <= len(w) <= max_len and is_valid(w)]
    random.shuffle(solo)
    pool = set(solo[:n])

    if aesthetic:
        for w in solo[:n//2]:
            for v in to_aesthetic(w):
                if is_valid(v): pool.add(v)
    if leet:
        for w in solo[:n//2]:
            v = to_leet(w)
            if is_valid(v): pool.add(v)
    if reverse:
        for w in solo[:n//2]:
            v = to_reverse(w)
            if is_valid(v): pool.add(v)
    if underscore:
        for w in solo[:n//2]:
            v = to_underscore(w)
            if is_valid(v): pool.add(v)

    if len(pool) < n:
        pairs_src = random.sample(solo, min(120, len(solo)))
        for a,b in itertools.combinations(pairs_src,2):
            if len(pool) >= n*2: break
            if 5 <= len(a)+len(b) <= max_len:
                pool.add(f"{a}{b}")
                pool.add(f"{a}_{b}")

    result = [p for p in pool if is_valid(p)]
    random.shuffle(result)
    return result[:n]

# ── CHECK PSEUDO ──────────────────────────────────────────────────────────────
async def check_available(session, username):
    if not USER_TOKEN:
        return None  # pas de USER_TOKEN configuré
    url = "https://discord.com/api/v9/users/@me/pomelo-attempt"
    try:
        async with session.post(url, json={"username": username},
                headers=get_user_headers(), timeout=aiohttp.ClientTimeout(total=5)) as r:
            STATS["checked"] += 1
            if r.status == 200:
                data = await r.json(content_type=None)
                return not data.get("taken", True)
            elif r.status == 401:
                return "INVALID_TOKEN"
            elif r.status == 429:
                retry = float(r.headers.get("Retry-After", 3))
                await asyncio.sleep(retry)
                return None
    except: pass
    return None

# ── CHECK VANITY ──────────────────────────────────────────────────────────────
async def check_vanity(session, code):
    url = f"https://discord.com/api/v9/invites/{code}"
    try:
        async with session.get(url, headers={"User-Agent":"Mozilla/5.0"},
                timeout=aiohttp.ClientTimeout(total=5)) as r:
            STATS["checked"] += 1
            if r.status == 404: return True
            elif r.status == 200: return False
            elif r.status == 429:
                retry = float(r.headers.get("Retry-After", 2))
                await asyncio.sleep(retry)
                return None
    except: pass
    return None

# ── EMBED HELPER ──────────────────────────────────────────────────────────────
def make_embed(title="", desc="", color=C["dark"], footer="meanings"):
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
        title=f"{flag}  {len(found)} {kind}{'s' if len(found)>1 else ''} dispo{'s' if len(found)>1 else ''}",
        description=lines, color=color)
    e.set_footer(text=f"meanings · {scanned} scannés · {len(ALL_FR):,} FR · {len(ALL_EN):,} EN")
    return e

# ── SCAN ENGINE ───────────────────────────────────────────────────────────────
async def _scan_engine(candidates, max_results, msg, flag, label, color,
                        check_fn, is_vanity=False, ctx=None, speed=CHECK_DELAY):
    found = []
    checked = 0
    sem = asyncio.Semaphore(CONFIG["parallel"])

    async def check_one(session, target):
        nonlocal checked
        async with sem:
            await asyncio.sleep(speed)
            result = await check_fn(session, target)
            checked += 1
            if result is True:
                found.append(target)
                STATS["found"] += 1
                if ctx:
                    LEADERBOARD[ctx.author.id] += 1
                    HISTORY[ctx.author.id].append({
                        "pseudo": target, "ts": time.time(), "available": True, "vanity": is_vanity
                    })
                if len(found) % 3 == 0 or len(found) == 1:
                    fmt = "discord.gg/{}" if is_vanity else "{}"
                    lines = "\n".join(f"> `{fmt.format(p)}`" for p in found)
                    e = discord.Embed(
                        title=f"{flag}  {len(found)} trouvé{'s' if len(found)>1 else ''} · {checked} vérifiés",
                        description=lines, color=color)
                    e.set_footer(text=f"meanings · scan {label} en cours...")
                    try: await msg.edit(embed=e)
                    except: pass

    async with aiohttp.ClientSession() as session:
        tasks = []
        for target in candidates:
            if len(found) >= max_results: break
            tasks.append(asyncio.create_task(check_one(session, target)))
            if len(tasks) >= CONFIG["parallel"]*4:
                await asyncio.gather(*tasks); tasks = []
                if len(found) >= max_results: break
        if tasks and len(found) < max_results:
            await asyncio.gather(*tasks)

    return found[:max_results], checked

async def run_scan(ctx, word_list, label, color, flag,
                   limit=MAX_RESULTS, min_len=3, max_len=16,
                   aesthetic=False, leet=False, underscore=False, speed=None):
    if not USER_TOKEN:
        e = discord.Embed(
            title="❌  USER_TOKEN manquant",
            description=(
                "> Le scan de pseudos nécessite un **USER_TOKEN** Discord.\n"
                "> Configure la variable `USER_TOKEN` sur Railway.\n\n"
                "> **Comment l'obtenir :**\n"
                "> 1. Ouvre Discord dans le navigateur\n"
                "> 2. F12 → Network → cherche une requête\n"
                "> 3. Copie le header `Authorization`\n"
                "> 4. Colle dans Railway → Variables → `USER_TOKEN`"
            ),
            color=C["error"]
        )
        await ctx.send(embed=e); return
    if speed is None: speed = CONFIG["check_delay"]
    limit = max(1, min(limit, 30))
    n = min(max(limit*6, 30), 200)
    STATS["scans"] += 1; STATS["commands"] += 1
    msg = await ctx.send(embed=make_embed(description=f"```\n⏳  Génération — {label}...\n```", footer="scan en cours"))
    candidates = build_pool(word_list, n, min_len, max_len, aesthetic, leet, False, underscore)
    found, checked = await _scan_engine(candidates, limit, msg, flag, label, color, check_available, False, ctx, speed)
    if not found and checked == 0:
        await msg.edit(embed=discord.Embed(
            title="❌  Token invalide ou expiré",
            description="> Le `USER_TOKEN` ne fonctionne pas.\n> Récupère-en un nouveau sur Discord Web.",
            color=C["error"])); return
    await msg.edit(embed=result_embed(found, checked, flag, label, color))

async def run_vanity_scan(ctx, word_list, label, color, flag,
                           limit=MAX_RESULTS, min_len=3, max_len=16, speed=None):
    if speed is None: speed = CONFIG["check_delay"]
    limit = max(1, min(limit, 30))
    n = min(max(limit*6, 30), 200)
    STATS["scans"] += 1; STATS["commands"] += 1
    msg = await ctx.send(embed=make_embed(description=f"```\n⏳  Vanity — {label}...\n```", footer="scan en cours"))
    raw = build_pool(word_list, n*2, min_len, max_len)
    candidates = [c for c in raw if is_vanity_allowed(c)][:n]
    found, checked = await _scan_engine(candidates, limit, msg, flag, label, color, check_vanity, True, ctx, speed)
    await msg.edit(embed=result_embed(found, checked, flag, label, color, is_vanity=True))

# ── BOT ───────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"[*] {bot.user} connecté — meanings v4.0")
    bot.loop.create_task(watch_loop())

@bot.event
async def on_command(ctx):
    STATS["commands"] += 1

# ═══════════════════════════════════════════════════════════════════════════════
#  🔢 LONGUEUR EXACTE — len3 à len12
# ═══════════════════════════════════════════════════════════════════════════════

def _len_cmd(exact):
    async def _inner(ctx, limit: int = MAX_RESULTS):
        STATS["commands"] += 1
        mixed = ALL_FR + ALL_EN
        # génère aussi des combinaisons de la bonne longueur
        pool = [w for w in mixed if len(w) == exact and is_valid(w)]
        # compléter avec des combinaisons
        all_words = [w for w in mixed if 2 <= len(w) <= exact-1 and re.match(r'^[a-z]+$',w)]
        random.shuffle(all_words)
        for a,b in itertools.combinations(all_words[:200],2):
            if len(a)+len(b) == exact:
                combo = a+b
                if is_valid(combo): pool.append(combo)
            if len(pool) > 500: break
        label = f"{exact}C"
        flag_map = {3:"⚡",4:"👑",5:"🔥",6:"✨",7:"💎",8:"🌟",9:"🎯",10:"🏆",11:"📌",12:"🎪"}
        flag = flag_map.get(exact,"🔢")
        color_map = {3:C["og"],4:C["og"],5:C["short"],6:C["short"],7:C["mix"],8:C["mix"],
                     9:C["fr"],10:C["fr"],11:C["en"],12:C["en"]}
        color = color_map.get(exact, C["info"])

        # afficher le panel avec info sur rareté
        rarity = {3:"🔴 Extrêmement rares",4:"🟠 Très rares",5:"🟡 Rares",
                  6:"🟢 Peu communs",7:"🔵 Communs",8:"⚪ Fréquents"}.get(exact,"⚪ Fréquents")

        limit_real = max(1, min(limit, 30))
        n = min(max(limit_real*6, 30), 200)
        msg = await ctx.send(embed=make_embed(
            description=f"```\n🔢  Scan {exact} chars exactement...\n{rarity}\n```",
            footer=f"scan {exact}C en cours"))
        random.shuffle(pool)
        candidates = pool[:n]
        found, checked = await _scan_engine(candidates, limit_real, msg, flag, label, color, check_available, False, ctx)
        # embed avec info rareté
        if found:
            lines = "\n".join(f"> `{p}`" for p in found)
            e = discord.Embed(
                title=f"{flag}  {len(found)} pseudo{'s' if len(found)>1 else ''} {exact} chars",
                description=f"> **{rarity}**\n\n{lines}", color=color)
            e.set_footer(text=f"meanings · {checked} scannés · {exact} chars exactement")
        else:
            e = make_embed(f"{flag}  Aucun pseudo {exact}C", f"> {rarity}\n> Relance pour réessayer.", C["error"], f"{checked} scannés")
        await msg.edit(embed=e)
    return _inner

for _n in range(3,13):
    bot.command(name=f"len{_n}")(_len_cmd(_n))

# alias courts : 3c, 4c, etc.
for _n in range(3,13):
    bot.command(name=f"{_n}c")(_len_cmd(_n))

# alias letters : 3l, 4l, etc.
for _n in range(3,13):
    bot.command(name=f"{_n}l")(_len_cmd(_n))

# ═══════════════════════════════════════════════════════════════════════════════
#  🇫🇷 PSEUDOS FRANÇAIS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="meaningfr")
async def cmd_meaningfr(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR, "FR", C["fr"], "🇫🇷", limit)

@bot.command(name="meaningfr2")
async def cmd_meaningfr2(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, random.sample(ALL_FR, min(500,len(ALL_FR))), "FR²", C["fr"], "🇫🇷", limit)

@bot.command(name="frshort")
async def cmd_frshort(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR, "FR SHORT", C["short"], "⚡🇫🇷", limit, min_len=3, max_len=5)

@bot.command(name="frlong")
async def cmd_frlong(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR, "FR LONG", C["fr"], "📏🇫🇷", limit, min_len=8, max_len=16)

@bot.command(name="fraesthetic")
async def cmd_fraesthetic(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR, "FR AESTHETIC", C["aesthetic"], "✨🇫🇷", limit, aesthetic=True)

@bot.command(name="frleet")
async def cmd_frleet(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR, "FR L33T", C["cyber"], "💻🇫🇷", limit, leet=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  🇬🇧 PSEUDOS ANGLAIS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="meaningen")
async def cmd_meaningen(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_EN, "EN", C["en"], "🇬🇧", limit)

@bot.command(name="meaningen2")
async def cmd_meaningen2(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, random.sample(ALL_EN, min(500,len(ALL_EN))), "EN²", C["en"], "🇬🇧", limit)

@bot.command(name="enshort")
async def cmd_enshort(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_EN, "EN SHORT", C["short"], "⚡🇬🇧", limit, min_len=3, max_len=5)

@bot.command(name="enlong")
async def cmd_enlong(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_EN, "EN LONG", C["en"], "📏🇬🇧", limit, min_len=8, max_len=16)

@bot.command(name="enaesthetic")
async def cmd_enaesthetic(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_EN, "EN AESTHETIC", C["aesthetic"], "✨🇬🇧", limit, aesthetic=True)

@bot.command(name="enleet")
async def cmd_enleet(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_EN, "EN L33T", C["cyber"], "💻🇬🇧", limit, leet=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  🌍 MULTILINGUES
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="meaningde")
async def cmd_meaningde(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["de"], "DE", C["mix"], "🇩🇪", limit)

@bot.command(name="meaninges")
async def cmd_meaninges(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["es"], "ES", C["fr"], "🇪🇸", limit)

@bot.command(name="meaningit")
async def cmd_meaningit(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["it"], "IT", C["en"], "🇮🇹", limit)

@bot.command(name="meaningpt")
async def cmd_meaningpt(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["pt"], "PT", C["nature"], "🇵🇹", limit)

@bot.command(name="meaningnl")
async def cmd_meaningnl(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["nl"], "NL", C["ocean"], "🇳🇱", limit)

@bot.command(name="meaningpl")
async def cmd_meaningpl(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["pl"], "PL", C["cyber"], "🇵🇱", limit)

@bot.command(name="meaningsv")
async def cmd_meaningsv(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["sv"], "SV", C["ice"], "🇸🇪", limit)

@bot.command(name="meaningno")
async def cmd_meaningno(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["no"], "NO", C["viking"], "🇳🇴", limit)

# ═══════════════════════════════════════════════════════════════════════════════
#  🌐 MIX & STYLES GÉNÉRAUX
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="meaningmix")
async def cmd_meaningmix(ctx, limit: int = MAX_RESULTS):
    mixed = random.sample(ALL_FR, min(300,len(ALL_FR))) + random.sample(ALL_EN, min(300,len(ALL_EN)))
    await run_scan(ctx, mixed, "MIX", C["mix"], "🌐", limit)

@bot.command(name="short")
async def cmd_short(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "SHORT", C["short"], "⚡", limit, min_len=3, max_len=5)

@bot.command(name="medium")
async def cmd_medium(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "MEDIUM", C["mix"], "📐", limit, min_len=5, max_len=8)

@bot.command(name="long")
async def cmd_long(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "LONG", C["fr"], "📏", limit, min_len=8, max_len=16)

@bot.command(name="og")
async def cmd_og(ctx, limit: int = MAX_RESULTS):
    og = [w for w in (ALL_FR+ALL_EN) if re.match(r'^[a-z]{4,6}$', w)]
    await run_scan(ctx, og, "OG", C["og"], "👑", limit, min_len=4, max_len=6)

@bot.command(name="og3")
async def cmd_og3(ctx, limit: int = MAX_RESULTS):
    og = [w for w in (ALL_FR+ALL_EN) if re.match(r'^[a-z]{3}$', w)]
    await run_scan(ctx, og, "OG3", C["og"], "👑⚡", limit, min_len=3, max_len=3)

@bot.command(name="aesthetic")
async def cmd_aesthetic(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "AESTHETIC", C["aesthetic"], "✨", limit, aesthetic=True)

@bot.command(name="leet")
async def cmd_leet(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "L33T", C["cyber"], "💻", limit, leet=True)

@bot.command(name="underscore")
async def cmd_underscore(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, ALL_FR+ALL_EN, "UNDERSCORE", C["mix"], "〰️", limit, underscore=True)

@bot.command(name="lucky")
async def cmd_lucky(ctx):
    STATS["commands"] += 1
    candidates = build_pool(ALL_FR+ALL_EN, 30, 3, 10)
    msg = await ctx.send(embed=make_embed(description="```\n🍀  Lucky search...\n```", footer="lucky"))
    async with aiohttp.ClientSession() as session:
        for t in candidates:
            if await check_available(session, t):
                await msg.edit(embed=discord.Embed(title="🍀  Lucky !",description=f"> `{t}` est libre !",color=C["lucky"]))
                return
            await asyncio.sleep(CHECK_DELAY)
    await msg.edit(embed=make_embed("🍀  Pas de chance","Relance.",C["error"],"lucky"))

@bot.command(name="luckyvanity")
async def cmd_luckyvanity(ctx):
    STATS["commands"] += 1
    candidates = [c for c in build_pool(ALL_FR+ALL_EN, 50, 3, 10) if is_vanity_allowed(c)]
    msg = await ctx.send(embed=make_embed(description="```\n🍀  Lucky vanity...\n```", footer="lucky vanity"))
    async with aiohttp.ClientSession() as session:
        for t in candidates:
            if await check_vanity(session, t):
                await msg.edit(embed=discord.Embed(title="🍀  Lucky vanity !",description=f"> `discord.gg/{t}` libre !",color=C["lucky"]))
                return
            await asyncio.sleep(CHECK_DELAY)
    await msg.edit(embed=make_embed("🍀  Pas de chance","Relance.",C["error"],"lucky vanity"))

# scan modes vitesse
@bot.command(name="turbo")
async def cmd_turbo(ctx, limit: int = MAX_RESULTS):
    """Scan turbo — 0.1s delay (risque 429)"""
    await run_scan(ctx, ALL_FR+ALL_EN, "TURBO", C["neon"], "⚡⚡", limit, speed=0.1)

@bot.command(name="snail")
async def cmd_snail(ctx, limit: int = MAX_RESULTS):
    """Scan lent — 1s delay (très safe)"""
    await run_scan(ctx, ALL_FR+ALL_EN, "SNAIL", C["stats"], "🐌", limit, speed=1.0)

@bot.command(name="deep")
async def cmd_deep(ctx, limit: int = MAX_RESULTS):
    """Scan approfondi — 200 candidats"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n🔬  Deep scan — 200 candidats...\n```", footer="deep scan"))
    candidates = build_pool(mixed, 200, 3, 16)
    found, checked = await _scan_engine(candidates, limit, msg, "🔬", "DEEP", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔬", "DEEP", C["mix"]))

@bot.command(name="burst")
async def cmd_burst(ctx, limit: int = MAX_RESULTS):
    """Scan burst — 50 candidats rapides"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n💥  Burst scan — 50 candidats...\n```", footer="burst"))
    candidates = build_pool(mixed, 50, 3, 16)
    found, checked = await _scan_engine(candidates, limit, msg, "💥", "BURST", C["neon"], check_available, False, ctx, 0.1)
    await msg.edit(embed=result_embed(found, checked, "💥", "BURST", C["neon"]))

# ═══════════════════════════════════════════════════════════════════════════════
#  🎨 THÈMES
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="mythologie")
async def cmd_mythologie(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["mythologie"], "MYTHOLOGIE", C["myth"], "⚡🏛️", limit)

@bot.command(name="astro")
async def cmd_astro(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["astro"], "ASTRO", C["astro"], "🔭", limit)

@bot.command(name="nature")
async def cmd_nature(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["nature"], "NATURE", C["nature"], "🌿", limit)

@bot.command(name="animal")
async def cmd_animal(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["animal"], "ANIMAL", C["animal"], "🐾", limit)

@bot.command(name="food")
async def cmd_food(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["food"], "FOOD", C["food"], "🍜", limit)

@bot.command(name="sport")
async def cmd_sport(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["sport"], "SPORT", C["sport"], "🏆", limit)

@bot.command(name="science")
async def cmd_science(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["science"], "SCIENCE", C["science"], "⚗️", limit)

@bot.command(name="music")
async def cmd_music(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["music"], "MUSIC", C["music"], "🎵", limit)

@bot.command(name="game")
async def cmd_game(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["game"], "GAME", C["game"], "🎮", limit)

@bot.command(name="pirate")
async def cmd_pirate(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["pirate"], "PIRATE", C["pirate"], "🏴‍☠️", limit)

@bot.command(name="cyber")
async def cmd_cyber(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["cyber"], "CYBER", C["cyber"], "💻", limit)

@bot.command(name="magic")
async def cmd_magic(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["magic"], "MAGIC", C["magic"], "🔮", limit)

@bot.command(name="dark")
async def cmd_dark(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["dark"], "DARK", C["dark2"], "🌑", limit)

@bot.command(name="fire")
async def cmd_fire(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["fire"], "FIRE", C["fire"], "🔥", limit)

@bot.command(name="ice")
async def cmd_ice(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["ice"], "ICE", C["ice"], "❄️", limit)

@bot.command(name="ocean")
async def cmd_ocean(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["ocean"], "OCEAN", C["ocean"], "🌊", limit)

@bot.command(name="storm")
async def cmd_storm(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["storm"], "STORM", C["storm"], "⛈️", limit)

@bot.command(name="viking")
async def cmd_viking(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["viking"], "VIKING", C["viking"], "⚔️", limit)

@bot.command(name="samurai")
async def cmd_samurai(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["samurai"], "SAMURAI", C["samurai"], "🗡️", limit)

@bot.command(name="aztec")
async def cmd_aztec(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["aztec"], "AZTEC", C["aztec"], "🏔️", limit)

@bot.command(name="celtic")
async def cmd_celtic(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["celtic"], "CELTIC", C["celtic"], "🍀", limit)

@bot.command(name="egyptian")
async def cmd_egyptian(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["egyptian"], "EGYPTIAN", C["egyptian"], "𓂀", limit)

@bot.command(name="roman")
async def cmd_roman(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["roman"], "ROMAN", C["roman"], "⚔️", limit)

@bot.command(name="spartan")
async def cmd_spartan(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["spartan"], "SPARTAN", C["war"], "🛡️", limit)

@bot.command(name="gemstones")
async def cmd_gemstones(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["gemstones"], "GEMS", C["gem"], "💎", limit)

@bot.command(name="metals")
async def cmd_metals(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["metals"], "METALS", C["metal"], "🔩", limit)

@bot.command(name="colorsen")
async def cmd_colorsen(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["colorsen"], "COLORS EN", C["color"], "🎨", limit)

@bot.command(name="colorsfr")
async def cmd_colorsfr(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["colorsfr"], "COLORS FR", C["color"], "🎨", limit)

@bot.command(name="emotions")
async def cmd_emotions(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["emotions"], "EMOTIONS", C["aesthetic"], "💭", limit)

@bot.command(name="philosophy")
async def cmd_philosophy(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["philosophy"], "PHILOSOPHY", C["myth"], "📜", limit)

@bot.command(name="duality")
async def cmd_duality(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["duality"], "DUALITY", C["mix"], "☯️", limit)

@bot.command(name="pronounceable")
async def cmd_pronounceable(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["pronounceable"], "PRONOUNCEABLE", C["info"], "🗣️", limit)

@bot.command(name="brandable")
async def cmd_brandable(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["brandable"], "BRANDABLE", C["stats"], "🚀", limit)

@bot.command(name="gamer")
async def cmd_gamer(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["gamer"], "GAMER", C["game"], "🎮", limit)

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
    mixed = random.sample(ALL_FR, min(300,len(ALL_FR)))+random.sample(ALL_EN, min(300,len(ALL_EN)))
    await run_vanity_scan(ctx, mixed, "MIX", C["mix"], "🌐", limit)

@bot.command(name="vanitycity")
async def cmd_vanitycity(ctx, limit: int = MAX_RESULTS):
    if not ALL_CITIES:
        await ctx.send(embed=make_embed("❌  Dico villes manquant","",C["error"])); return
    await run_vanity_scan(ctx, ALL_CITIES, "CITY", C["city"], "🌍", limit)

@bot.command(name="vanityshort")
async def cmd_vanityshort(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, ALL_FR+ALL_EN+ALL_CITIES, "SHORT", C["short"], "⚡", limit, min_len=3, max_len=5)

@bot.command(name="vanityog")
async def cmd_vanityog(ctx, limit: int = MAX_RESULTS):
    og = [w for w in (ALL_FR+ALL_EN) if re.match(r'^[a-z]{4,6}$', w)]
    await run_vanity_scan(ctx, og, "OG", C["og"], "👑", limit, min_len=4, max_len=6)

@bot.command(name="vanitymyth")
async def cmd_vanitymyth(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["mythologie"], "MYTH", C["myth"], "🏛️", limit)

@bot.command(name="vanityastro")
async def cmd_vanityastro(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["astro"], "ASTRO", C["astro"], "🔭", limit)

@bot.command(name="vanitygame")
async def cmd_vanitygame(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["game"], "GAME", C["game"], "🎮", limit)

@bot.command(name="vanitynature")
async def cmd_vanitynature(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["nature"], "NATURE", C["nature"], "🌿", limit)

@bot.command(name="vanitydark")
async def cmd_vanitydark(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["dark"], "DARK", C["dark2"], "🌑", limit)

@bot.command(name="vanityfire")
async def cmd_vanityfire(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["fire"], "FIRE", C["fire"], "🔥", limit)

@bot.command(name="vanityice")
async def cmd_vanityice(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["ice"], "ICE", C["ice"], "❄️", limit)

@bot.command(name="vanitystorm")
async def cmd_vanitystorm(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["storm"], "STORM", C["storm"], "⛈️", limit)

@bot.command(name="vanityocean")
async def cmd_vanityocean(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["ocean"], "OCEAN", C["ocean"], "🌊", limit)

@bot.command(name="vanityforest")
async def cmd_vanityforest(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["nature"], "FOREST", C["forest"], "🌲", limit)

@bot.command(name="vanitydesert")
async def cmd_vanitydesert(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["desert"] if "desert" in THEMES else THEMES["nature"], "DESERT", C["desert"], "🏜️", limit)

@bot.command(name="vanitymetal")
async def cmd_vanitymetal(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["metals"], "METAL", C["metal"], "🔩", limit)

@bot.command(name="vanitygem")
async def cmd_vanitygem(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["gemstones"], "GEM", C["gem"], "💎", limit)

@bot.command(name="vanitycolor")
async def cmd_vanitycolor(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["colorsen"]+THEMES["colorsfr"], "COLOR", C["color"], "🎨", limit)

@bot.command(name="vanityanimal")
async def cmd_vanityanimal(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["animal"], "ANIMAL", C["animal"], "🐾", limit)

@bot.command(name="vanityfood")
async def cmd_vanityfood(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["food"], "FOOD", C["food"], "🍜", limit)

@bot.command(name="vanitysport")
async def cmd_vanitysport(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["sport"], "SPORT", C["sport"], "🏆", limit)

@bot.command(name="vanitymusic")
async def cmd_vanitymusic(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["music"], "MUSIC", C["music"], "🎵", limit)

@bot.command(name="vanitypirate")
async def cmd_vanitypirate(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["pirate"], "PIRATE", C["pirate"], "🏴‍☠️", limit)

@bot.command(name="vanitycyber")
async def cmd_vanitycyber(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["cyber"], "CYBER", C["cyber"], "💻", limit)

@bot.command(name="vanitymagic")
async def cmd_vanitymagic(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["magic"], "MAGIC", C["magic"], "🔮", limit)

@bot.command(name="vanityviking")
async def cmd_vanityviking(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["viking"], "VIKING", C["viking"], "⚔️", limit)

@bot.command(name="vanitysamurai")
async def cmd_vanitysamurai(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["samurai"], "SAMURAI", C["samurai"], "🗡️", limit)

@bot.command(name="vanityspace")
async def cmd_vanityspace(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["astro"], "SPACE", C["space"], "🚀", limit)

# ═══════════════════════════════════════════════════════════════════════════════
#  🔍 CHECK DIRECT
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="check")
async def cmd_check(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+check <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    if not is_valid(mot):
        await ctx.send(embed=make_embed("⚠️  Invalide",f"> `{mot}` invalide.",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {mot}...\n```",footer="check"))
    async with aiohttp.ClientSession() as session:
        result = await check_available(session, mot)
    if result is True:
        e = discord.Embed(title="✅  Disponible",description=f"> `{mot}` est libre !",color=C["check"])
    elif result is False:
        e = discord.Embed(title="❌  Pris",description=f"> `{mot}` est utilisé.",color=C["error"])
    else:
        e = make_embed("⚠️  Erreur","> Réessaie.",C["warn"])
    e.set_footer(text=f"meanings · check · {mot}")
    await msg.edit(embed=e)

@bot.command(name="checkvanity")
async def cmd_checkvanity(ctx, *, code: str = None):
    STATS["commands"] += 1
    if not code:
        await ctx.send(embed=make_embed("❌  Usage",">`+checkvanity <code>`",C["error"])); return
    code = code.lower().strip()
    if not is_valid_vanity(code):
        await ctx.send(embed=make_embed("⚠️  Code invalide","",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check discord.gg/{code}...\n```",footer="check vanity"))
    async with aiohttp.ClientSession() as session:
        result = await check_vanity(session, code)
    if result is True:
        e = discord.Embed(title="✅  Vanity disponible",description=f"> `discord.gg/{code}` libre !",color=C["check"])
    elif result is False:
        e = discord.Embed(title="❌  Vanity pris",description=f"> `discord.gg/{code}` utilisé.",color=C["error"])
    else:
        e = make_embed("⚠️  Erreur","> Réessaie.",C["warn"])
    e.set_footer(text=f"meanings · checkvanity · {code}")
    await msg.edit(embed=e)

@bot.command(name="checkall")
async def cmd_checkall(ctx, *, mot: str = None):
    """Check pseudo ET vanity en même temps"""
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+checkall <mot>`",C["error"])); return
    mot = mot.lower().strip()
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check pseudo + vanity {mot}...\n```",footer="checkall"))
    async with aiohttp.ClientSession() as session:
        r_pseudo  = await check_available(session, mot) if is_valid(mot) else None
        await asyncio.sleep(0.3)
        r_vanity  = await check_vanity(session, mot)   if is_valid_vanity(mot) else None

    pseudo_line  = "✅ libre" if r_pseudo is True  else "❌ pris" if r_pseudo is False  else "⚠️ invalide"
    vanity_line  = "✅ libre" if r_vanity is True  else "❌ pris" if r_vanity is False  else "⚠️ invalide"
    e = discord.Embed(title=f"🔍  Check all — `{mot}`",color=C["info"])
    e.add_field(name="👤  Pseudo Discord", value=f"> {pseudo_line}", inline=True)
    e.add_field(name="🔗  discord.gg/"+mot, value=f"> {vanity_line}", inline=True)
    e.set_footer(text="meanings · checkall")
    await msg.edit(embed=e)

@bot.command(name="available")
async def cmd_available(ctx, *, mot: str = None):
    """Alias de +check"""
    ctx.command = bot.get_command("check")
    await cmd_check(ctx, mot=mot)

@bot.command(name="taken")
async def cmd_taken(ctx, *, mot: str = None):
    """Vérifie si un pseudo est PRIS"""
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+taken <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    if not is_valid(mot):
        await ctx.send(embed=make_embed("⚠️  Invalide","",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Vérifie si {mot} est pris...\n```",footer="taken"))
    async with aiohttp.ClientSession() as session:
        result = await check_available(session, mot)
    if result is False:
        e = discord.Embed(title="✅  Oui, pris",description=f"> `{mot}` est bien utilisé par quelqu'un.",color=C["warn"])
    elif result is True:
        e = discord.Embed(title="❌  Non, disponible",description=f"> `{mot}` n'est PAS pris — il est libre !",color=C["check"])
    else:
        e = make_embed("⚠️  Erreur","> Réessaie.",C["warn"])
    e.set_footer(text=f"meanings · taken · {mot}")
    await msg.edit(embed=e)

@bot.command(name="checkstats")
async def cmd_checkstats(ctx, *, mot: str = None):
    """Analyse un pseudo — longueur, score, style"""
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+checkstats <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    length = len(mot)
    has_num = bool(re.search(r'\d', mot))
    has_under = '_' in mot
    vowels = sum(1 for c in mot if c in 'aeiou')
    consonants = length - vowels - mot.count('_') - sum(1 for c in mot if c.isdigit())

    rarity = {3:"🔴 Extrêmement rare",4:"🟠 Très rare",5:"🟡 Rare",
              6:"🟢 Peu commun",7:"🔵 Commun",8:"⚪ Fréquent"}.get(length,"⚪ Fréquent")

    score = max(0, 100 - (length-3)*8 - (10 if has_num else 0) - (5 if has_under else 0))

    style = []
    if re.match(r'^[a-z]+$', mot): style.append("lettres seulement")
    if has_num: style.append("contient des chiffres")
    if has_under: style.append("contient underscore")
    if length <= 4: style.append("OG")
    if vowels == 0: style.append("sans voyelles")

    e = discord.Embed(title=f"📊  Analyse de `{mot}`", color=C["info"])
    e.add_field(name="📏  Longueur",  value=f"`{length} chars`",    inline=True)
    e.add_field(name="⭐  Score OG",  value=f"`{score}/100`",       inline=True)
    e.add_field(name="💎  Rareté",    value=f"`{rarity}`",          inline=True)
    e.add_field(name="🔤  Voyelles",  value=f"`{vowels}`",          inline=True)
    e.add_field(name="🔡  Consonnes", value=f"`{consonants}`",      inline=True)
    e.add_field(name="🎨  Style",     value="\n".join(f"> {s}" for s in style) or "> standard", inline=False)
    e.set_footer(text="meanings · checkstats — utilisez +check pour vérifier la dispo")
    await ctx.send(embed=e)

@bot.command(name="checklist")
async def cmd_checklist(ctx, *, mots: str = None):
    STATS["commands"] += 1
    if not mots:
        await ctx.send(embed=make_embed("❌  Usage",">`+checklist mot1 mot2 mot3`",C["error"])); return
    words = [w.lower().strip() for w in mots.split() if is_valid(w.lower().strip())][:10]
    if not words:
        await ctx.send(embed=make_embed("⚠️  Aucun mot valide","",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {len(words)} pseudos...\n```",footer="checklist"))
    results = {}
    async with aiohttp.ClientSession() as session:
        for w in words:
            results[w] = await check_available(session, w)
            await asyncio.sleep(CHECK_DELAY)
    lines = [f"> {'✅' if r is True else '❌' if r is False else '⚠️'} `{w}`" for w,r in results.items()]
    e = discord.Embed(title=f"🔍  Check liste — {len(words)} pseudos",description="\n".join(lines),color=C["info"])
    e.set_footer(text="meanings · checklist")
    await msg.edit(embed=e)

@bot.command(name="checklistvanity")
async def cmd_checklistvanity(ctx, *, mots: str = None):
    STATS["commands"] += 1
    if not mots:
        await ctx.send(embed=make_embed("❌  Usage",">`+checklistvanity code1 code2`",C["error"])); return
    codes = [c.lower().strip() for c in mots.split() if is_valid_vanity(c.lower().strip())][:10]
    if not codes:
        await ctx.send(embed=make_embed("⚠️  Aucun code valide","",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {len(codes)} vanity...\n```",footer="checklist vanity"))
    results = {}
    async with aiohttp.ClientSession() as session:
        for c in codes:
            results[c] = await check_vanity(session, c)
            await asyncio.sleep(CHECK_DELAY)
    lines = [f"> {'✅' if r is True else '❌' if r is False else '⚠️'} `discord.gg/{c}`" for c,r in results.items()]
    e = discord.Embed(title=f"🔍  Check vanity liste — {len(codes)}",description="\n".join(lines),color=C["info"])
    e.set_footer(text="meanings · checklist vanity")
    await msg.edit(embed=e)

@bot.command(name="recheck")
async def cmd_recheck(ctx):
    """Relance le check de toute ta watchlist immédiatement"""
    STATS["commands"] += 1
    mine = [(k,w) for k,ws in WATCHLIST.items() for w in ws if w["user_id"]==ctx.author.id]
    if not mine:
        await ctx.send(embed=make_embed("👀  Watchlist vide","> Rien à rechequer.",C["info"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Recheck de {len(mine)} entrée(s)...\n```",footer="recheck"))
    freed = []
    async with aiohttp.ClientSession() as session:
        for key, watcher in mine:
            is_v = key.startswith("vanity:")
            target = key[7:] if is_v else key
            result = await (check_vanity if is_v else check_available)(session, target)
            await asyncio.sleep(0.5)
            if result is True:
                freed.append((key, is_v, target))
    if freed:
        lines = [f"> ✅ `{'discord.gg/'+t if v else t}` est libre !" for k,v,t in freed]
        e = discord.Embed(title=f"🔔  {len(freed)} libéré(s) !",description="\n".join(lines),color=C["check"])
        for key,_,_ in freed:
            WATCHLIST.pop(key, None)
    else:
        e = make_embed("👀  Rien de libéré","Toujours pris. Réessaie plus tard.",C["warn"],"recheck")
    e.set_footer(text="meanings · recheck")
    await msg.edit(embed=e)

@bot.command(name="snipe")
async def cmd_snipe(ctx, *, mot: str = None):
    """Surveille un pseudo toutes les 30min (snipe)"""
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+snipe <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    key = f"snipe:{mot}"
    if key not in WATCHLIST: WATCHLIST[key] = []
    WATCHLIST[key].append({"user_id":ctx.author.id,"channel_id":ctx.channel.id,"type":"snipe","interval":1800})
    e = discord.Embed(title="🎯  Snipe activé",
        description=f"> `{mot}` surveillé toutes les **30 minutes**.\n> Tu seras pingé immédiatement.",
        color=C["lucky"])
    e.set_footer(text="meanings · snipe · +unwatch pour annuler")
    await ctx.send(embed=e)

# ═══════════════════════════════════════════════════════════════════════════════
#  🎨 STYLE / GENERATE
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="style")
async def cmd_style(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+style <mot>`",C["error"])); return
    mot = mot.lower().strip()
    variants = {}
    ae = [v for v in to_aesthetic(mot) if is_valid(v) and v!=mot]
    lt = to_leet(mot)
    rv = to_reverse(mot)
    un = to_underscore(mot)
    if ae: variants["✨ aesthetic"] = ae[:3]
    if is_valid(lt) and lt!=mot: variants["💻 l33t"] = [lt]
    if is_valid(rv) and rv!=mot: variants["🔄 reverse"] = [rv]
    if is_valid(un) and un!=mot: variants["〰️ underscore"] = [un]
    if not variants:
        await ctx.send(embed=make_embed("⚠️  Aucune variante","",C["warn"])); return
    lines = [f"> `{mot}` → variantes :\n"]
    for label, vs in variants.items():
        for v in vs: lines.append(f"> {label} → `{v}`")
    e = discord.Embed(title="🎨  Variantes style",description="\n".join(lines),color=C["aesthetic"])
    e.set_footer(text="meanings · style — +check pour vérifier la dispo")
    await ctx.send(embed=e)

@bot.command(name="combine")
async def cmd_combine(ctx, mot1: str = None, mot2: str = None):
    STATS["commands"] += 1
    if not mot1 or not mot2:
        await ctx.send(embed=make_embed("❌  Usage",">`+combine mot1 mot2`",C["error"])); return
    a, b = mot1.lower().strip(), mot2.lower().strip()
    combos = []
    for x in [f"{a}{b}",f"{b}{a}",f"{a}_{b}",f"{b}_{a}",f"{a}{b[:3]}",f"{a[:3]}{b}",f"{a[0]}{b}",f"{a}{b[0]}"]:
        if is_valid(x): combos.append(x)
    if not combos:
        await ctx.send(embed=make_embed("⚠️  Aucune combo valide","",C["warn"])); return
    lines = "\n".join(f"> `{c}`" for c in combos)
    e = discord.Embed(title=f"🔀  Combos `{a}` × `{b}`",description=lines,color=C["mix"])
    e.set_footer(text="meanings · combine — +check pour vérifier")
    await ctx.send(embed=e)

@bot.command(name="suggest")
async def cmd_suggest(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+suggest <mot>`",C["error"])); return
    mot = mot.lower().strip()
    suggestions = set()
    for w in ALL_FR+ALL_EN:
        if w.startswith(mot[:3]) and w!=mot and is_valid(w): suggestions.add(w)
        if len(suggestions) >= 25: break
    for w in ALL_FR+ALL_EN:
        if mot[:4] in w and w!=mot and is_valid(w): suggestions.add(w)
        if len(suggestions) >= 30: break
    result = list(suggestions)[:20]
    random.shuffle(result)
    lines = "\n".join(f"> `{w}`" for w in result[:15])
    e = discord.Embed(title=f"💡  Suggestions pour `{mot}`",description=lines or "> Aucune suggestion.",color=C["info"])
    e.set_footer(text="meanings · suggest — +check pour vérifier")
    await ctx.send(embed=e)

@bot.command(name="from")
async def cmd_from(ctx, *, mot: str = None):
    """Génère des pseudos basés sur un mot"""
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+from <mot>`",C["error"])); return
    mot = mot.lower().strip()
    pool = set()
    base = ALL_FR + ALL_EN
    random.shuffle(base)
    for w in base[:500]:
        for x in [f"{mot}{w}", f"{w}{mot}", f"{mot}_{w}", f"{w}_{mot}"]:
            if is_valid(x) and len(x) <= 16: pool.add(x)
        if len(pool) >= 30: break
    result = list(pool)[:20]
    random.shuffle(result)
    lines = "\n".join(f"> `{p}`" for p in result[:15])
    e = discord.Embed(title=f"🔗  Pseudos depuis `{mot}`",description=lines or "> Aucun résultat.",color=C["mix"])
    e.set_footer(text="meanings · from — +check pour vérifier")
    await ctx.send(embed=e)

@bot.command(name="prefix")
async def cmd_prefix_search(ctx, *, pfx: str = None):
    """Scan pseudos commençant par un préfixe"""
    STATS["commands"] += 1
    if not pfx:
        await ctx.send(embed=make_embed("❌  Usage",">`+prefix <préfixe>`",C["error"])); return
    pfx = pfx.lower().strip()
    pool = [w for w in ALL_FR+ALL_EN if w.startswith(pfx) and is_valid(w)]
    if not pool:
        await ctx.send(embed=make_embed("⚠️  Aucun mot",f"> Aucun mot commençant par `{pfx}`.",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Scan préfixe {pfx}... ({len(pool)} candidats)\n```",footer="prefix scan"))
    found, checked = await _scan_engine(pool[:60], MAX_RESULTS, msg, "🔡", f"PREFIX:{pfx}", C["info"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔡", f"PREFIX:{pfx}", C["info"]))

@bot.command(name="suffix")
async def cmd_suffix_search(ctx, *, sfx: str = None):
    """Scan pseudos finissant par un suffixe"""
    STATS["commands"] += 1
    if not sfx:
        await ctx.send(embed=make_embed("❌  Usage",">`+suffix <suffixe>`",C["error"])); return
    sfx = sfx.lower().strip()
    pool = [w for w in ALL_FR+ALL_EN if w.endswith(sfx) and is_valid(w)]
    if not pool:
        await ctx.send(embed=make_embed("⚠️  Aucun mot",f"> Aucun mot finissant par `{sfx}`.",C["warn"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Scan suffixe {sfx}... ({len(pool)} candidats)\n```",footer="suffix scan"))
    found, checked = await _scan_engine(pool[:60], MAX_RESULTS, msg, "🔠", f"SUFFIX:{sfx}", C["info"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔠", f"SUFFIX:{sfx}", C["info"]))

@bot.command(name="contains")
async def cmd_contains(ctx, *, letters: str = None):
    """Scan pseudos contenant certaines lettres"""
    STATS["commands"] += 1
    if not letters:
        await ctx.send(embed=make_embed("❌  Usage",">`+contains <lettres>`",C["error"])); return
    letters = letters.lower().strip()
    pool = [w for w in ALL_FR+ALL_EN if letters in w and is_valid(w)]
    if not pool:
        await ctx.send(embed=make_embed("⚠️  Aucun mot",f"> Aucun mot contenant `{letters}`.",C["warn"])); return
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Scan contenant {letters}... ({min(len(pool),60)} candidats)\n```",footer="contains scan"))
    found, checked = await _scan_engine(pool[:60], MAX_RESULTS, msg, "🔍", f"CONTAINS:{letters}", C["info"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔍", f"CONTAINS:{letters}", C["info"]))

# ═══════════════════════════════════════════════════════════════════════════════
#  👀 WATCH
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="watch")
async def cmd_watch(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+watch <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    if mot not in WATCHLIST: WATCHLIST[mot] = []
    if any(w["user_id"]==ctx.author.id for w in WATCHLIST[mot]):
        await ctx.send(embed=make_embed("⚠️  Déjà surveillé",f"> Tu surveilles déjà `{mot}`.",C["warn"])); return
    WATCHLIST[mot].append({"user_id":ctx.author.id,"channel_id":ctx.channel.id,"type":"pseudo"})
    e = discord.Embed(title="👀  Surveillance activée",
        description=f"> `{mot}` surveillé.\n> Ping dès qu'il se libère.",color=C["watch"])
    e.set_footer(text="meanings · watch · check toutes les 6h")
    await ctx.send(embed=e)

@bot.command(name="watchvanity")
async def cmd_watchvanity(ctx, *, code: str = None):
    STATS["commands"] += 1
    if not code:
        await ctx.send(embed=make_embed("❌  Usage",">`+watchvanity <code>`",C["error"])); return
    code = code.lower().strip()
    key = f"vanity:{code}"
    if key not in WATCHLIST: WATCHLIST[key] = []
    if any(w["user_id"]==ctx.author.id for w in WATCHLIST[key]):
        await ctx.send(embed=make_embed("⚠️  Déjà surveillé","",C["warn"])); return
    WATCHLIST[key].append({"user_id":ctx.author.id,"channel_id":ctx.channel.id,"type":"vanity"})
    e = discord.Embed(title="👀  Vanity surveillé",
        description=f"> `discord.gg/{code}` surveillé.",color=C["watch"])
    e.set_footer(text="meanings · watchvanity")
    await ctx.send(embed=e)

@bot.command(name="unwatch")
async def cmd_unwatch(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+unwatch <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    removed = False
    for key in [mot, f"vanity:{mot}", f"snipe:{mot}"]:
        if key in WATCHLIST:
            before = len(WATCHLIST[key])
            WATCHLIST[key] = [w for w in WATCHLIST[key] if w["user_id"]!=ctx.author.id]
            if len(WATCHLIST[key])<before: removed = True
            if not WATCHLIST[key]: del WATCHLIST[key]
    e = make_embed("🗑️  Supprimé",f"> `{mot}` retiré.",C["stats"]) if removed else \
        make_embed("⚠️  Introuvable",f"> `{mot}` pas dans ta watchlist.",C["warn"])
    await ctx.send(embed=e)

@bot.command(name="watchlist")
async def cmd_watchlist(ctx):
    STATS["commands"] += 1
    mine = []
    for key, watchers in WATCHLIST.items():
        for w in watchers:
            if w["user_id"]==ctx.author.id:
                paused = key in WATCH_PAUSED
                prefix = "⏸️" if paused else ("🎯" if key.startswith("snipe:") else ("🔗" if key.startswith("vanity:") else "👤"))
                if key.startswith("vanity:"): mine.append(f"> {prefix}  `discord.gg/{key[7:]}`")
                elif key.startswith("snipe:"): mine.append(f"> {prefix}  `{key[6:]}` (snipe 30min)")
                else: mine.append(f"> {prefix}  `{key}`")
    if not mine:
        e = make_embed("📋  Watchlist vide","> `+watch <pseudo>` pour ajouter.",C["info"])
    else:
        e = discord.Embed(title=f"📋  Watchlist — {len(mine)} entrée{'s' if len(mine)>1 else ''}",
            description="\n".join(mine),color=C["watch"])
        e.set_footer(text="meanings · +unwatch pour supprimer · +recheck pour vérifier maintenant")
    await ctx.send(embed=e)

@bot.command(name="watchpause")
async def cmd_watchpause(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+watchpause <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    WATCH_PAUSED.add(mot)
    await ctx.send(embed=make_embed("⏸️  Surveillance en pause",f"> `{mot}` ne sera plus checké jusqu'à `+watchresume {mot}`.",C["warn"]))

@bot.command(name="watchresume")
async def cmd_watchresume(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+watchresume <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    WATCH_PAUSED.discard(mot)
    await ctx.send(embed=make_embed("▶️  Surveillance reprise",f"> `{mot}` est à nouveau surveillé.",C["check"]))

@bot.command(name="watchstatus")
async def cmd_watchstatus(ctx):
    STATS["commands"] += 1
    mine = [(k,w) for k,ws in WATCHLIST.items() for w in ws if w["user_id"]==ctx.author.id]
    if not mine:
        await ctx.send(embed=make_embed("👀  Watchlist vide","",C["info"])); return
    lines = []
    for key, _ in mine:
        paused = key in WATCH_PAUSED
        status = "⏸️ en pause" if paused else "✅ actif"
        interval = "30min" if key.startswith("snipe:") else "6h"
        target = key.split(":",1)[1] if ":" in key else key
        lines.append(f"> {status} `{target}` — check toutes les {interval}")
    e = discord.Embed(title="👀  Statut watchlist",description="\n".join(lines),color=C["watch"])
    e.set_footer(text="meanings · watchstatus")
    await ctx.send(embed=e)

@bot.command(name="watchcount")
async def cmd_watchcount(ctx):
    STATS["commands"] += 1
    mine = sum(1 for ws in WATCHLIST.values() for w in ws if w["user_id"]==ctx.author.id)
    total = sum(len(ws) for ws in WATCHLIST.values())
    e = discord.Embed(title="👀  Compteur watchlist",color=C["info"])
    e.add_field(name="Tes surveillances", value=f"`{mine}`", inline=True)
    e.add_field(name="Total bot",         value=f"`{total}`", inline=True)
    e.set_footer(text="meanings · watchcount")
    await ctx.send(embed=e)

@bot.command(name="watchexport")
async def cmd_watchexport(ctx):
    STATS["commands"] += 1
    mine = []
    for key, watchers in WATCHLIST.items():
        for w in watchers:
            if w["user_id"]==ctx.author.id:
                target = key.split(":",1)[1] if ":" in key else key
                mine.append(target)
    if not mine:
        await ctx.send(embed=make_embed("📋  Watchlist vide","",C["info"])); return
    text = "\n".join(mine)
    e = discord.Embed(title="📤  Export watchlist",description=f"```\n{text}\n```",color=C["info"])
    e.set_footer(text="meanings · watchexport")
    await ctx.send(embed=e)

async def watch_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(1800)  # check toutes les 30min pour les snipes
        if not WATCHLIST: continue
        async with aiohttp.ClientSession() as session:
            for key in list(WATCHLIST.keys()):
                if key not in WATCHLIST or key in WATCH_PAUSED: continue
                is_v = key.startswith("vanity:")
                is_s = key.startswith("snipe:")
                # watch normal : check toutes les 6h = toutes les 12 itérations de 30min
                target = key[7:] if is_v else (key[6:] if is_s else key)
                # pour watch normal, skip 11/12 itérations
                if not is_s:
                    if random.random() > 1/12: continue
                result = await (check_vanity if is_v else check_available)(session, target)
                await asyncio.sleep(1)
                if result is True:
                    watchers = WATCHLIST.pop(key, [])
                    for w in watchers:
                        try:
                            channel = bot.get_channel(w["channel_id"])
                            if channel:
                                user = await bot.fetch_user(w["user_id"])
                                fmt = f"discord.gg/{target}" if is_v else target
                                e = discord.Embed(title="🔔  Libéré !",
                                    description=f"{user.mention} → `{fmt}` est disponible !",
                                    color=C["check"])
                                e.set_footer(text="meanings · watchlist")
                                await channel.send(embed=e)
                        except: pass

# ═══════════════════════════════════════════════════════════════════════════════
#  ⭐ FAVORIS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="fav")
async def cmd_fav(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+fav <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    if mot in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Déjà en favori","",C["warn"])); return
    if len(FAVORITES[ctx.author.id]) >= 20:
        await ctx.send(embed=make_embed("⚠️  Limite","Max 20 favoris.",C["warn"])); return
    FAVORITES[ctx.author.id].append(mot)
    e = discord.Embed(title="⭐  Ajouté",description=f"> `{mot}` sauvegardé.",color=C["lucky"])
    e.set_footer(text="meanings · +favlist pour voir · +checkfavs pour vérifier")
    await ctx.send(embed=e)

@bot.command(name="unfav")
async def cmd_unfav(ctx, *, mot: str = None):
    STATS["commands"] += 1
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+unfav <pseudo>`",C["error"])); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas trouvé","",C["warn"])); return
    FAVORITES[ctx.author.id].remove(mot)
    FAV_NOTES[ctx.author.id].pop(mot, None)
    FAV_TAGS[ctx.author.id].pop(mot, None)
    await ctx.send(embed=make_embed("🗑️  Supprimé",f"> `{mot}` retiré.",C["stats"]))

@bot.command(name="favlist")
async def cmd_favlist(ctx):
    STATS["commands"] += 1
    favs = FAVORITES[ctx.author.id]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide","> +fav <pseudo> pour ajouter.",C["info"])); return
    lines = []
    for p in favs:
        tag  = FAV_TAGS[ctx.author.id].get(p,"")
        note = FAV_NOTES[ctx.author.id].get(p,"")
        line = f"> `{p}`"
        if tag:  line += f"  🏷️ {tag}"
        if note: line += f"  — _{note}_"
        lines.append(line)
    e = discord.Embed(title=f"⭐  Favoris — {len(favs)}",description="\n".join(lines),color=C["lucky"])
    e.set_footer(text="meanings · +checkfavs pour vérifier la dispo")
    await ctx.send(embed=e)

@bot.command(name="checkfavs")
async def cmd_checkfavs(ctx):
    STATS["commands"] += 1
    favs = FAVORITES[ctx.author.id]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide","",C["info"])); return
    msg = await ctx.send(embed=make_embed(description=f"```\n🔎  Check {len(favs)} favoris...\n```",footer="checkfavs"))
    results = {}
    async with aiohttp.ClientSession() as session:
        for w in favs:
            results[w] = await check_available(session, w)
            await asyncio.sleep(CHECK_DELAY)
    lines = [f"> {'✅' if r is True else '❌' if r is False else '⚠️'} `{w}`" for w,r in results.items()]
    e = discord.Embed(title=f"⭐  Check favoris",description="\n".join(lines),color=C["lucky"])
    e.set_footer(text="meanings · checkfavs")
    await msg.edit(embed=e)

@bot.command(name="favnote")
async def cmd_favnote(ctx, mot: str = None, *, note: str = None):
    STATS["commands"] += 1
    if not mot or not note:
        await ctx.send(embed=make_embed("❌  Usage",">`+favnote <pseudo> <note>`",C["error"])); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas en favori","Ajoute d'abord avec +fav.",C["warn"])); return
    FAV_NOTES[ctx.author.id][mot] = note
    await ctx.send(embed=make_embed("📝  Note ajoutée",f"> `{mot}` → _{note}_",C["info"]))

@bot.command(name="favtag")
async def cmd_favtag(ctx, mot: str = None, *, tag: str = None):
    STATS["commands"] += 1
    if not mot or not tag:
        await ctx.send(embed=make_embed("❌  Usage",">`+favtag <pseudo> <tag>`",C["error"])); return
    mot = mot.lower().strip()
    if mot not in FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⚠️  Pas en favori","",C["warn"])); return
    FAV_TAGS[ctx.author.id][mot] = tag.lower()
    await ctx.send(embed=make_embed("🏷️  Tag ajouté",f"> `{mot}` tagué `{tag}`",C["info"]))

@bot.command(name="favfilter")
async def cmd_favfilter(ctx, *, tag: str = None):
    STATS["commands"] += 1
    if not tag:
        await ctx.send(embed=make_embed("❌  Usage",">`+favfilter <tag>`",C["error"])); return
    tag = tag.lower().strip()
    favs = [p for p in FAVORITES[ctx.author.id] if FAV_TAGS[ctx.author.id].get(p,"") == tag]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Aucun favori",f"> Aucun favori avec le tag `{tag}`.",C["warn"])); return
    lines = "\n".join(f"> `{p}`" for p in favs)
    e = discord.Embed(title=f"⭐  Favoris — tag `{tag}`",description=lines,color=C["lucky"])
    e.set_footer(text="meanings · favfilter")
    await ctx.send(embed=e)

@bot.command(name="favexport")
async def cmd_favexport(ctx):
    STATS["commands"] += 1
    favs = FAVORITES[ctx.author.id]
    if not favs:
        await ctx.send(embed=make_embed("⭐  Vide","",C["info"])); return
    text = "\n".join(favs)
    e = discord.Embed(title=f"📤  Export favoris — {len(favs)}",description=f"```\n{text}\n```",color=C["lucky"])
    e.set_footer(text="meanings · favexport")
    await ctx.send(embed=e)

@bot.command(name="favclear")
async def cmd_favclear(ctx):
    STATS["commands"] += 1
    if not FAVORITES[ctx.author.id]:
        await ctx.send(embed=make_embed("⭐  Vide","",C["info"])); return
    n = len(FAVORITES[ctx.author.id])
    FAVORITES[ctx.author.id].clear()
    FAV_NOTES[ctx.author.id].clear()
    FAV_TAGS[ctx.author.id].clear()
    await ctx.send(embed=make_embed("🗑️  Favoris vidés",f"> {n} favori(s) supprimé(s).",C["stats"]))

# ═══════════════════════════════════════════════════════════════════════════════
#  📊 STATS PERSO & SERVEUR
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="mystats")
async def cmd_mystats(ctx):
    STATS["commands"] += 1
    hist = HISTORY[ctx.author.id]
    found = sum(1 for h in hist if h["available"])
    vanity_found = sum(1 for h in hist if h["available"] and h.get("vanity"))
    pseudo_found = found - vanity_found
    rank = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)
    my_rank = next((i+1 for i,x in enumerate(rank) if x[0]==ctx.author.id), "?")
    e = discord.Embed(title=f"📊  Mes stats — {ctx.author.display_name}",color=C["profile"])
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.add_field(name="✅  Trouvés total",   value=f"`{found}`",        inline=True)
    e.add_field(name="👤  Pseudos",          value=f"`{pseudo_found}`", inline=True)
    e.add_field(name="🔗  Vanity",           value=f"`{vanity_found}`", inline=True)
    e.add_field(name="🏆  Rang",             value=f"`#{my_rank}`",     inline=True)
    e.add_field(name="⭐  Favoris",          value=f"`{len(FAVORITES[ctx.author.id])}`", inline=True)
    e.add_field(name="👀  Watchlist",        value=f"`{sum(1 for ws in WATCHLIST.values() for w in ws if w['user_id']==ctx.author.id)}`", inline=True)
    e.set_footer(text="meanings · mystats")
    await ctx.send(embed=e)

@bot.command(name="myprofile")
async def cmd_myprofile(ctx):
    STATS["commands"] += 1
    hist = HISTORY[ctx.author.id]
    found = sum(1 for h in hist if h["available"])
    favs = FAVORITES[ctx.author.id]
    watch_count = sum(1 for ws in WATCHLIST.values() for w in ws if w["user_id"]==ctx.author.id)
    rank = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)
    my_rank = next((i+1 for i,x in enumerate(rank) if x[0]==ctx.author.id), "?")
    best = None
    for h in hist:
        if h["available"] and (best is None or len(h["pseudo"]) < len(best)): best = h["pseudo"]
    e = discord.Embed(title=f"👤  Profil — {ctx.author.display_name}",color=C["profile"])
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.add_field(name="✅  Total trouvés",    value=f"`{found}`",      inline=True)
    e.add_field(name="🏆  Rang",             value=f"`#{my_rank}`",   inline=True)
    e.add_field(name="⭐  Favoris",          value=f"`{len(favs)}`",  inline=True)
    e.add_field(name="👀  Watchlist",        value=f"`{watch_count}`",inline=True)
    e.add_field(name="🏅  Meilleur pseudo",  value=f"`{best}`" if best else "`—`", inline=True)
    if favs:
        e.add_field(name="⭐  Derniers favoris", value="\n".join(f"> `{p}`" for p in favs[-3:]), inline=False)
    e.set_footer(text="meanings · myprofile")
    await ctx.send(embed=e)

@bot.command(name="mybest")
async def cmd_mybest(ctx):
    STATS["commands"] += 1
    hist = [h for h in HISTORY[ctx.author.id] if h["available"]]
    if not hist:
        await ctx.send(embed=make_embed("🏅  Aucun trouvé","Lance un scan d'abord.",C["info"])); return
    best = min(hist, key=lambda h: len(h["pseudo"]))
    e = discord.Embed(title="🏅  Ton meilleur pseudo trouvé",
        description=f"> `{best['pseudo']}` — {len(best['pseudo'])} chars",color=C["og"])
    e.set_footer(text="meanings · mybest")
    await ctx.send(embed=e)

@bot.command(name="myrank")
async def cmd_myrank(ctx):
    STATS["commands"] += 1
    rank = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)
    my_rank = next((i+1 for i,x in enumerate(rank) if x[0]==ctx.author.id), None)
    score = LEADERBOARD[ctx.author.id]
    if my_rank is None:
        await ctx.send(embed=make_embed("🏆  Pas encore classé","Lance un scan pour entrer dans le classement.",C["info"])); return
    e = discord.Embed(title="🏆  Ton rang",
        description=f"> **#{my_rank}** avec `{score}` pseudos trouvés",color=C["og"])
    e.set_footer(text="meanings · myrank")
    await ctx.send(embed=e)

@bot.command(name="history")
async def cmd_history(ctx):
    STATS["commands"] += 1
    hist = HISTORY[ctx.author.id][-20:]
    if not hist:
        await ctx.send(embed=make_embed("📜  Historique vide","Lance un scan.",C["info"])); return
    lines = []
    for h in reversed(hist[-15:]):
        icon = "✅" if h["available"] else "❌"
        prefix = "discord.gg/" if h.get("vanity") else ""
        ts = datetime.fromtimestamp(h["ts"]).strftime("%H:%M")
        lines.append(f"> {icon} `{prefix}{h['pseudo']}` — {ts}")
    e = discord.Embed(title=f"📜  Historique — {len(hist)} entrées",description="\n".join(lines),color=C["info"])
    e.set_footer(text="meanings · history")
    await ctx.send(embed=e)

@bot.command(name="leaderboard")
async def cmd_leaderboard(ctx):
    STATS["commands"] += 1
    if not LEADERBOARD:
        await ctx.send(embed=make_embed("🏆  Vide","Pas encore de scans.",C["info"])); return
    top = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇","🥈","🥉"]+["🏅"]*7
    lines = []
    for i,(uid,count) in enumerate(top):
        try:
            user = await bot.fetch_user(uid)
            name = user.display_name
        except:
            name = f"User#{uid}"
        lines.append(f"> {medals[i]} **{name}** — `{count}` trouvés")
    e = discord.Embed(title="🏆  Leaderboard",description="\n".join(lines),color=C["og"])
    e.set_footer(text="meanings · leaderboard")
    await ctx.send(embed=e)

# ═══════════════════════════════════════════════════════════════════════════════
#  📊 STATS BOT & UTILS
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="stats")
async def cmd_stats(ctx):
    STATS["commands"] += 1
    uptime = int(time.time()-START_TIME)
    h,m = divmod(uptime//60,60)
    e = discord.Embed(title="📊  meanings — statistiques",color=C["stats"])
    e.add_field(name="🔍  Scans",     value=f"`{STATS['scans']:,}`",    inline=True)
    e.add_field(name="✅  Trouvés",    value=f"`{STATS['found']:,}`",    inline=True)
    e.add_field(name="📡  Checks",     value=f"`{STATS['checked']:,}`",  inline=True)
    e.add_field(name="⌨️  Commandes",  value=f"`{STATS['commands']:,}`", inline=True)
    e.add_field(name="👀  Watchlist",  value=f"`{len(WATCHLIST):,}`",    inline=True)
    e.add_field(name="⏱️  Uptime",     value=f"`{h}h {m}m`",            inline=True)
    e.add_field(name="📚  Dicos",
        value=f"`{len(ALL_FR):,} FR · {len(ALL_EN):,} EN · {len(ALL_CITIES):,} villes`",
        inline=False)
    e.set_footer(text="meanings · stats")
    await ctx.send(embed=e)

@bot.command(name="botinfo")
async def cmd_botinfo(ctx):
    STATS["commands"] += 1
    uptime = int(time.time()-START_TIME)
    h,m = divmod(uptime//60,60)
    e = discord.Embed(title="🤖  meanings — infos",color=C["info"])
    e.add_field(name="📌  Version",  value="`4.0`",        inline=True)
    e.add_field(name="⏱️  Uptime",   value=f"`{h}h {m}m`", inline=True)
    e.add_field(name="🏓  Latence",  value=f"`{round(bot.latency*1000)}ms`", inline=True)
    e.add_field(name="🇫🇷  FR",      value=f"`{len(ALL_FR):,}`",    inline=True)
    e.add_field(name="🇬🇧  EN",      value=f"`{len(ALL_EN):,}`",    inline=True)
    e.add_field(name="🌍  Villes",   value=f"`{len(ALL_CITIES):,}`",inline=True)
    e.add_field(name="🎨  Thèmes",   value=f"`{len(THEMES)}`",      inline=True)
    e.add_field(name="⚙️  Config",
        value=f"`PARALLEL={CONFIG['parallel']} · DELAY={CONFIG['check_delay']}s · MAX={CONFIG['max_results']}`",
        inline=False)
    e.set_footer(text="meanings v4.0")
    await ctx.send(embed=e)

@bot.command(name="ping")
async def cmd_ping(ctx):
    STATS["commands"] += 1
    lat = round(bot.latency*1000)
    color = C["check"] if lat<100 else C["warn"] if lat<300 else C["error"]
    await ctx.send(embed=discord.Embed(title="🏓  Pong !",description=f"> Latence : `{lat}ms`",color=color))

@bot.command(name="uptime")
async def cmd_uptime(ctx):
    STATS["commands"] += 1
    uptime = int(time.time()-START_TIME)
    h,m,s = uptime//3600,(uptime%3600)//60,uptime%60
    await ctx.send(embed=discord.Embed(title="⏱️  Uptime",description=f"> `{h}h {m}m {s}s`",color=C["info"]))

@bot.command(name="version")
async def cmd_version(ctx):
    STATS["commands"] += 1
    e = discord.Embed(title="📌  Version",description="> `meanings v4.0`\n> 200+ commandes · 20+ thèmes",color=C["info"])
    e.set_footer(text="meanings v4.0")
    await ctx.send(embed=e)

@bot.command(name="config")
async def cmd_config(ctx):
    STATS["commands"] += 1
    e = discord.Embed(title="⚙️  Configuration actuelle",color=C["info"])
    e.add_field(name="🔢  MAX_RESULTS",  value=f"`{CONFIG['max_results']}`",    inline=True)
    e.add_field(name="⏱️  CHECK_DELAY",  value=f"`{CONFIG['check_delay']}s`",   inline=True)
    e.add_field(name="🔀  PARALLEL",     value=f"`{CONFIG['parallel']}`",       inline=True)
    e.set_footer(text="meanings · config · +setmax/setdelay/setparallel pour modifier (admin)")
    await ctx.send(embed=e)

@bot.command(name="apistatus")
async def cmd_apistatus(ctx):
    STATS["commands"] += 1
    msg = await ctx.send(embed=make_embed(description="```\n🔎  Test API Discord...\n```",footer="apistatus"))
    t0 = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://discord.com/api/v9/gateway",
                    timeout=aiohttp.ClientTimeout(total=5)) as r:
                lat = round((time.time()-t0)*1000)
                if r.status == 200:
                    e = discord.Embed(title="✅  API Discord — OK",
                        description=f"> Gateway : `{lat}ms`\n> Status : `{r.status}`",color=C["check"])
                else:
                    e = discord.Embed(title="⚠️  API Discord — Dégradée",
                        description=f"> Status : `{r.status}`",color=C["warn"])
        except Exception as ex:
            e = make_embed("❌  API Discord — Hors ligne",f"> `{ex}`",C["error"])
    e.set_footer(text="meanings · apistatus")
    await msg.edit(embed=e)

@bot.command(name="dico")
async def cmd_dico(ctx):
    STATS["commands"] += 1
    total = len(ALL_FR)+len(ALL_EN)+len(ALL_CITIES)
    e = discord.Embed(title="📚  Dicos chargés",color=C["info"])
    e.add_field(name="🇫🇷  Français", value=f"`{len(ALL_FR):,} mots`",    inline=True)
    e.add_field(name="🇬🇧  Anglais",  value=f"`{len(ALL_EN):,} mots`",    inline=True)
    e.add_field(name="🌍  Villes",    value=f"`{len(ALL_CITIES):,}`",      inline=True)
    e.add_field(name="🎨  Thèmes",    value="\n".join(f"> `+{k}`" for k in THEMES), inline=False)
    e.add_field(name="📊  Total",     value=f"`{total:,} entrées`",        inline=False)
    e.set_footer(text="meanings · dico")
    await ctx.send(embed=e)

# ═══════════════════════════════════════════════════════════════════════════════
#  🛡️ ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

def is_owner(ctx):
    return ctx.author.id == OWNER_ID or ctx.author.guild_permissions.administrator

@bot.command(name="setmax")
async def cmd_setmax(ctx, n: int = None):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    if not n or not (1 <= n <= 50):
        await ctx.send(embed=make_embed("❌  Usage",">`+setmax <1-50>`",C["error"])); return
    CONFIG["max_results"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour",f"> MAX_RESULTS = `{n}`",C["admin"]))

@bot.command(name="setdelay")
async def cmd_setdelay(ctx, n: float = None):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    if n is None or not (0.05 <= n <= 5.0):
        await ctx.send(embed=make_embed("❌  Usage",">`+setdelay <0.05-5.0>`",C["error"])); return
    CONFIG["check_delay"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour",f"> CHECK_DELAY = `{n}s`",C["admin"]))

@bot.command(name="setparallel")
async def cmd_setparallel(ctx, n: int = None):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    if not n or not (1 <= n <= 20):
        await ctx.send(embed=make_embed("❌  Usage",">`+setparallel <1-20>`",C["error"])); return
    CONFIG["parallel"] = n
    await ctx.send(embed=make_embed("✅  Mis à jour",f"> PARALLEL = `{n}`",C["admin"]))

@bot.command(name="resetstats")
async def cmd_resetstats(ctx):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    STATS.update({"scans":0,"found":0,"checked":0,"commands":0})
    await ctx.send(embed=make_embed("✅  Stats réinitialisées","",C["admin"]))

@bot.command(name="clearwatchlist")
async def cmd_clearwatchlist(ctx):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    n = len(WATCHLIST)
    WATCHLIST.clear()
    await ctx.send(embed=make_embed("✅  Watchlist vidée",f"> {n} entrée(s) supprimée(s).",C["admin"]))

@bot.command(name="blacklistadd")
async def cmd_blacklistadd(ctx, *, mot: str = None):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+blacklistadd <mot>`",C["error"])); return
    VANITY_BLACKLIST.add(mot.lower().strip())
    await ctx.send(embed=make_embed("✅  Ajouté",f"> `{mot}` ajouté à la blacklist.",C["admin"]))

@bot.command(name="blacklistremove")
async def cmd_blacklistremove(ctx, *, mot: str = None):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    if not mot:
        await ctx.send(embed=make_embed("❌  Usage",">`+blacklistremove <mot>`",C["error"])); return
    VANITY_BLACKLIST.discard(mot.lower().strip())
    await ctx.send(embed=make_embed("✅  Retiré",f"> `{mot}` retiré de la blacklist.",C["admin"]))

@bot.command(name="blacklistshow")
async def cmd_blacklistshow(ctx):
    if not is_owner(ctx):
        await ctx.send(embed=make_embed("❌  Admin only","",C["error"])); return
    items = sorted(VANITY_BLACKLIST)
    text = ", ".join(f"`{w}`" for w in items[:50])
    e = discord.Embed(title=f"🚫  Blacklist — {len(items)} mots",description=text,color=C["admin"])
    e.set_footer(text="meanings · blacklist")
    await ctx.send(embed=e)

# ═══════════════════════════════════════════════════════════════════════════════
#  ❓ HELP
# ═══════════════════════════════════════════════════════════════════════════════

# ── CATALOGUE COMMANDES ──────────────────────────────────────────────────────
HELP_CATEGORIES = {
    "scan": {
        "emoji": "🔍",
        "label": "Scan Pseudos",
        "cmds": [
            ("+meaningfr [n]",    "Scan pseudos français"),
            ("+meaningfr2 [n]",   "Scan FR — autre lot aléatoire"),
            ("+frshort [n]",      "Pseudos FR courts (3-5 chars)"),
            ("+frlong [n]",       "Pseudos FR longs (8-16 chars)"),
            ("+fraesthetic [n]",  "Pseudos FR aesthetic"),
            ("+frleet [n]",       "Pseudos FR l33t"),
            ("+meaningen [n]",    "Scan pseudos anglais"),
            ("+meaningen2 [n]",   "Scan EN — autre lot aléatoire"),
            ("+enshort [n]",      "Pseudos EN courts"),
            ("+enlong [n]",       "Pseudos EN longs"),
            ("+enaesthetic [n]",  "Pseudos EN aesthetic"),
            ("+enleet [n]",       "Pseudos EN l33t"),
            ("+meaningmix [n]",   "Mix FR + EN aléatoire"),
            ("+short [n]",        "Pseudos courts toutes langues"),
            ("+medium [n]",       "Pseudos moyens (5-8 chars)"),
            ("+long [n]",         "Pseudos longs (8-16 chars)"),
            ("+og [n]",           "Pseudos OG (4-6 chars purs)"),
            ("+og3 [n]",          "Pseudos OG 3 chars (très rares)"),
            ("+aesthetic [n]",    "Style aesthetic global"),
            ("+leet [n]",         "Style l33t global"),
            ("+underscore [n]",   "Style underscore"),
            ("+lucky",            "1 pseudo dispo rapide"),
            ("+turbo [n]",        "Scan ultra rapide (risque 429)"),
            ("+snail [n]",        "Scan lent très safe"),
            ("+burst [n]",        "50 candidats rapides"),
            ("+deep [n]",         "Scan approfondi 200 candidats"),
        ]
    },
    "longueur": {
        "emoji": "🔢",
        "label": "Longueur Exacte",
        "cmds": [
            ("+len3 [n]  /  +3c [n]  /  +3l [n]",  "Pseudos de 3 chars exactement 🔴 Extrêmement rares"),
            ("+len4 [n]  /  +4c [n]  /  +4l [n]",  "Pseudos de 4 chars 🟠 Très rares"),
            ("+len5 [n]  /  +5c [n]  /  +5l [n]",  "Pseudos de 5 chars 🟡 Rares"),
            ("+len6 [n]  /  +6c [n]  /  +6l [n]",  "Pseudos de 6 chars 🟢 Peu communs"),
            ("+len7 [n]  /  +7c [n]  /  +7l [n]",  "Pseudos de 7 chars 🔵 Communs"),
            ("+len8 [n]  /  +8c [n]  /  +8l [n]",  "Pseudos de 8 chars ⚪ Fréquents"),
            ("+len9 [n]  /  +9c [n]  /  +9l [n]",  "Pseudos de 9 chars"),
            ("+len10 [n] / +10c [n] / +10l [n]",   "Pseudos de 10 chars"),
            ("+len11 [n] / +11c [n] / +11l [n]",   "Pseudos de 11 chars"),
            ("+len12 [n] / +12c [n] / +12l [n]",   "Pseudos de 12 chars"),
        ]
    },
    "multilingue": {
        "emoji": "🌍",
        "label": "Multilingue",
        "cmds": [
            ("+meaningde [n]", "Scan pseudos allemands 🇩🇪"),
            ("+meaninges [n]", "Scan pseudos espagnols 🇪🇸"),
            ("+meaningit [n]", "Scan pseudos italiens 🇮🇹"),
            ("+meaningpt [n]", "Scan pseudos portugais 🇵🇹"),
            ("+meaningnl [n]", "Scan pseudos néerlandais 🇳🇱"),
            ("+meaningpl [n]", "Scan pseudos polonais 🇵🇱"),
            ("+meaningsv [n]", "Scan pseudos suédois 🇸🇪"),
            ("+meaningno [n]", "Scan pseudos norvégiens 🇳🇴"),
        ]
    },
    "themes": {
        "emoji": "🎨",
        "label": "Thèmes Pseudos",
        "cmds": [
            ("+mythologie [n]",  "Dieux grecs/romains/nordiques"),
            ("+astro [n]",       "Constellations, planètes, étoiles"),
            ("+nature [n]",      "Phénomènes naturels"),
            ("+animal [n]",      "Animaux sauvages"),
            ("+food [n]",        "Cuisine du monde"),
            ("+sport [n]",       "Disciplines sportives"),
            ("+science [n]",     "Physique, chimie, biologie"),
            ("+music [n]",       "Termes musicaux"),
            ("+game [n]",        "Classes & termes gaming"),
            ("+pirate [n]",      "Thème pirate"),
            ("+cyber [n]",       "Thème hacking / cyber"),
            ("+magic [n]",       "Sorts, magie, arcane"),
            ("+dark [n]",        "Thème sombre / obscur"),
            ("+fire [n]",        "Thème feu / flammes"),
            ("+ice [n]",         "Thème glace / arctique"),
            ("+ocean [n]",       "Thème mer / océan"),
            ("+storm [n]",       "Thème tempête / orage"),
            ("+viking [n]",      "Thème viking nordique"),
            ("+samurai [n]",     "Thème samouraï japonais"),
            ("+aztec [n]",       "Thème civilisation aztèque"),
            ("+celtic [n]",      "Thème celtique / druide"),
            ("+egyptian [n]",    "Thème égypte antique"),
            ("+roman [n]",       "Thème Rome antique"),
            ("+spartan [n]",     "Thème Sparte / guerriers"),
            ("+gemstones [n]",   "Pierres précieuses"),
            ("+metals [n]",      "Métaux et minéraux"),
            ("+colorsen [n]",    "Couleurs en anglais"),
            ("+colorsfr [n]",    "Couleurs en français"),
            ("+emotions [n]",    "Émotions et sentiments"),
            ("+philosophy [n]",  "Concepts philosophiques"),
            ("+duality [n]",     "Dualités (yin/yang, etc.)"),
            ("+pronounceable [n]","Pseudos prononçables"),
            ("+brandable [n]",   "Style startup / brandable"),
            ("+gamer [n]",       "Argot et termes gamer"),
        ]
    },
    "vanity": {
        "emoji": "🔗",
        "label": "Vanity URLs",
        "cmds": [
            ("+vanityfr [n]",      "Vanity mots français"),
            ("+vanityen [n]",      "Vanity mots anglais"),
            ("+vanitymix [n]",     "Vanity mix FR+EN"),
            ("+vanitycity [n]",    "Vanity noms de villes"),
            ("+vanityshort [n]",   "Vanity courts (3-5 chars)"),
            ("+vanityog [n]",      "Vanity OG (4-6 chars)"),
            ("+luckyvanity",       "1 vanity dispo rapide"),
            ("+vanitydark [n]",    "Vanity thème dark"),
            ("+vanityfire [n]",    "Vanity thème feu"),
            ("+vanityice [n]",     "Vanity thème glace"),
            ("+vanitystorm [n]",   "Vanity thème tempête"),
            ("+vanityocean [n]",   "Vanity thème océan"),
            ("+vanityforest [n]",  "Vanity thème forêt"),
            ("+vanitydesert [n]",  "Vanity thème désert"),
            ("+vanitymetal [n]",   "Vanity métaux"),
            ("+vanitygem [n]",     "Vanity pierres précieuses"),
            ("+vanitycolor [n]",   "Vanity couleurs"),
            ("+vanityanimal [n]",  "Vanity animaux"),
            ("+vanityfood [n]",    "Vanity nourriture"),
            ("+vanitysport [n]",   "Vanity sport"),
            ("+vanitymusic [n]",   "Vanity musique"),
            ("+vanitypirate [n]",  "Vanity pirate"),
            ("+vanitycyber [n]",   "Vanity cyber"),
            ("+vanitymagic [n]",   "Vanity magie"),
            ("+vanityviking [n]",  "Vanity viking"),
            ("+vanitysamurai [n]", "Vanity samouraï"),
            ("+vanityspace [n]",   "Vanity espace / cosmos"),
            ("+vanitymyth [n]",    "Vanity mythologie"),
            ("+vanityastro [n]",   "Vanity astro"),
            ("+vanitygame [n]",    "Vanity gaming"),
            ("+vanitynature [n]",  "Vanity nature"),
        ]
    },
    "check": {
        "emoji": "🔎",
        "label": "Check & Vérification",
        "cmds": [
            ("+check <pseudo>",          "Vérifie si un pseudo est dispo"),
            ("+checkvanity <code>",      "Vérifie si une vanity est dispo"),
            ("+checkall <mot>",          "Check pseudo ET vanity en même temps"),
            ("+available <pseudo>",      "Alias de +check"),
            ("+taken <pseudo>",          "Vérifie si un pseudo est PRIS"),
            ("+checkstats <pseudo>",     "Analyse longueur, score OG, style"),
            ("+checklist mot1 mot2...",  "Check jusqu'à 10 pseudos d'un coup"),
            ("+checklistvanity code...", "Check jusqu'à 10 vanity d'un coup"),
            ("+recheck",                 "Relance le check de toute ta watchlist"),
            ("+snipe <pseudo>",          "Surveille un pseudo toutes les 30min"),
        ]
    },
    "outils": {
        "emoji": "🛠️",
        "label": "Outils & Génération",
        "cmds": [
            ("+style <mot>",          "Génère toutes les variantes style"),
            ("+combine mot1 mot2",    "Génère des combos de deux mots"),
            ("+suggest <mot>",        "Suggestions proches d'un mot"),
            ("+from <mot>",           "Pseudos construits à partir d'un mot"),
            ("+prefix <préfixe>",     "Scan pseudos commençant par..."),
            ("+suffix <suffixe>",     "Scan pseudos finissant par..."),
            ("+contains <lettres>",   "Scan pseudos contenant ces lettres"),
        ]
    },
    "watch": {
        "emoji": "👀",
        "label": "Surveillance (Watch)",
        "cmds": [
            ("+watch <pseudo>",      "Surveille un pseudo (check 6h)"),
            ("+watchvanity <code>",  "Surveille une vanity (check 6h)"),
            ("+snipe <pseudo>",      "Surveillance rapide toutes les 30min"),
            ("+unwatch <pseudo>",    "Arrête de surveiller"),
            ("+watchlist",           "Affiche ta watchlist"),
            ("+watchpause <pseudo>", "Met une surveillance en pause"),
            ("+watchresume <pseudo>","Reprend une surveillance"),
            ("+watchstatus",         "Statut détaillé de ta watchlist"),
            ("+watchcount",          "Nombre de surveillances actives"),
            ("+watchexport",         "Exporte ta watchlist en texte"),
            ("+recheck",             "Force le check immédiat de tout"),
        ]
    },
    "favoris": {
        "emoji": "⭐",
        "label": "Favoris",
        "cmds": [
            ("+fav <pseudo>",           "Sauvegarde un pseudo en favori"),
            ("+unfav <pseudo>",         "Retire un favori"),
            ("+favlist",                "Affiche tes favoris"),
            ("+checkfavs",              "Check la dispo de tous tes favoris"),
            ("+favnote <pseudo> <note>","Ajoute une note à un favori"),
            ("+favtag <pseudo> <tag>",  "Ajoute un tag à un favori"),
            ("+favfilter <tag>",        "Filtre les favoris par tag"),
            ("+favexport",              "Exporte tes favoris en texte"),
            ("+favclear",               "Vide tous tes favoris"),
        ]
    },
    "stats": {
        "emoji": "📊",
        "label": "Stats Personnelles",
        "cmds": [
            ("+mystats",    "Tes statistiques complètes"),
            ("+myprofile",  "Ton profil complet"),
            ("+mybest",     "Ton meilleur pseudo trouvé"),
            ("+myrank",     "Ton rang dans le classement"),
            ("+history",    "Ton historique de scans"),
            ("+leaderboard","Top 10 des meilleurs chasseurs"),
        ]
    },
    "bot": {
        "emoji": "🤖",
        "label": "Infos Bot",
        "cmds": [
            ("+stats",      "Statistiques globales du bot"),
            ("+botinfo",    "Infos techniques du bot"),
            ("+ping",       "Latence du bot"),
            ("+uptime",     "Temps de fonctionnement"),
            ("+version",    "Version du bot"),
            ("+config",     "Configuration actuelle"),
            ("+dico",       "Dicos chargés et thèmes dispos"),
            ("+apistatus",  "Test de l'API Discord"),
            ("+help [cat]", "Ce menu d'aide"),
            ("+helpall",    "Liste complète de toutes les commandes"),
        ]
    },
    "admin": {
        "emoji": "🛡️",
        "label": "Admin",
        "cmds": [
            ("+setmax <n>",           "Change le nombre max de résultats"),
            ("+setdelay <n>",         "Change le délai entre les checks"),
            ("+setparallel <n>",      "Change le nb de checks simultanés"),
            ("+resetstats",           "Réinitialise les stats globales"),
            ("+clearwatchlist",       "Vide toute la watchlist"),
            ("+blacklistadd <mot>",   "Ajoute un mot à la blacklist vanity"),
            ("+blacklistremove <mot>","Retire un mot de la blacklist"),
            ("+blacklistshow",        "Affiche la blacklist vanity"),
        ]
    },
}

TOTAL_CMDS = sum(len(v["cmds"]) for v in HELP_CATEGORIES.values()) + 60  # +30 dynamiques len/c/l + 30 nouvelles

# ══════════════════════════════════════════════════════════════════════════════
#  HELP SYSTEM — style Gestion (Views discord.py 2.x)
# ══════════════════════════════════════════════════════════════════════════════

def _build_help_home_embed():
    """Embed page d'accueil +help style Gestion"""
    e = discord.Embed(
        title="Help - meanings",
        description=(
            "**Bienvenue dans le système d'aide de meanings !**\n\n"
            "Sélectionnez une catégorie ci-dessous pour\n"
            "découvrir toutes les commandes disponibles.\n"
            f"Commandes disponibles : `{TOTAL_CMDS}` · Préfixe : `+`\n​"
        ),
        color=C["info"]
    )
    lines = []
    for key, cat in HELP_CATEGORIES.items():
        n = str(len(cat["cmds"])).zfill(2)
        lines.append(f"`{n}`  **{cat['label']}**")
    e.add_field(name="​", value="\n".join(lines), inline=False)
    e.add_field(
        name="​",
        value=(
            "`+help <catégorie>` · `+helpall` · `+helpall <catégorie>`\n"
            "**Catégories :** "
            + "  ".join(f"`{k}`" for k in HELP_CATEGORIES)
        ),
        inline=False
    )
    e.add_field(
        name="🚀  Quickstart",
        value=(
            "`+meaningen 5` — 5 pseudos EN\n"
            "`+og 3` — 3 OG 4-6 chars\n"
            "`+4c 5` — 5 pseudos de 4 chars exactement\n"
            "`+check storm` — vérifier un pseudo\n"
            "`+checkall storm` — pseudo + vanity\n"
            "`+dark 5` — thème dark\n"
            "`+lucky` — 1 pseudo rapide"
        ),
        inline=False
    )
    e.set_footer(text=f"meanings v4.0 · {len(ALL_FR):,} FR · {len(ALL_EN):,} EN · {len(ALL_CITIES):,} villes · {len(THEMES)} thèmes")
    return e


def _build_cat_embed(key: str):
    """Embed catégorie pour +help <cat>"""
    cat = HELP_CATEGORIES[key]
    cmds = cat["cmds"]
    # Chips style Gestion : toutes les commandes en ligne séparées par virgules
    chip_line = ", ".join(f"`{c[0]}`" for c in cmds)
    e = discord.Embed(
        title=f"{cat['emoji']}  {cat['label']} ({len(cmds)})",
        description=chip_line + "\n​",
        color=C["info"]
    )
    e.set_footer(text=f"meanings · +helpall {key} pour tout voir")
    return e


def _build_helpall_pages():
    """Génère les pages pour +helpall global — style Gestion (toutes catégories, chips)"""
    pages = []
    # Page 1 : aperçu global
    e1 = discord.Embed(
        title=f"✦  Commandes · {TOTAL_CMDS}",
        color=C["info"]
    )
    for key, cat in HELP_CATEGORIES.items():
        cmds = cat["cmds"]
        chip_line = ", ".join(f"`{c[0]}`" for c in cmds[:8])
        if len(cmds) > 8: chip_line += f", ..."
        e1.add_field(
            name=f"{cat['emoji']}  {cat['label']} ({len(cmds)})",
            value=chip_line + f"\n`+helpall {key}` pour tout voir",
            inline=False
        )
    e1.set_footer(text="meanings v4.0 · préfixe + · page 1")
    pages.append(e1)

    # Pages suivantes : détail de chaque catégorie (groupées 3 par page)
    cat_items = list(HELP_CATEGORIES.items())
    per_page  = 3
    for i in range(0, len(cat_items), per_page):
        e = discord.Embed(title=f"✦  Commandes · {TOTAL_CMDS}", color=C["info"])
        for key, cat in cat_items[i:i+per_page]:
            cmds = cat["cmds"]
            chip_line = ", ".join(f"`{c[0]}`" for c in cmds)
            e.add_field(
                name=f"{cat['emoji']}  {cat['label']} ({len(cmds)})",
                value=chip_line,
                inline=False
            )
        pg = i//per_page + 2
        total_pg = math.ceil(len(cat_items)/per_page) + 1
        e.set_footer(text=f"meanings v4.0 · préfixe + · page {pg}/{total_pg}")
        pages.append(e)
    return pages


def _build_helpall_cat_pages(key: str):
    """Pages pour +helpall <cat> — toutes les commandes avec descriptions"""
    cat  = HELP_CATEGORIES[key]
    cmds = cat["cmds"]
    per  = 12  # commandes par page
    pages = []
    total_pg = math.ceil(len(cmds)/per)
    for i in range(0, len(cmds), per):
        chunk = cmds[i:i+per]
        chip_line = ", ".join(f"`{c[0]}`" for c in chunk)
        e = discord.Embed(
            title=f"{cat['emoji']}  {cat['label']} ({len(cmds)})",
            description=chip_line,
            color=C["info"]
        )
        pg = i//per + 1
        e.set_footer(text=f"meanings · {key} · page {pg}/{total_pg}")
        pages.append(e)
    return pages


class HelpView(discord.ui.View):
    """View avec boutons Précédent / Suivant + Accueil"""
    def __init__(self, pages, page=0, home_embed=None):
        super().__init__(timeout=120)
        self.pages     = pages
        self.page      = page
        self.home_embed = home_embed
        self._update_buttons()

    def _update_buttons(self):
        self.children[0].disabled = (self.page == 0)                   # Précédent
        self.children[1].disabled = (self.page >= len(self.pages)-1)   # Suivant

    @discord.ui.button(label="Précédent", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page-1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    @discord.ui.button(label="Suivant", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(self.pages)-1, self.page+1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    @discord.ui.button(label="Accueil", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def home_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.home_embed:
            # Reset nav view sans le bouton Accueil (on est à l'accueil)
            view = HomeView()
            await interaction.response.edit_message(embed=self.home_embed, view=view)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class HomeView(discord.ui.View):
    """View page d'accueil +help — bouton Accueil désactivé"""
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Accueil", style=discord.ButtonStyle.secondary, emoji="🏠", disabled=True)
    async def home_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.command(name="help")
async def cmd_help(ctx, section: str = None):
    STATS["commands"] += 1

    if section and section.lower() in HELP_CATEGORIES:
        # Page catégorie avec pagination
        pages = _build_helpall_cat_pages(section.lower())
        home  = _build_help_home_embed()
        view  = HelpView(pages, 0, home_embed=home)
        await ctx.send(embed=pages[0], view=view)
        return

    # Page d'accueil
    e    = _build_help_home_embed()
    view = HomeView()
    await ctx.send(embed=e, view=view)


@bot.command(name="helpall")
async def cmd_helpall(ctx, section: str = None, page: int = 1):
    STATS["commands"] += 1

    if section and section.lower() in HELP_CATEGORIES:
        pages   = _build_helpall_cat_pages(section.lower())
        home    = _build_help_home_embed()
        pg      = max(0, min(page-1, len(pages)-1))
        view    = HelpView(pages, pg, home_embed=home)
        await ctx.send(embed=pages[pg], view=view)
        return

    # helpall global paginé
    pages = _build_helpall_pages()
    home  = _build_help_home_embed()
    view  = HelpView(pages, 0, home_embed=home)
    await ctx.send(embed=pages[0], view=view)

# ═══════════════════════════════════════════════════════════════════════════════
#  🆕 200 NOUVELLES COMMANDES
# ═══════════════════════════════════════════════════════════════════════════════

# ── THÈMES SUPPLÉMENTAIRES ────────────────────────────────────────────────────
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
        "coral","reef","atoll","shoal","bank","seamount","ridge","rift","trench","basin"],
    "storm2": ["cyclone","typhoon","hurricane","tornado","waterspout","haboob","derecho","squall",
        "gale","tempest","maelstrom","vortex","whirlwind","dust","devil","sandstorm","blizzard",
        "snowsquall","ice","storm","thunderstorm","lightning","thunder","hail","sleet","freezing"],
    "lore": ["legend","myth","tale","saga","epic","ballad","chronicle","annals","tome","codex",
        "grimoire","scroll","tablet","inscription","relic","artifact","totem","idol","effigy",
        "prophecy","oracle","vision","dream","omen","portent","sign","wonder","miracle","mystery"],
    "mage": ["arcane","mystic","esoteric","occult","eldritch","arcanum","grimoire","tome","scroll",
        "spell","rune","glyph","sigil","ward","seal","binding","summon","conjure","invoke","banish",
        "ward","shield","barrier","veil","shroud","cloak","illude","glamour","enchant","bewitch"],
    "assassin2": ["silent","swift","deadly","fatal","lethal","precise","accurate","calculated",
        "cold","ruthless","merciless","relentless","unstoppable","shadow","ghost","phantom","wraith",
        "specter","shade","darkness","night","void","nothing","nowhere","everywhere","unseen"],
    "warlock": ["pact","bargain","deal","contract","soul","power","dark","eldritch","arcane",
        "forbidden","cursed","tainted","corrupted","twisted","warped","broken","shattered","void",
        "chaos","entropy","destruction","obliteration","annihilation","devastation","ruin","doom"],
}

# Fusion dans THEMES
THEMES.update(THEMES_EXTRA)

# ── THÈMES SUPPLÉMENTAIRES — SCAN PSEUDOS ────────────────────────────────────

@bot.command(name="ninja")
async def cmd_ninja(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["ninja"], "NINJA", C["ninja"], "🥷", limit)

@bot.command(name="gladiator")
async def cmd_gladiator(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["gladiator"], "GLADIATOR", C["war"], "⚔️", limit)

@bot.command(name="dragon")
async def cmd_dragon(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["dragon"], "DRAGON", C["fire"], "🐉", limit)

@bot.command(name="witch")
async def cmd_witch(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["witch"], "WITCH", C["magic"], "🧙", limit)

@bot.command(name="demon")
async def cmd_demon(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["demon"], "DEMON", C["dark2"], "👿", limit)

@bot.command(name="angel")
async def cmd_angel(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["angel"], "ANGEL", C["color"], "👼", limit)

@bot.command(name="forest")
async def cmd_forest(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["forest"], "FOREST", C["forest"], "🌲", limit)

@bot.command(name="desert")
async def cmd_desert(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["desert"], "DESERT", C["desert"], "🏜️", limit)

@bot.command(name="space")
async def cmd_space(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["space"], "SPACE", C["space"], "🚀", limit)

@bot.command(name="lore")
async def cmd_lore(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["lore"], "LORE", C["myth"], "📜", limit)

@bot.command(name="mage")
async def cmd_mage(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["mage"], "MAGE", C["magic"], "🧙‍♂️", limit)

@bot.command(name="warlock")
async def cmd_warlock(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["warlock"], "WARLOCK", C["dark2"], "🔮", limit)

# ── VANITY SUPPLÉMENTAIRES ────────────────────────────────────────────────────

@bot.command(name="vanityninja")
async def cmd_vanityninja(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["ninja"], "NINJA", C["ninja"], "🥷", limit)

@bot.command(name="vanitydragon")
async def cmd_vanitydragon(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["dragon"], "DRAGON", C["fire"], "🐉", limit)

@bot.command(name="vanitywitch")
async def cmd_vanitywitch(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["witch"], "WITCH", C["magic"], "🧙", limit)

@bot.command(name="vanitydemon")
async def cmd_vanitydemon(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["demon"], "DEMON", C["dark2"], "👿", limit)

@bot.command(name="vanityangel")
async def cmd_vanityangel(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["angel"], "ANGEL", C["color"], "👼", limit)

@bot.command(name="vanityforest2")
async def cmd_vanityforest2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["forest"], "FOREST", C["forest"], "🌲", limit)

@bot.command(name="vanitydesert2")
async def cmd_vanitydesert2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["desert"], "DESERT", C["desert"], "🏜️", limit)

@bot.command(name="vanityspace2")
async def cmd_vanityspace2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["space"], "SPACE", C["space"], "🚀", limit)

@bot.command(name="vanitydruid")
async def cmd_vanitydruid(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["celtic"], "DRUID", C["nature"], "🌿", limit)

@bot.command(name="vanitywarlock")
async def cmd_vanitywarlock(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["warlock"], "WARLOCK", C["dark2"], "🔮", limit)

@bot.command(name="vanitylore")
async def cmd_vanitylore(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["lore"], "LORE", C["myth"], "📜", limit)

@bot.command(name="vanitymage")
async def cmd_vanitymage(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["mage"], "MAGE", C["magic"], "🧙‍♂️", limit)

@bot.command(name="vanityassassin")
async def cmd_vanityassassin(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES.get("assassin2", THEMES["ninja"]), "ASSASSIN", C["dark2"], "🗡️", limit)

@bot.command(name="vanitygladiator")
async def cmd_vanitygladiator(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["gladiator"], "GLADIATOR", C["war"], "⚔️", limit)

@bot.command(name="vanityspartan2")
async def cmd_vanityspartan2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["spartan"], "SPARTAN", C["war"], "🛡️", limit)

@bot.command(name="vanityroman2")
async def cmd_vanityroman2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["roman"], "ROMAN", C["roman"], "⚔️", limit)

@bot.command(name="vanityviking2")
async def cmd_vanityviking2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["viking"], "VIKING", C["viking"], "⚔️", limit)

@bot.command(name="vanitysamurai2")
async def cmd_vanitysamurai2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["samurai"], "SAMURAI", C["samurai"], "🗡️", limit)

@bot.command(name="vanitycyber2")
async def cmd_vanitycyber2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["cyber"], "CYBER", C["cyber"], "💻", limit)

@bot.command(name="vanityaztec")
async def cmd_vanityaztec(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["aztec"], "AZTEC", C["aztec"], "🏔️", limit)

@bot.command(name="vanityceltic")
async def cmd_vanityceltic(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["celtic"], "CELTIC", C["celtic"], "🍀", limit)

@bot.command(name="vanityegyptian")
async def cmd_vanityegyptian(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["egyptian"], "EGYPTIAN", C["egyptian"], "𓂀", limit)

@bot.command(name="vanityphilosophy")
async def cmd_vanityphilosophy(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["philosophy"], "PHILOSOPHY", C["myth"], "📜", limit)

@bot.command(name="vanityemotions")
async def cmd_vanityemotions(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["emotions"], "EMOTIONS", C["aesthetic"], "💭", limit)

@bot.command(name="vanityscience")
async def cmd_vanityscience(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["science"], "SCIENCE", C["science"], "⚗️", limit)

@bot.command(name="vanitygamer")
async def cmd_vanitygamer(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["gamer"], "GAMER", C["game"], "🎮", limit)

# ── COMBINAISONS GÉNÉRATION ───────────────────────────────────────────────────

@bot.command(name="adjnoun")
async def cmd_adjnoun(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos adjectif+nom"""
    STATS["commands"] += 1
    adjs = ["dark","cold","bright","swift","dead","wild","free","bold","iron","steel",
            "black","white","red","blue","gold","silver","shadow","silent","fierce","brave"]
    nouns = ["wolf","blade","storm","fire","void","soul","heart","mind","eye","hand",
             "fist","claw","wing","horn","flame","stone","river","mountain","forest","ocean"]
    pool = []
    for a in adjs:
        for n in nouns:
            combo = f"{a}{n}"
            if is_valid(combo): pool.append(combo)
            combo2 = f"{a}_{n}"
            if is_valid(combo2): pool.append(combo2)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🎲  Génération adj+noun...\n```", footer="adjnoun"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🎲", "ADJ+NOUN", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🎲", "ADJ+NOUN", C["mix"]))

@bot.command(name="coloranimal")
async def cmd_coloranimal(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos couleur+animal"""
    STATS["commands"] += 1
    colors = ["red","blue","black","white","grey","gold","silver","dark","bright","shadow",
              "iron","steel","midnight","crimson","azure","emerald","violet","amber","jade","coral"]
    animals = ["wolf","fox","bear","eagle","hawk","raven","owl","lion","tiger","dragon",
               "serpent","phoenix","lynx","panther","falcon","cobra","viper","shark","whale","orca"]
    pool = []
    for c in colors:
        for a in animals:
            combo = f"{c}{a}"
            if is_valid(combo): pool.append(combo)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🎨  Génération couleur+animal...\n```", footer="coloranimal"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🎨", "COLOR+ANIMAL", C["color"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🎨", "COLOR+ANIMAL", C["color"]))

@bot.command(name="doubleword")
async def cmd_doubleword(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos mot+mot courts"""
    STATS["commands"] += 1
    shorts = [w for w in ALL_FR+ALL_EN if 3 <= len(w) <= 5 and re.match(r'^[a-z]+$', w)]
    random.shuffle(shorts)
    shorts = shorts[:60]
    pool = []
    for a, b in itertools.combinations(shorts, 2):
        combo = f"{a}{b}"
        if is_valid(combo) and len(combo) <= 10: pool.append(combo)
        if len(pool) >= 150: break
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔀  Génération double mots...\n```", footer="doubleword"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔀", "DOUBLE WORD", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔀", "DOUBLE WORD", C["mix"]))

@bot.command(name="prefixword")
async def cmd_prefixword(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos avec préfixes cool"""
    STATS["commands"] += 1
    prefixes = ["neo","pro","ultra","hyper","super","mega","meta","omni","poly","mono",
                "anti","anti","auto","bio","geo","micro","macro","cyber","techno","electro"]
    words = [w for w in ALL_EN if 3 <= len(w) <= 7 and re.match(r'^[a-z]+$', w)]
    random.shuffle(words)
    pool = []
    for pfx in prefixes:
        for w in words[:30]:
            combo = f"{pfx}{w}"
            if is_valid(combo): pool.append(combo)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔡  Génération préfixe+mot...\n```", footer="prefixword"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔡", "PREFIX+WORD", C["cyber"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔡", "PREFIX+WORD", C["cyber"]))

@bot.command(name="wordsuffix")
async def cmd_wordsuffix(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos avec suffixes cool"""
    STATS["commands"] += 1
    suffixes = ["ify","ize","ism","ist","ite","oid","eon","ion","ark","ard","ling","ward",
                "less","ness","ful","able","ible","ive","ous","al"]
    words = [w for w in ALL_EN if 3 <= len(w) <= 7 and re.match(r'^[a-z]+$', w)]
    random.shuffle(words)
    pool = []
    for sfx in suffixes:
        for w in words[:30]:
            combo = f"{w}{sfx}"
            if is_valid(combo): pool.append(combo)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔠  Génération mot+suffixe...\n```", footer="wordsuffix"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔠", "WORD+SUFFIX", C["info"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔠", "WORD+SUFFIX", C["info"]))

@bot.command(name="wordnumber")
async def cmd_wordnumber(ctx, limit: int = MAX_RESULTS):
    """Génère pseudos mot+chiffre"""
    STATS["commands"] += 1
    words = [w for w in ALL_FR+ALL_EN if 4 <= len(w) <= 10 and is_valid(w)]
    random.shuffle(words)
    pool = []
    for w in words[:100]:
        for n in ["1","2","3","7","0","00","01","69","77","99","x","xx"]:
            combo = f"{w}{n}"
            if is_valid(combo): pool.append(combo)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔢  Génération mot+chiffre...\n```", footer="wordnumber"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔢", "MOT+CHIFFRE", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔢", "MOT+CHIFFRE", C["mix"]))

# ── SCAN MODES SUPPLÉMENTAIRES ────────────────────────────────────────────────

@bot.command(name="mega")
async def cmd_mega(ctx, limit: int = MAX_RESULTS):
    """Scan mega — 300 candidats"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n💪  Mega scan — 300 candidats...\n```", footer="mega"))
    candidates = build_pool(mixed, 300, 3, 16)
    found, checked = await _scan_engine(candidates, limit, msg, "💪", "MEGA", C["neon"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "💪", "MEGA", C["neon"]))

@bot.command(name="ultra")
async def cmd_ultra(ctx, limit: int = MAX_RESULTS):
    """Scan ultra — 400 candidats"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n⚡  Ultra scan — 400 candidats...\n```", footer="ultra"))
    candidates = build_pool(mixed, 400, 3, 16)
    found, checked = await _scan_engine(candidates, limit, msg, "⚡", "ULTRA", C["og"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "⚡", "ULTRA", C["og"]))

@bot.command(name="blitz")
async def cmd_blitz(ctx, limit: int = MAX_RESULTS):
    """Scan blitz — vitesse max, 0.05s delay"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n⚡⚡  Blitz — vitesse max...\n```", footer="blitz"))
    candidates = build_pool(mixed, 100, 3, 16)
    found, checked = await _scan_engine(candidates, limit, msg, "⚡⚡", "BLITZ", C["neon"], check_available, False, ctx, 0.05)
    await msg.edit(embed=result_embed(found, checked, "⚡⚡", "BLITZ", C["neon"]))

@bot.command(name="hyper")
async def cmd_hyper(ctx, limit: int = MAX_RESULTS):
    """Scan hyper — 0.15s delay"""
    await run_scan(ctx, ALL_FR+ALL_EN, "HYPER", C["neon"], "🚀", limit, speed=0.15)

@bot.command(name="flash")
async def cmd_flash(ctx, limit: int = MAX_RESULTS):
    """Scan flash — 0.2s delay"""
    await run_scan(ctx, ALL_FR+ALL_EN, "FLASH", C["og"], "⚡", limit, speed=0.2)

@bot.command(name="rapid")
async def cmd_rapid(ctx, limit: int = MAX_RESULTS):
    """Scan rapid — 0.25s delay"""
    await run_scan(ctx, ALL_FR+ALL_EN, "RAPID", C["check"], "🏃", limit, speed=0.25)

@bot.command(name="crawl")
async def cmd_crawl(ctx, limit: int = MAX_RESULTS):
    """Scan très lent — 2s delay, très safe"""
    await run_scan(ctx, ALL_FR+ALL_EN, "CRAWL", C["stats"], "🐢", limit, speed=2.0)

# ── PATTERNS SPÉCIAUX ─────────────────────────────────────────────────────────

@bot.command(name="novowel")
async def cmd_novowel(ctx, limit: int = MAX_RESULTS):
    """Pseudos sans voyelles"""
    STATS["commands"] += 1
    pool = [w for w in ALL_FR+ALL_EN if not any(c in 'aeiou' for c in w) and is_valid(w)]
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔤  Scan sans voyelles...\n```", footer="novowel"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔤", "NO VOWEL", C["cyber"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔤", "NO VOWEL", C["cyber"]))

@bot.command(name="palindrome")
async def cmd_palindrome(ctx, limit: int = MAX_RESULTS):
    """Pseudos palindromes"""
    STATS["commands"] += 1
    # Génère des palindromes
    pool = []
    for w in ALL_FR+ALL_EN:
        if w == w[::-1] and is_valid(w): pool.append(w)
    # Génère aussi des palindromes courts
    for w in ALL_FR+ALL_EN:
        if 3 <= len(w) <= 5:
            pal = w + w[::-1]
            if is_valid(pal): pool.append(pal)
            pal2 = w + w[-2::-1]
            if is_valid(pal2): pool.append(pal2)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔄  Scan palindromes...\n```", footer="palindrome"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔄", "PALINDROME", C["aesthetic"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔄", "PALINDROME", C["aesthetic"]))

@bot.command(name="mirror")
async def cmd_mirror(ctx, limit: int = MAX_RESULTS):
    """Pseudos en miroir (mot+reverse)"""
    STATS["commands"] += 1
    pool = []
    words = [w for w in ALL_FR+ALL_EN if 3 <= len(w) <= 4 and re.match(r'^[a-z]+$', w)]
    random.shuffle(words)
    for w in words[:100]:
        combo = w + w[::-1]
        if is_valid(combo): pool.append(combo)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🪞  Scan miroir...\n```", footer="mirror"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🪞", "MIRROR", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🪞", "MIRROR", C["mix"]))

@bot.command(name="double")
async def cmd_double(ctx, limit: int = MAX_RESULTS):
    """Pseudos mot répété 2x"""
    STATS["commands"] += 1
    pool = []
    words = [w for w in ALL_FR+ALL_EN if 3 <= len(w) <= 4 and re.match(r'^[a-z]+$', w)]
    random.shuffle(words)
    for w in words[:100]:
        combo = w + w
        if is_valid(combo): pool.append(combo)
        combo2 = w + "_" + w
        if is_valid(combo2): pool.append(combo2)
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n✌️  Scan double mots...\n```", footer="double"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "✌️", "DOUBLE", C["mix"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "✌️", "DOUBLE", C["mix"]))

@bot.command(name="initials")
async def cmd_initials(ctx, limit: int = MAX_RESULTS):
    """Pseudos type initiales (abc, xyz)"""
    STATS["commands"] += 1
    import string
    letters = string.ascii_lowercase
    pool = []
    # 2 lettres + mot
    for a in letters:
        for b in letters:
            if a != b:
                for w in random.sample(ALL_EN[:200], min(50, len(ALL_EN[:200]))):
                    combo = f"{a}{b}{w}"
                    if is_valid(combo) and len(combo) <= 8: pool.append(combo)
                    if len(pool) >= 150: break
        if len(pool) >= 150: break
    random.shuffle(pool)
    msg = await ctx.send(embed=make_embed(description="```\n🔡  Scan initiales...\n```", footer="initials"))
    found, checked = await _scan_engine(pool[:80], min(limit,30), msg, "🔡", "INITIALES", C["info"], check_available, False, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔡", "INITIALES", C["info"]))

# ── MULTILINGUES SUPPLÉMENTAIRES ──────────────────────────────────────────────

LANGS_EXTRA = {
    "jp": ["tsuki","hoshi","kaze","hi","mizu","uchi","sora","yama","kawa","umi",
           "mori","shiro","kuroi","aoi","aka","midori","kiiro","shiro","kage","hikari",
           "katana","ninja","samurai","ronin","shogun","dojo","sakura","fuji","oni","tengu"],
    "ko": ["dal","byul","baram","bul","mul","san","gang","bada","hanal","areum",
           "bidam","cheon","earth","black","white","blue","red","green","shadow","light"],
    "ar": ["nour","badr","fajr","leil","qamar","najm","rih","bahr","jabal","sahara",
           "asad","namir","saqr","dhi","iblis","jinn","marid","ifrit","silat","ghoul"],
    "ru": ["luna","zvezda","veter","ogon","voda","les","more","gora","reka","noch",
           "volya","sila","dukh","volk","orel","medved","lion","tigr","zmey","feniks"],
}
LANGS.update(LANGS_EXTRA)

@bot.command(name="meaningjp")
async def cmd_meaningjp(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["jp"], "JP", C["samurai"], "🇯🇵", limit)

@bot.command(name="meaningko")
async def cmd_meaningko(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["ko"], "KO", C["neon"], "🇰🇷", limit)

@bot.command(name="meaningar")
async def cmd_meaningar(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["ar"], "AR", C["desert"], "🇸🇦", limit)

@bot.command(name="meaningru")
async def cmd_meaningru(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, LANGS["ru"], "RU", C["ice"], "🇷🇺", limit)

# ── STYLES IDENTITÉ ───────────────────────────────────────────────────────────

@bot.command(name="streamer")
async def cmd_streamer(ctx, limit: int = MAX_RESULTS):
    words = ["live","stream","clip","highlight","vod","chat","sub","raid","hype","train",
             "pog","lul","kek","omegalul","trihard","pepehands","pepelaugh","sadge","catjam",
             "copium","hopium","monkas","pepega","widepeepo","booba","nodders","nodge"]
    await run_scan(ctx, words, "STREAMER", C["neon"], "📺", limit)

@bot.command(name="artist")
async def cmd_artist(ctx, limit: int = MAX_RESULTS):
    words = ["canvas","brush","stroke","palette","sketch","draft","ink","line","curve","shape",
             "color","hue","tone","shade","tint","pigment","dye","stain","wash","blot",
             "abstract","surreal","realist","impressionist","expressionist","minimalist","maximalist"]
    await run_scan(ctx, words, "ARTIST", C["color"], "🎨", limit)

@bot.command(name="hacker")
async def cmd_hacker(ctx, limit: int = MAX_RESULTS):
    await run_scan(ctx, THEMES["cyber"], "HACKER", C["cyber"], "👾", limit)

@bot.command(name="developer")
async def cmd_developer(ctx, limit: int = MAX_RESULTS):
    words = ["code","hack","debug","compile","deploy","push","pull","merge","fork","clone",
             "commit","branch","patch","hotfix","refactor","rebase","stash","diff","blame","grep",
             "sudo","chmod","bash","shell","script","kernel","daemon","thread","stack","heap"]
    await run_scan(ctx, words, "DEVELOPER", C["cyber"], "💻", limit)

@bot.command(name="designer")
async def cmd_designer(ctx, limit: int = MAX_RESULTS):
    words = ["pixel","vector","raster","gradient","blend","layer","mask","clip","path","anchor",
             "bezier","curve","font","serif","sans","mono","kerning","tracking","leading","weight",
             "grid","column","gutter","margin","padding","whitespace","contrast","ratio","scale","rhythm"]
    await run_scan(ctx, words, "DESIGNER", C["aesthetic"], "✏️", limit)

@bot.command(name="creator")
async def cmd_creator(ctx, limit: int = MAX_RESULTS):
    words = THEMES["brandable"]
    await run_scan(ctx, words, "CREATOR", C["og"], "✨", limit)

# ── STATS SERVEUR ─────────────────────────────────────────────────────────────

@bot.command(name="serverstats")
async def cmd_serverstats(ctx):
    STATS["commands"] += 1
    total_users = sum(1 for ws in WATCHLIST.values() for w in ws)
    total_favs  = sum(len(v) for v in FAVORITES.values())
    total_hist  = sum(len(v) for v in HISTORY.values())
    e = discord.Embed(title="📊  Stats serveur", color=C["stats"])
    e.add_field(name="🔍  Scans",          value=f"`{STATS['scans']:,}`",    inline=True)
    e.add_field(name="✅  Trouvés",         value=f"`{STATS['found']:,}`",    inline=True)
    e.add_field(name="📡  Checks",          value=f"`{STATS['checked']:,}`",  inline=True)
    e.add_field(name="👀  Watch actifs",    value=f"`{total_users}`",          inline=True)
    e.add_field(name="⭐  Favoris total",   value=f"`{total_favs}`",           inline=True)
    e.add_field(name="📜  Historique",      value=f"`{total_hist}`",           inline=True)
    e.add_field(name="🏆  Chasseurs",       value=f"`{len(LEADERBOARD)}`",     inline=True)
    e.set_footer(text="meanings · serverstats")
    await ctx.send(embed=e)

@bot.command(name="serverleaderboard")
async def cmd_serverleaderboard(ctx):
    await cmd_leaderboard(ctx)

@bot.command(name="serverrecord")
async def cmd_serverrecord(ctx):
    STATS["commands"] += 1
    if not LEADERBOARD:
        await ctx.send(embed=make_embed("🏆  Aucun record","Pas encore de scans.",C["info"])); return
    best_user = max(LEADERBOARD, key=LEADERBOARD.get)
    best_score = LEADERBOARD[best_user]
    try:
        user = await bot.fetch_user(best_user)
        name = user.display_name
    except:
        name = f"User#{best_user}"
    best_pseudo = None
    for h in HISTORY.get(best_user, []):
        if h["available"] and (best_pseudo is None or len(h["pseudo"]) < len(best_pseudo)):
            best_pseudo = h["pseudo"]
    e = discord.Embed(title="🏆  Record serveur", color=C["og"])
    e.add_field(name="👑  Meilleur chasseur", value=f"> **{name}** — `{best_score}` trouvés", inline=False)
    if best_pseudo:
        e.add_field(name="🏅  Plus court pseudo", value=f"> `{best_pseudo}` ({len(best_pseudo)} chars)", inline=False)
    e.set_footer(text="meanings · serverrecord")
    await ctx.send(embed=e)

@bot.command(name="globalstats")
async def cmd_globalstats(ctx):
    await cmd_serverstats(ctx)

# ── CHECK AVANCÉ ──────────────────────────────────────────────────────────────

@bot.command(name="checkrandom")
async def cmd_checkrandom(ctx, limit: int = 5):
    """Check des pseudos aléatoires"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 10))
    words = random.sample(ALL_FR+ALL_EN, min(20, len(ALL_FR)+len(ALL_EN)))
    words = [w for w in words if is_valid(w)][:limit*2]
    msg = await ctx.send(embed=make_embed(description=f"```\n🎲  Check {len(words)} aléatoires...\n```",footer="checkrandom"))
    results = {}
    async with aiohttp.ClientSession() as session:
        for w in words[:limit*2]:
            results[w] = await check_available(session, w)
            await asyncio.sleep(CHECK_DELAY)
    lines = [f"> {'✅' if r is True else '❌' if r is False else '⚠️'} `{w}`" for w,r in list(results.items())[:limit]]
    e = discord.Embed(title=f"🎲  Check aléatoire",description="\n".join(lines),color=C["info"])
    e.set_footer(text="meanings · checkrandom")
    await msg.edit(embed=e)

@bot.command(name="checkbulk")
async def cmd_checkbulk(ctx, *, mots: str = None):
    """Alias de +checklist"""
    if not mots:
        await ctx.send(embed=make_embed("❌  Usage",">`+checkbulk mot1 mot2 ...`",C["error"])); return
    await cmd_checklist(ctx, mots=mots)

@bot.command(name="checkscore")
async def cmd_checkscore(ctx, *, mot: str = None):
    """Score OG d'un pseudo"""
    await cmd_checkstats(ctx, mot=mot)

@bot.command(name="checkrare")
async def cmd_checkrare(ctx, limit: int = MAX_RESULTS):
    """Scan uniquement les pseudos rares (3-5 chars)"""
    await run_scan(ctx, ALL_FR+ALL_EN, "RARE", C["og"], "💎", limit, min_len=3, max_len=5)

# ── VANITY MODES SPÉCIAUX ─────────────────────────────────────────────────────

@bot.command(name="vanitymega")
async def cmd_vanitymega(ctx, limit: int = MAX_RESULTS):
    """Vanity scan mega — 300 candidats"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n💪  Mega vanity scan...\n```", footer="vanitymega"))
    raw = build_pool(mixed, 300, 3, 16)
    candidates = [c for c in raw if is_vanity_allowed(c)]
    found, checked = await _scan_engine(candidates, limit, msg, "💪", "VANITY MEGA", C["neon"], check_vanity, True, ctx)
    await msg.edit(embed=result_embed(found, checked, "💪", "VANITY MEGA", C["neon"], is_vanity=True))

@bot.command(name="vanitydeep")
async def cmd_vanitydeep(ctx, limit: int = MAX_RESULTS):
    """Vanity scan approfondi"""
    STATS["commands"] += 1
    limit = max(1, min(limit, 30))
    mixed = ALL_FR + ALL_EN
    msg = await ctx.send(embed=make_embed(description="```\n🔬  Deep vanity scan...\n```", footer="vanitydeep"))
    raw = build_pool(mixed, 200, 3, 16)
    candidates = [c for c in raw if is_vanity_allowed(c)]
    found, checked = await _scan_engine(candidates, limit, msg, "🔬", "VANITY DEEP", C["mix"], check_vanity, True, ctx)
    await msg.edit(embed=result_embed(found, checked, "🔬", "VANITY DEEP", C["mix"], is_vanity=True))

@bot.command(name="vanitylucky")
async def cmd_vanitylucky(ctx):
    """Alias luckyvanity"""
    await cmd_luckyvanity(ctx)

@bot.command(name="vanitymythologie")
async def cmd_vanitymythologie(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["mythologie"], "MYTHOLOGIE", C["myth"], "🏛️", limit)

@bot.command(name="vanitygemstones")
async def cmd_vanitygemstones(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["gemstones"], "GEMS", C["gem"], "💎", limit)

@bot.command(name="vanitymetals")
async def cmd_vanitymetals(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["metals"], "METALS", C["metal"], "🔩", limit)

@bot.command(name="vanitycolors")
async def cmd_vanitycolors(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["colorsen"]+THEMES["colorsfr"], "COLORS", C["color"], "🎨", limit)

@bot.command(name="vanityduality")
async def cmd_vanityduality(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["duality"], "DUALITY", C["mix"], "☯️", limit)

@bot.command(name="vanitygladiator2")
async def cmd_vanitygladiator2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["gladiator"], "GLADIATOR", C["war"], "⚔️", limit)

@bot.command(name="vanitydragon2")
async def cmd_vanitydragon2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["dragon"], "DRAGON", C["fire"], "🐉", limit)

@bot.command(name="vanitywitch2")
async def cmd_vanitywitch2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["witch"], "WITCH", C["magic"], "🧙", limit)

@bot.command(name="vanitydemon2")
async def cmd_vanitydemon2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["demon"], "DEMON", C["dark2"], "👿", limit)

@bot.command(name="vanityangel2")
async def cmd_vanityangel2(ctx, limit: int = MAX_RESULTS):
    await run_vanity_scan(ctx, THEMES["angel"], "ANGEL", C["color"], "👼", limit)

# ── INFOS SUPPLÉMENTAIRES ─────────────────────────────────────────────────────

@bot.command(name="themes")
async def cmd_themes(ctx):
    STATS["commands"] += 1
    names = sorted(THEMES.keys())
    lines = [f"> `+{n}`" for n in names]
    # Split en 3 colonnes
    third = math.ceil(len(lines)/3)
    e = discord.Embed(title=f"🎨  Thèmes disponibles — {len(names)}", color=C["info"])
    e.add_field(name="​", value="\n".join(lines[:third]),       inline=True)
    e.add_field(name="​", value="\n".join(lines[third:third*2]),inline=True)
    e.add_field(name="​", value="\n".join(lines[third*2:]),     inline=True)
    e.set_footer(text="meanings · themes · +<theme> pour scanner")
    await ctx.send(embed=e)

@bot.command(name="commands")
async def cmd_commands(ctx):
    STATS["commands"] += 1
    total = TOTAL_CMDS
    e = discord.Embed(title=f"⌨️  Total commandes : {total}", color=C["info"])
    for key, cat in HELP_CATEGORIES.items():
        e.add_field(name=f"{cat['emoji']} {cat['label']}", value=f"`{len(cat['cmds'])} cmds`", inline=True)
    e.set_footer(text="meanings · +helpall pour tout voir")
    await ctx.send(embed=e)

@bot.command(name="about")
async def cmd_about(ctx):
    STATS["commands"] += 1
    uptime = int(time.time()-START_TIME)
    h, m = divmod(uptime//60, 60)
    e = discord.Embed(
        title="✦  meanings — About",
        description=(
            "> Bot de recherche de pseudos et vanity Discord.\n"
            f"> **{TOTAL_CMDS} commandes** · Préfixe `+`\n"
            f"> `{len(ALL_FR):,}` mots FR · `{len(ALL_EN):,}` mots EN · `{len(ALL_CITIES):,}` villes\n"
            f"> `{len(THEMES)}` thèmes · Uptime `{h}h {m}m`"
        ),
        color=C["info"]
    )
    e.set_footer(text="meanings v4.0 · +help pour l'aide")
    await ctx.send(embed=e)

@bot.command(name="ratelimit")
async def cmd_ratelimit(ctx):
    STATS["commands"] += 1
    delay = CONFIG["check_delay"]
    parallel = CONFIG["parallel"]
    cpm = round(60 / delay * parallel)
    e = discord.Embed(title="⚡  Rate Limit Info", color=C["info"])
    e.add_field(name="⏱️  Délai",        value=f"`{delay}s`",     inline=True)
    e.add_field(name="🔀  Parallèle",    value=f"`{parallel}`",   inline=True)
    e.add_field(name="📊  Checks/min",   value=f"~`{cpm}`",       inline=True)
    e.add_field(name="💡  Conseil",
        value="> Si tu vois des 429, utilise `+setdelay 0.5` ou `+snail`",
        inline=False)
    e.set_footer(text="meanings · ratelimit")
    await ctx.send(embed=e)

@bot.command(name="status")
async def cmd_status(ctx):
    STATS["commands"] += 1
    uptime = int(time.time()-START_TIME)
    h, m = divmod(uptime//60, 60)
    lat = round(bot.latency*1000)
    color = C["check"] if lat < 100 else C["warn"] if lat < 300 else C["error"]
    e = discord.Embed(title="🟢  Bot en ligne", color=color)
    e.add_field(name="🏓  Latence", value=f"`{lat}ms`",     inline=True)
    e.add_field(name="⏱️  Uptime",  value=f"`{h}h {m}m`",  inline=True)
    e.add_field(name="📊  Scans",   value=f"`{STATS['scans']:,}`", inline=True)
    e.set_footer(text="meanings · status")
    await ctx.send(embed=e)

@bot.command(name="myhistory")
async def cmd_myhistory(ctx):
    await cmd_history(ctx)

@bot.command(name="mytime")
async def cmd_mytime(ctx):
    STATS["commands"] += 1
    hist = HISTORY[ctx.author.id]
    if not hist:
        await ctx.send(embed=make_embed("📜  Aucun historique","Lance un scan.",C["info"])); return
    first = datetime.fromtimestamp(hist[0]["ts"]).strftime("%d/%m/%Y %H:%M")
    last  = datetime.fromtimestamp(hist[-1]["ts"]).strftime("%d/%m/%Y %H:%M")
    e = discord.Embed(title="⏱️  Ton activité", color=C["profile"])
    e.add_field(name="📅  Premier scan",  value=f"`{first}`",        inline=True)
    e.add_field(name="📅  Dernier scan",  value=f"`{last}`",         inline=True)
    e.add_field(name="📊  Total entries", value=f"`{len(hist)}`",    inline=True)
    e.set_footer(text="meanings · mytime")
    await ctx.send(embed=e)

@bot.command(name="myscore")
async def cmd_myscore(ctx):
    STATS["commands"] += 1
    found = sum(1 for h in HISTORY[ctx.author.id] if h["available"])
    score = found * 10
    rank = sorted(LEADERBOARD.items(), key=lambda x: x[1], reverse=True)
    my_rank = next((i+1 for i, x in enumerate(rank) if x[0] == ctx.author.id), "?")
    e = discord.Embed(title="🏆  Ton score", color=C["og"])
    e.add_field(name="⭐  Score",   value=f"`{score} pts`",  inline=True)
    e.add_field(name="🏆  Rang",    value=f"`#{my_rank}`",   inline=True)
    e.add_field(name="✅  Trouvés", value=f"`{found}`",      inline=True)
    e.set_footer(text="meanings · myscore")
    await ctx.send(embed=e)

bot.run(BOT_TOKEN)
