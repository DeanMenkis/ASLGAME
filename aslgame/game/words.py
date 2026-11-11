"""Word decks: themed word lists, sorted into levels by length, and drawn fresh for every run."""

from dataclasses import dataclass

from aslgame import config

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Drawn letters are slower to sign, so a short word with one is never Easy.
DRAWN_LETTERS = frozenset("JZ")


@dataclass(frozen=True)
class Deck:
    name: str
    title: str
    words: tuple
    ordered: bool = False  # signed in the order written, at every level
    by_need: bool = False  # words are drawn by how much their letters need practice


def _deck(name, title, text):
    return Deck(name, title, tuple(text.split()))


DECKS = (
    Deck("alphabet", "A to Z", (ALPHABET,), ordered=True),
    _deck("hello", "First Words", """
        HI HEY YES NO OK BYE YOU ME WE NAME GOOD DAY HELP LOVE SIGN HAND NICE MEET FINE SURE HOW WHO WHAT MORE
        HELLO PLEASE SORRY THANK FRIEND AGAIN LEARN SPELL SMILE HAPPY LATER MAYBE WHERE EXCUSE ENJOY FINGER LETTER THANKS
        WELCOME MORNING GOODBYE EVENING TOGETHER PRACTICE LANGUAGE ALPHABET QUESTION STUDENT TEACHER BIRTHDAY AWESOME
        PATIENCE EVERYONE NEIGHBOR"""),
    _deck("home", "Home", """
        MOM DAD BABY HOME ROOM DOOR BED SOFA LAMP RUG COOK EAT CUP BOWL SOAP BATH BOOK PET YARD GATE ROOF WALL AUNT KIN TEA NEST
        FAMILY MOTHER FATHER SISTER HOUSE TABLE CHAIR WINDOW GARDEN DINNER COUCH UNCLE COUSIN PILLOW MIRROR CLOSET GARAGE
        SHELF STAIRS PARENT COZY
        BROTHER KITCHEN BEDROOM GRANDMA GRANDPA BREAKFAST BLANKET FIREPLACE NEIGHBOR CHILDREN BATHROOM DAUGHTER HUSBAND
        PICTURE UPSTAIRS HOMEWORK"""),
    _deck("wild", "Animals", """
        CAT DOG FOX OWL BAT COW PIG HEN BEE ANT FROG FISH BEAR WOLF DEER LION DUCK CRAB SEAL GOAT MOLE HAWK TOAD BIRD WORM SWAN
        TIGER HORSE MOUSE SNAKE WHALE SHARK EAGLE RABBIT MONKEY PARROT TURTLE SPIDER ZEBRA JAGUAR LLAMA OTTER PANDA KOALA
        LIZARD BEAVER FALCON DONKEY
        GIRAFFE DOLPHIN PENGUIN ELEPHANT KANGAROO BUTTERFLY CROCODILE SQUIRREL HEDGEHOG FLAMINGO OCTOPUS GORILLA CHEETAH
        RACCOON HAMSTER LEOPARD"""),
    _deck("nature", "Fire and Water", """
        FIRE RAIN WAVE LAKE SEA SUN WIND LEAF TREE ROCK SAND SNOW ICE HILL POND MOSS SEED FERN MUD DEW ASH COAL FOG BAY TIDE GLOW
        FLAME WATER RIVER OCEAN STORM CLOUD EARTH STONE FOREST FLOWER LIQUID STREAM GARDEN SPRING SUMMER WINTER AUTUMN EMBER
        BREEZE FROZEN JUNGLE MEADOW
        VOLCANO RAINBOW THUNDER MOUNTAIN WATERFALL SUNSHINE CAMPFIRE BLOSSOM GLACIER HURRICANE WILDFIRE SNOWFLAKE RAINDROP
        TORNADO LANDSCAPE SEASHORE"""),
    _deck("night", "Night Sky", """
        MOON STAR DARK GLOW NAP BED OWL SKY WISH CALM REST HUSH DUSK DAWN BAT COOL DEEP FAR MIST HALO NOVA ORB
        DREAM SLEEP NIGHT LIGHT SPACE COMET ORBIT PLANET ROCKET SHADOW QUIET CLOUD SILVER PILLOW SLEEPY GALAXY WONDER LUNAR
        ZENITH NEBULA
        MIDNIGHT STARLIGHT ELECTRIC UNIVERSE TWILIGHT MOONBEAM SLUMBER LULLABY BLANKET DREAMER ECLIPSE FIREFLY ASTRONAUT
        TELESCOPE HORIZON INFINITY"""),
    _deck("music", "Music", """
        SONG BEAT DRUM TUNE SING BASS NOTE CLAP TAP HUM BAND FUNK SOUL ROCK POP RAP LOUD SOFT PLAY MIX KEY HORN HARP DUET SOLO TONE
        DANCE GROOVE RHYTHM PIANO GUITAR MELODY TEMPO CHORUS FUNKY HOUSE VINYL RADIO VOICE STAGE DISCO JAZZ VIOLIN SINGER LYRIC
        TRUMPET SHUFFLE HARMONY CONCERT SPEAKER MUSICIAN KEYBOARD DRUMMER PLAYLIST ORCHESTRA SAXOPHONE FESTIVAL FREESTYLE
        DANCING ACOUSTIC BASSLINE"""),
    _deck("move", "Body and Motion", """
        RUN HOP SKIP KICK SPIN STEP WALK ARM LEG FOOT HAND HEAD KNEE TOE BACK DASH LEAP ROLL SWIM BALL GOAL TEAM FAST PUSH PULL
        JUMP BOUNCE DANCE CLIMB THROW CATCH SPRINT STRONG ELBOW WRIST FINGER MUSCLE SPORT RACER SKATE DODGE TWIST REACH
        BALANCE STRETCH EXERCISE SHOULDER FOOTBALL BASEBALL SWIMMING MARATHON GYMNAST CYCLING HANDSTAND WORKOUT VOLLEYBALL
        CHAMPION ATHLETE TRAMPOLINE"""),
    _deck("party", "Party", """
        CAKE GIFT FUN YAY PLAY GAME WIN HAT CUP PIE CHIP DIP SODA BOW CARD HUG SING GLAD WOW TOY POP MILK TACO
        PARTY HAPPY CANDY CHEER DANCE PIZZA FRIEND CANDLE PRIZE LAUGH SMILE INVITE RIBBON COOKIE DONUT SWEET JOY JUICE FIESTA
        BANNER GIGGLE PARADE TREAT
        VICTORY BALLOON BIRTHDAY CONFETTI PRESENT SURPRISE CELEBRATE FIREWORKS SPARKLE CUPCAKE LEMONADE POPCORN FESTIVAL
        CHOCOLATE WEEKEND TOGETHER"""),
    _deck("quest", "Quest", """
        HERO MAP GOLD KING CAVE SHIP BOW AXE KEY DOOR PATH FOE WAR RUN HIDE SEEK FIND LOST BOLD OATH RUBY GEM MASK CAPE DUEL TRAP
        QUEST SWORD SHIELD DRAGON KNIGHT CASTLE MAGIC WIZARD BRAVE ARMOR ARROW TOWER BATTLE RESCUE LEGEND SECRET ESCAPE PIRATE
        JOKER RIVAL HONOR VALOR
        JOURNEY VILLAIN MONSTER VICTORY WARRIOR KINGDOM TREASURE VENGEANCE ADVENTURE CHAMPION GUARDIAN EXPLORER MYSTERY
        COURAGE DUNGEON FORTRESS"""),
    _deck("power", "Power", """
        FAST BOLT RUSH FIRE HEAT BOOM BANG KICK DASH PUSH HARD LOUD WILD BOLD IRON FUEL GEAR RACE WIN MAX GRIT TANK VOLT WATT CORE
        POWER SPEED TURBO SURGE LASER BLAST FORCE STORM MOTOR ENGINE ROCKET STRONG ENERGY BRAVE STEEL TITAN CRUSH ZAP BLAZE
        FIERCE HYPER
        THUNDER MACHINE MAXIMUM VOLTAGE EXPLODE OVERDRIVE HARDSTYLE LIGHTNING UNSTOPPABLE VELOCITY MOMENTUM STRENGTH POWERFUL
        DYNAMITE FEARLESS SUPERSONIC"""),
)
EVERYTHING = Deck("everything", "Everything", tuple(sorted({word for deck in DECKS[1:] for word in deck.words})))
# Every word, dealt so the letters the player finds hard come up most.
PRACTISE = Deck("practise", "Practise", EVERYTHING.words, by_need=True)
DECKS = DECKS[:1] + (PRACTISE,) + DECKS[1:] + (EVERYTHING,)
DECKS_BY_NAME = {deck.name: deck for deck in DECKS}


def level_of(word):
    """0 Easy, 1 Medium, 2 Hard: longer words are harder, and a drawn letter lifts a short word to Medium."""
    easy_max, medium_max = config.LEVEL_MAX_WORD_LETTERS
    if len(word) > medium_max:
        return 2
    if len(word) > easy_max or DRAWN_LETTERS & set(word):
        return 1
    return 0


def pool(deck, level, sign_names):
    """The deck's words for a level that can be signed with the recorded letters."""
    return [word for word in deck.words
            if (deck.ordered or level_of(word) == level) and all(letter in sign_names for letter in word)]


def word_need(word, letter_need):
    """How much a word is worth practising: the mean need of its letters, sharpened so weak letters stand out."""
    return (sum(letter_need(letter) for letter in word) / len(word)) ** config.PRACTISE_SHARPNESS + config.PRACTISE_BASE_WEIGHT


def shuffled(words, rng, weight=None):
    """A shuffle. With weight, heavier words tend to come first, and every word still appears once."""
    if weight is None:
        batch = list(words)
        rng.shuffle(batch)
        return batch
    return sorted(words, key=lambda word: rng.random() ** (1.0 / weight(word)), reverse=True)


def draw_words(deck, level, min_signs, rng, sign_names, letter_need=None):
    """Words for one run with at least min_signs letters in all: shuffled, with no word twice in a row.

    letter_need gives each letter's need for practice, from 0 to 1; only a deck drawn by need uses it.
    """
    words = pool(deck, level, sign_names)
    if not words:
        return []
    weight = (lambda word: word_need(word, letter_need)) if deck.by_need and letter_need else None
    drawn, letters = [], 0
    while letters < min_signs:
        batch = list(words) if deck.ordered else shuffled(words, rng, weight)
        if not deck.ordered and drawn and len(batch) > 1 and batch[0] == drawn[-1]:
            batch.append(batch.pop(0))
        for word in batch:
            drawn.append(word)
            letters += len(word)
            if letters >= min_signs:
                break
    return drawn
