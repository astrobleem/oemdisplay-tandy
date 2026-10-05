"""Documented original authoring seed. STARTER.JSON is the editable source of truth.
This script is only for reproducing the initial curation, not for normal builds.
"""
import json
from pathlib import Path

QUESTION_TEXT = '''real|Is your character a real person?
fictional|Is your character fictional or legendary?
male|Is your character male?
female|Is your character female?
human|Is your character human?
young|Is your character usually a child or teenager?
animal|Is your character an animal rather than a human?
robot|Is your character a robot or artificial machine?
alien|Is your character from another planet?
magical_being|Is your character a magical or supernatural being?
monster|Is your character usually called a monster?
villain|Is your character mainly a villain?
hero|Is your character known for heroic adventures?
royal|Is your character royalty?
crown|Is your character often shown wearing a crown or tiara?
leader|Is your character a ruler, commander, or national leader?
sidekick|Is your character often a hero's helper or sidekick?
comic_relief|Is being funny a major part of your character's role?
video_origin|Did your character first become known in video games?
animation_origin|Did your character first become known in animation?
live_origin|Did your character first become known in live-action fiction?
comics_origin|Did your character first become known in comics or comic strips?
books_origin|Did your character first become known in a book or story?
folklore|Is your character from folklore, legend, or mythology?
movie|Is your character strongly associated with movies?
tv|Is your character strongly associated with a television series?
singer|Is your character famous for singing or making music?
scientist|Is your character known as a scientist or mathematician?
politician|Is your character known for politics or governing?
athlete|Is your character famous for competitive sports or wrestling?
performer|Is your character a professional actor or stage entertainer?
adventurer|Is your character an explorer or adventurer?
fighter|Is your character known as a warrior or trained fighter?
detective|Is your character a detective or investigator?
inventor|Is your character known for inventing or building machines?
artist|Is your character famous as an author or visual artist?
business|Is your character known for owning or running a business?
wizard|Is your character a wizard, witch, or sorcerer?
student|Is your character usually a student?
food|Is your character strongly associated with food or cooking?
american|Is your character mainly associated with the United States?
japanese|Was your character created in Japan?
british|Is your character mainly associated with Britain?
french|Is your character mainly associated with France?
european|Is your character mainly associated with continental Europe?
african|Is your character strongly associated with Africa?
asian|Is your character strongly associated with Asia outside Japan?
pre1800|Is this a real historical person who lived before 1800?
nineteenth|Is this a real historical person active in the 1800s?
old_fiction|Was your fictional character known before 1950?
mid_fiction|Did your fictional character debut between 1950 and 1979?
late_fiction|Did your fictional character debut between 1980 and 1999?
new_fiction|Did your fictional character debut in 2000 or later?
red|Is red a major color in your character's usual appearance?
blue|Is blue a major color in your character's usual appearance?
green|Is green a major color in your character's usual appearance?
pink|Is pink a major color in your character's usual appearance?
yellow|Is yellow or gold a major color in your character's appearance?
black|Is black a major color in your character's usual appearance?
white|Is white a major color in your character's usual appearance?
purple|Is purple a major color in your character's usual appearance?
hat|Does your character often wear a hat?
mask|Does your character usually wear a mask or helmet?
cape|Does your character often wear a cape or cloak?
uniform|Does your character often wear a work or military uniform?
formal|Is your character often shown in a suit or formal clothes?
glasses|Is your character usually shown wearing glasses?
moustache|Is your character known for having a moustache?
beard|Is your character known for having a beard?
blond|Is your character usually shown with blond hair?
dark_hair|Is your character usually shown with dark hair?
bald|Is your character usually bald or almost bald?
long_hair|Is your character usually shown with long hair?
unusual_skin|Does your character have an unusual nonhuman skin color?
fur|Does your character have fur?
feathers|Does your character have feathers?
tail|Does your character have a tail?
big_ears|Does your character have conspicuously large or pointed ears?
small|Is your character much smaller than an average adult human?
large|Is your character unusually large or bulky?
strength|Does your character have extraordinary physical strength?
flies|Can your character fly without an ordinary aircraft?
magic|Does your character use magic or supernatural powers?
speed|Is your character known for extraordinary speed?
transforms|Does your character famously change shape or physical form?
sword|Is your character associated with a sword or lightsaber?
gun|Is your character associated with a gun or blaster?
martial|Is your character known for martial arts or hand-to-hand combat?
gadgets|Does your character rely on special tools or gadgets?
instrument|Is your character known for playing a musical instrument?
dance|Is your character famous for dancing?
ball_sport|Is your character famous for a sport involving a ball?
spacecraft|Is your character strongly associated with spacecraft?
vehicle|Is your character associated with a distinctive vehicle?
water|Is your character closely associated with water or the sea?
treasure|Does your character often search for treasure or ancient objects?
superhero|Is your character a costumed comic-book-style superhero?
rescue|Does your character often rescue or protect other people?
conquest|Does your character seek power by conquering or ruling others?
crime|Is your character strongly associated with crime stories?
space|Is your character strongly associated with outer space?
fantasy|Does your character belong mainly to a fantasy world?
ordinary|Does your character mainly inhabit an everyday Earth-like world?
future|Is your character's world strongly associated with future technology?
historical_setting|Is your character associated with a historical setting?
modern|Is your character associated with modern-day life?
comedy|Is your character mainly associated with comedy?
horror|Is your character strongly associated with horror stories?
romance|Is romance a major theme in your character's best-known story?
mystery|Are mysteries a major part of your character's stories?
team|Is your character a member of a well-known team or close group?
family|Are family relationships central to your character's story?
sibling|Does your character have a famous brother or sister?
animal_friend|Does your character have a well-known animal companion?
horse|Is your character often associated with riding a horse?
castle|Is your character strongly associated with a castle or kingdom?
nature|Is your character strongly associated with forests or wilderness?
city|Is your character closely associated with city life?
school|Is your character strongly associated with a school?
stage|Is your character known for appearing on a stage?
quest|Does your character undertake a major journey or quest?
science|Is science or technology central to your character's identity?
teacher|Is your character known as a teacher, scholar, or wise mentor?
peace|Is your character widely associated with peace or social justice?
gloves|Does your character often wear gloves?
wealthy|Is great wealth part of your character's well-known image?
catchphrase|Is your character known for a distinctive catchphrase?
red_hair|Is your character usually shown with red or orange hair?'''
QUESTIONS = [dict(id=l.split('|')[0], text=l.split('|')[1]) for l in QUESTION_TEXT.splitlines()]
assert len(QUESTIONS) == 128, len(QUESTIONS)
QIDS = [q['id'] for q in QUESTIONS]
SOURCES = {
 'nintendo': {'url':'https://mario.nintendo.com/ca/characters/','kind':'official publisher','scope':'Mario-family roles and appearance; checked 2026-10-05'},
 'zelda': {'url':'https://www.zelda.com/about/','kind':'official franchise reference','scope':'Reference route for Link and Zelda; broad traits independently curated'},
 'sonic': {'url':'https://sonic.sega.jp/SonicChannel/character/','kind':'official publisher reference','scope':'Reference route for Sonic, Tails, Knuckles; broad traits independently curated'},
 'pokemon': {'url':'https://www.pokemon.com/us/pokedex/pikachu','kind':'official publisher reference','scope':'Reference route for Pikachu; broad traits independently curated'},
 'dc': {'url':'https://www.dc.com/characters','kind':'official publisher','scope':'DC character catalog; Batman and Wonder Woman profiles checked 2026-10-05'},
 'batman': {'url':'https://www.dc.com/characters/batman','kind':'official publisher','scope':'Batman occupation, abilities, costume, wealth and first appearance checked 2026-10-05'},
 'wonderwoman': {'url':'https://www.dc.com/characters/wonder-woman','kind':'official publisher','scope':'Wonder Woman royalty, powers and first appearance checked 2026-10-05'},
 'marvel': {'url':'https://www.marvel.com/characters','kind':'official publisher reference','scope':'Reference route for Marvel characters; broad traits independently curated'},
 'starwars': {'url':'https://www.starwars.com/databank','kind':'official franchise','scope':'Catalog and Darth Vader/Luke Skywalker profiles checked 2026-10-05'},
 'disney': {'url':'https://characters.disney.com/','kind':'official publisher reference','scope':'Reference route for Disney characters; broad traits independently curated'},
 'nobel': {'url':'https://www.nobelprize.org/prizes/physics/1903/marie-curie/facts/','kind':'award institution reference','scope':'Reference route; automated page fetch blocked, not counted as independently verified'},
 'general': {'kind':'original general-knowledge curation','scope':'Common, non-niche character traits composed for this project; no Akinator data or questions used'},
}
BASES = {
 'game':'fictional video_origin late_fiction japanese fantasy hero adventurer quest',
 'cartoon':'fictional animation_origin tv comedy comic_relief american',
 'disney':'fictional animation_origin movie american fantasy',
 'comic':'fictional comics_origin movie american hero fighter superhero rescue team',
 'sw':'fictional live_origin movie mid_fiction american space future spacecraft fantasy team quest',
 'book':'fictional books_origin movie british',
 'real':'real human ordinary',
}
CHARS=[]
def add(name, group, tags, *, no='', unknown='', probably='', unlikely='', source='general', notes=''):
    ident=''.join(c.lower() if c.isalnum() else '_' for c in name).strip('_')
    while '__' in ident: ident=ident.replace('__','_')
    yes=set((BASES[group]+' '+tags).split())
    yes-=set(no.split())
    answers={q:0 for q in QIDS}
    for value, keys in ((4,yes),(2,unknown.split()),(3,probably.split()),(1,unlikely.split())):
        for q in keys:
            assert q in answers,(name,q)
            answers[q]=value
    CHARS.append({'id':ident,'name':name,'notes':notes or 'Use the best-known mainstream portrayal; isolated spin-offs do not determine answers.',
                  'sources':list(dict.fromkeys([source,'general'])), 'answers':answers})

add('Mario','game','male human red blue hat moustache dark_hair small gloves food rescue sibling catchphrase gadgets',source='nintendo',probably='strength speed transforms movie')
add('Luigi','game','male human green blue hat moustache dark_hair gloves sibling sidekick rescue gadgets',source='nintendo',probably='horror',notes='Green-clad Mario brother; ghost-catching is a recurring theme. Often a protagonist as well as a helper.')
add('Princess Peach','game','female human royal crown leader pink blond long_hair castle gloves family rescue',source='nintendo',probably='magic romance movie')
add('Bowser','game','male monster villain royal leader conquest green yellow red_hair tail large strength castle family',no='hero',source='nintendo',probably='magic',unknown='animal')
add('Link','game','male green hat blond sword fighter rescue castle nature horse treasure gadgets',source='zelda',unknown='human young',probably='magic',notes='Across the main games Link is Hylian; age varies. Classic green-clad version is the appearance reference.')
add('Princess Zelda','game','female royal crown leader blond long_hair magic castle rescue family',no='adventurer',source='zelda',unknown='human',probably='fighter pink white',notes='Hylian princess across the main Zelda games; costume varies, so some appearance values are tentative.')
add('Sonic the Hedgehog','game','male animal blue red white fur tail big_ears small speed gloves rescue team',source='sonic',probably='movie transforms')
add('Tails','game','male animal yellow white fur tail big_ears small flies inventor gadgets vehicle gloves sidekick team',source='sonic',probably='young')
add('Knuckles','game','male animal red white fur tail small strength fighter gloves treasure team',source='sonic',probably='martial',notes='Echidna character, guardian and powerful hand-to-hand fighter; the large-ear question is no.')
add('Pac-Man','game','male yellow small gloves food comedy comic_relief',no='',unknown='human animal',source='general')

add('Mega Man','game','male robot blue mask small young gun science future rescue gadgets',no='fantasy')
add('Donkey Kong','game','male animal fur large strength red nature food family',probably='hero',source='nintendo',notes='Modern tie-wearing Donkey Kong; early arcade villain role is not the main reference.')
add('Kirby','game','male pink small unusual_skin flies transforms magic food rescue',unknown='animal alien',probably='young')
add('Pikachu','game','animal yellow black fur tail big_ears small unusual_skin team sidekick',no='adventurer quest',unknown='male female',source='pokemon',probably='tv movie',notes='Generic Pikachu species mascot, not a claim about the sex of every Pikachu. Electric powers are not treated as wizardry.')
add('Ash Ketchum','cartoon','male human young red blue hat dark_hair gloves japanese late_fiction hero adventurer quest team animal_friend',no='american comic_relief comedy',source='pokemon')
add('Samus Aran','game','female human blond long_hair mask uniform gun gadgets science future spacecraft space fighter rescue transforms',no='fantasy',notes='Human bounty hunter wearing powered armor. Morph Ball is a recurring physical-form change.')
add('Lara Croft','game','female human british dark_hair long_hair gun fighter treasure nature wealthy',no='japanese fantasy',probably='movie historical_setting',notes='British archaeologist/adventurer; the games were created in Britain.')
add('Ryu','game','male human dark_hair white red gloves fighter martial team',no='adventurer quest fantasy',probably='magic')
add('Chun-Li','game','female human dark_hair blue white fighter martial detective asian city',no='adventurer quest fantasy')
add('Crash Bandicoot','game','male animal red_hair fur tail blue gloves small comedy comic_relief',no='japanese',probably='speed')
add('Steve','game','male human blue dark_hair beard nature gadgets sword new_fiction',no='japanese late_fiction',unknown='young',notes='Default classic Minecraft Steve avatar. Appearance and play style can be customized; weapon and adventure associations refer to standard gameplay.')
add('Gordon Freeman','game','male human glasses beard gun gadgets scientist science future alien red',no='japanese fantasy alien',probably='hero',notes='Human physicist from Half-Life. Orange protective suit counts as no for a major red color; corrected below.')
add('Master Chief','game','male human green mask uniform gun fighter science future spacecraft space rescue new_fiction',no='japanese late_fiction fantasy',probably='strength')
add('Kratos','game','male magical_being white red bald beard sword fighter strength magic large new_fiction family',no='late_fiction',probably='hero villain historical_setting',notes='God of War protagonist; antihero alignment varies across Greek and Norse stories.')
add('Yoshi','game','male animal green white red tail small food sidekick team',source='nintendo',probably='hero',unknown='young',notes='Green dinosaur-like Nintendo character; supernatural taxonomy and age left unspecified.')
add('Isabelle','game','female animal yellow fur tail small tv uniform new_fiction ordinary modern',no='late_fiction hero adventurer quest fantasy tv',source='nintendo',notes='Animal Crossing secretary and assistant, commonly wearing a work vest. Not a television-origin character.')
add('Mickey Mouse','cartoon','male animal black red white fur tail big_ears small gloves old_fiction movie catchphrase',source='disney')
add('Minnie Mouse','cartoon','female animal black red white pink fur tail big_ears small gloves old_fiction movie romance',source='disney')
add('Donald Duck','cartoon','male animal white blue yellow feathers small hat uniform old_fiction movie family catchphrase',source='disney')
add('Goofy','cartoon','male animal black fur big_ears hat gloves old_fiction movie family',source='disney',notes='Goofy is an anthropomorphic dog. Usual orange shirt is not counted as red.')
add('Bugs Bunny','cartoon','male animal fur tail big_ears small old_fiction movie catchphrase food white')
add('Daffy Duck','cartoon','male animal black feathers small old_fiction movie catchphrase')
add('Tweety','cartoon','male animal yellow feathers small old_fiction flies young')
add('Sylvester','cartoon','male animal black white fur tail small old_fiction catchphrase')
add('Tom','cartoon','male animal fur tail small old_fiction white',notes='Tom the cat from Tom and Jerry; best-known blue-gray and white appearance. Blue is tentative because designs vary.',probably='blue')
add('Jerry','cartoon','male animal fur tail big_ears small old_fiction',notes='Jerry the brown mouse from Tom and Jerry; does not usually wear clothes.')
add('Scooby-Doo','cartoon','male animal fur tail mid_fiction food mystery detective team animal_friend catchphrase')
add('Shaggy Rogers','cartoon','male human green dark_hair beard mid_fiction food mystery team animal_friend catchphrase',probably='young')
add('Fred Flintstone','cartoon','male human dark_hair black mid_fiction family historical_setting vehicle catchphrase',probably='large')
add('Barney Rubble','cartoon','male human blond mid_fiction family historical_setting vehicle small sidekick')
add('Homer Simpson','cartoon','male human white blue unusual_skin bald large late_fiction family food ordinary modern catchphrase')
add('Bart Simpson','cartoon','male human young red blue unusual_skin late_fiction family sibling school student ordinary modern catchphrase',notes='Orange-red shirt varies between artwork; red appearance is tentative.',probably='red')
add('Lisa Simpson','cartoon','female human young red unusual_skin late_fiction family sibling school student instrument ordinary modern',no='comic_relief',probably='peace')
add('Marge Simpson','cartoon','female human green blue unusual_skin long_hair late_fiction family ordinary modern')
add('SpongeBob SquarePants','cartoon','male animal yellow white unusual_skin small late_fiction food uniform water ordinary modern catchphrase team')
add('Patrick Star','cartoon','male animal pink green unusual_skin large late_fiction water sidekick ordinary modern team')
add('Squidward Tentacles','cartoon','male animal unusual_skin bald late_fiction water food uniform instrument artist ordinary modern',probably='green',notes='Octopus character from SpongeBob; blue-green coloration varies by artwork.')
add('Popeye','cartoon','male human white blue hat uniform old_fiction strength food water catchphrase',no='animation_origin',probably='hero',notes='Originally a comic-strip character; spinach and sailor outfit are the reference.',source='general')
add('Betty Boop','cartoon','female human black red dark_hair old_fiction singer performer dance stage romance')
add('Charlie Brown','cartoon','male human young yellow black bald mid_fiction family school student animal_friend ball_sport ordinary modern catchphrase',no='animation_origin',notes='Originally a newspaper comic-strip character, not television animation.')
add('Snoopy','cartoon','male animal white black fur tail small mid_fiction ordinary modern flies',no='animation_origin flies',notes='Originally a comic-strip character. Imagined flying-ace adventures do not make ordinary flight a yes.')
add('Garfield','cartoon','male animal red_hair black fur tail small late_fiction food ordinary modern',no='animation_origin',notes='Originally a comic-strip character. Orange fur is represented by red_hair because that question explicitly includes orange.')
add('Winnie the Pooh','cartoon','male animal yellow red fur small old_fiction food nature fantasy team',no='animation_origin american',probably='british',notes='Originally a British book character. Modern red-shirt appearance is used.')
add('Tigger','cartoon','male animal red_hair black fur tail old_fiction nature fantasy team',no='animation_origin american',probably='british',notes='Originally a British book character. Orange and black tiger with a springy tail.')
add('Elsa','disney','female human royal leader blond long_hair blue white magic new_fiction castle family sibling romance',source='disney',no='romance',probably='hero',notes='Frozen film portrayal. Familial love is central, but Elsa has no central romantic storyline.')
add('Anna','disney','female human royal crown leader red_hair long_hair green purple black new_fiction castle family sibling romance hero adventurer quest',source='disney',probably='crown',notes='Frozen films; Anna becomes queen. Costume colors and crown vary by installment.')
add('Mulan','disney','female human dark_hair long_hair fighter sword uniform horse hero rescue family asian historical_setting late_fiction',no='american',source='disney',probably='royal',unknown='royal',notes='Disney film portrayal of the Chinese legendary heroine. Not a literal princess; royalty set to no in final corrections.')
add('Ariel','disney','female magical_being red_hair long_hair green purple tail water royal romance late_fiction family transforms',source='disney',unknown='human',notes='Disney mermaid princess; humanity and tail change in the story, so human is unknown and transforms yes.')
add('Belle','disney','female human dark_hair long_hair yellow blue white romance late_fiction castle books_origin french european',no='books_origin',source='disney',probably='royal')
add('Aladdin','disney','male human dark_hair hat purple romance late_fiction castle adventurer quest animal_friend magic',source='disney',no='magic',probably='royal flies',notes='Disney animated-film portrayal; magic belongs mainly to companions and objects, not innate sorcery.')
add('Genie','disney','male magical_being blue unusual_skin beard magic flies transforms large comedy comic_relief sidekick late_fiction',source='disney')
add('Shrek','disney','male monster green unusual_skin large strength romance new_fiction nature comedy comic_relief quest',no='animation_origin',probably='hero',notes='DreamWorks ogre, originally in a 1990 book. The familiar movie appearance is the reference; not a Disney property.')
add('Donkey','disney','male animal fur tail big_ears sidekick comedy comic_relief new_fiction quest team',notes='Donkey from DreamWorks Shrek; not a Disney property.')
add('Woody','disney','male hat yellow red blue gloves family team late_fiction hero rescue',no='gloves',unknown='human',notes='Toy Story cowboy toy. Human-shaped toy is not a living human; corrected to no below.',source='disney')
add('Buzz Lightyear','disney','male white green purple mask space future team late_fiction hero rescue gadgets',unknown='robot',notes='Toy Story action figure rather than an actual astronaut. Electronic toy is not unambiguously a robot.',source='disney',probably='flies')
add('Simba','disney','male animal fur tail royal leader family romance late_fiction african nature hero',no='american',source='disney',unknown='young',probably='large')
add('Nala','disney','female animal fur tail royal family romance late_fiction african nature',no='american',source='disney',unknown='young',probably='large hero')
add('Batman','comic','male human black mask cape gloves gadgets martial detective crime city wealthy dark_hair old_fiction vehicle science',source='batman',probably='blue family')
add('Superman','comic','male alien blue red cape dark_hair strength flies speed old_fiction city family',source='dc',probably='gloves',no='gloves',notes='Kryptonian superhero in the familiar blue suit and red cape. Normally bare-handed.')
add('Wonder Woman','comic','female magical_being royal crown dark_hair long_hair red blue yellow strength flies magic sword martial old_fiction peace',source='wonderwoman',unknown='human')
add('Spider-Man','comic','male human red blue mask gloves young mid_fiction city science gadgets student school family',source='marvel',probably='strength',unknown='young student school',notes='Peter Parker; age varies from teenage student to adult across mainstream adaptations.')
add('Iron Man','comic','male human red yellow mask beard moustache wealthy inventor business gadgets science future flies strength mid_fiction city',source='marvel')
add('Captain America','comic','male human blue red white mask gloves uniform fighter strength old_fiction leader blond',source='marvel',probably='historical_setting')
add('Thor','comic','male magical_being royal blond long_hair cape red sword strength flies magic mid_fiction beard',no='sword',source='marvel',probably='beard',notes='Marvel portrayal, known for a hammer rather than a sword; not generic mythological Thor.')
add('Hulk','comic','male human green purple unusual_skin large strength transforms scientist science mid_fiction',source='marvel',unknown='human',notes='Bruce Banner/Hulk combined identity; ordinary human status depends on form.')
add('Black Panther','comic','male human royal leader black mask gloves strength martial african mid_fiction wealthy science gadgets',no='american',source='marvel')
add('Joker','comic','male human villain green purple white unusual_skin dark_hair crime city comedy mid_fiction',no='hero fighter superhero rescue team mid_fiction',source='dc',probably='comedy',notes='Joker debuted in 1940. Green hair is not classified as dark hair in final corrections.')
add('Harley Quinn','comic','female human villain red black white blond long_hair crime city comedy late_fiction martial gloves',no='comics_origin hero superhero rescue',source='dc',probably='villain hero',notes='First appeared in Batman animation. Antihero versus villain depends on portrayal.')
add('Darth Vader','sw','male human villain black mask cape uniform fighter sword magic leader conquest family strength large',source='starwars')
add('Luke Skywalker','sw','male human blond white black hero fighter sword magic rescue family sibling',source='starwars',probably='young',notes='Original-trilogy portrayal, aging into a mentor in later films.')
add('Princess Leia','sw','female human royal leader white dark_hair long_hair gun hero rescue family sibling',source='starwars')
add('Yoda','sw','male alien green unusual_skin small big_ears bald magical_being magic sword fighter hero teacher nature',source='starwars',no='magical_being',notes='Alien Jedi with Force abilities; not classified as a supernatural species.')
add('Chewbacca','sw','male alien animal fur large strength gun sidekick hero rescue vehicle',no='animal',source='starwars',notes='Wookiee alien, not classified as an Earth animal.')
add('R2-D2','sw','robot white blue small gadgets science sidekick hero rescue',source='starwars',probably='male flies',notes='Robot referred to with male pronouns; rocket boosters appear in some films.')
add('C-3PO','sw','robot yellow science sidekick comic_relief',source='starwars',probably='male')
add('Indiana Jones','sw','male human hat dark_hair gun gadgets hero adventurer treasure historical_setting teacher animal_friend horse late_fiction',no='mid_fiction space spacecraft fantasy future animal_friend',notes='Earthbound archaeologist from the Indiana Jones films; whip counts as a special tool.')
add('Sherlock Holmes','book','male human detective mystery crime city hat gadgets dark_hair instrument old_fiction historical_setting',probably='tv',notes='Victorian literary detective; deerstalker and violin are familiar depictions.')
add('James Bond','book','male human fighter martial gun gadgets formal dark_hair crime city vehicle old_fiction modern',probably='hero',notes='Ian Fleming secret agent, first published in 1953: corrected to mid-century below.')
add('Harry Potter','book','male human young student school glasses dark_hair wizard magic hero rescue family team quest castle late_fiction',probably='flies',notes='School-age novel and film portrayal. Broom flight is magical flight.')
add('Hermione Granger','book','female human young student school dark_hair long_hair wizard magic hero rescue team quest castle late_fiction',probably='teacher',no='teacher')
add('Ron Weasley','book','male human young student school red_hair wizard magic sidekick hero rescue family sibling team quest castle late_fiction')
add('Gandalf','book','male magical_being wizard magic white hat beard long_hair sword cape teacher hero rescue team quest fantasy old_fiction horse',unknown='human',notes='Tolkien wizard; human-looking supernatural being, so human is no in final corrections.')
add('Frodo Baggins','book','male small dark_hair sword hero team quest fantasy old_fiction nature',notes='Tolkien hobbit; not human and not a child in the main story.')
add('Aragorn','book','male human dark_hair long_hair beard sword fighter royal leader hero rescue team quest fantasy old_fiction horse castle nature')
add('Gollum','book','male small bald monster fantasy old_fiction nature treasure',unknown='villain',notes='Former hobbit with a conflicted role. The ring is treated as a prized treasure.')
add('Dracula','book','male magical_being monster villain dark_hair black cape horror old_fiction castle european transforms flies',probably='royal',no='royal',notes='Bram Stoker vampire count; nobility is not the same as royalty.')
add("Frankenstein's Monster",'book','male monster large strength black horror old_fiction european science',unknown='human',probably='green',notes='Artificially assembled humanlike creature. Green skin is a familiar screen convention, not universal.')
add('Santa Claus','book','male magical_being red white hat beard large glasses magic flies vehicle food old_fiction folklore nature',no='books_origin british nature',probably='glasses',notes='Folkloric Christmas gift-giver; appearance and details vary by tradition.')
add('Robin Hood','book','male human green hat hero fighter rescue nature old_fiction folklore historical_setting horse',no='books_origin',probably='sword',notes='Legendary English outlaw. Bow and arrow do not count as a gun.')
add('King Arthur','book','male human royal crown leader sword fighter hero castle old_fiction folklore historical_setting horse',no='books_origin',probably='beard',notes='Legendary king; the dataset does not claim historical proof of a specific real Arthur.')
add('Merlin','book','male magical_being wizard magic hat beard long_hair teacher castle old_fiction folklore historical_setting',no='books_origin',unknown='human',probably='blue')
add('Alice','book','female human young blond long_hair blue white fantasy old_fiction quest small',no='small',notes='Alice in Wonderland; size changes are part of the story.',probably='transforms')
add('Peter Pan','book','male human young green hat flies magic fantasy old_fiction quest sword hero rescue',no='books_origin',probably='books_origin',notes='First appeared in a novel, with the familiar story developed as a play; origin marked probably book.')
add('Mary Poppins','book','female human hat dark_hair magic flies gadgets teacher city old_fiction family',probably='singer',unknown='human',notes='Magical nanny; human status is not made definitive by the familiar story.')
add('Willy Wonka','book','male human hat purple formal food business wealthy mid_fiction fantasy',probably='singer')
add('Paddington Bear','book','male animal fur small blue red hat food city mid_fiction comedy comic_relief family',notes='Brown bear from Peru, best known in London with a blue duffel coat and red hat.')
add('Abraham Lincoln','real','male politician leader american beard black formal nineteenth historical_setting peace hat',unknown='red blue green pink yellow white purple gloves',notes='US president, 1809-1865; iconic beard without a moustache.')
add('George Washington','real','male politician leader american pre1800 historical_setting uniform white',unknown='red blue green pink yellow black purple gloves blond dark_hair',notes='US president and military commander; white powdered hairstyle is the familiar portrait image.')
add('Albert Einstein','real','male scientist teacher moustache white nineteenth european american science',unknown='red blue green pink yellow black purple gloves formal',no='nineteenth',notes='Physicist; public scientific career belongs mainly to the 20th century. White hair is the familiar later-life image.')
add('Isaac Newton','real','male scientist teacher long_hair british pre1800 historical_setting science',unknown='red blue green pink yellow black white purple gloves dark_hair blond formal',notes='English scientist and mathematician; no claim is made about everyday clothing colors.')
add('Marie Curie','real','female scientist teacher dark_hair long_hair european french nineteenth science',unknown='red blue green pink yellow black white purple gloves formal',source='nobel',notes='Polish-born scientist working in France. Scientific activity began in the 1800s and continued in the 1900s.')
add('Ada Lovelace','real','female scientist dark_hair long_hair british nineteenth historical_setting science',unknown='red blue green pink yellow black white purple gloves formal',notes='British mathematician associated with early computing; not credited here with physically building a machine.')
add('Leonardo da Vinci','real','male artist inventor scientist beard long_hair european pre1800 historical_setting science',unknown='red blue green pink yellow black white purple gloves formal',notes='Italian Renaissance artist and inventor; later-life bearded portrait is the reference.')
add('Cleopatra','real','female royal crown leader politician african pre1800 historical_setting dark_hair long_hair',unknown='red blue green pink yellow black white purple gloves formal',notes='Cleopatra VII of ancient Egypt; familiar dark-haired depiction is cultural iconography rather than a verified portrait.')
add('Joan of Arc','real','female fighter leader french european pre1800 historical_setting sword horse uniform',unknown='red blue green pink yellow black white purple gloves dark_hair blond',notes='French historical military figure; hair details are not confidently standardized.')
add('Nelson Mandela','real','male politician leader african peace modern',unknown='red blue green pink yellow black white purple gloves formal',notes='South African president and anti-apartheid leader. No current-life status question is used.')
add('Mahatma Gandhi','real','male politician leader asian peace glasses bald white nineteenth',no='politician',unknown='red blue green pink yellow black purple gloves formal',notes='Indian independence leader; not classified as a government officeholder. Public activism began in the 1890s.')
add('Amelia Earhart','real','female adventurer american vehicle historical_setting uniform',unknown='red blue green pink yellow black white purple gloves',notes='American aviation pioneer; ordinary aircraft do not make the supernatural flight question yes.')
add('Elvis Presley','real','male american singer performer dark_hair instrument dance stage movie white',unknown='red blue green pink yellow black purple gloves formal',notes='Recognizable later-career white stage jumpsuits; otherwise costume colors vary.')
add('Michael Jackson','real','male american singer performer dark_hair long_hair dance stage gloves black white hat',unknown='red blue green pink yellow purple formal',notes='Signature performance glove and stage imagery; no sensitive medical or appearance speculation.')
add('Dolly Parton','real','female american singer performer blond long_hair instrument stage business peace',no='peace',unknown='red blue green pink yellow black white purple gloves formal',notes='Country singer, songwriter, instrumentalist and businesswoman; outfits vary.')
add('Freddie Mercury','real','male british singer performer dark_hair moustache instrument stage',unknown='red blue green pink yellow black white purple gloves formal',notes='Queen frontman; the moustached 1980s stage appearance is the reference.')
add('Beyonce','real','female american singer performer long_hair dance stage business modern',unknown='red blue green pink yellow black white purple gloves formal blond dark_hair',notes='Stage performer; hairstyle and hair color vary, so no fixed color is asserted.')
add('Mr. T','real','male american performer tv movie beard dark_hair large strength catchphrase yellow',unknown='red blue green pink black white purple gloves formal',no='strength',notes='Actor and television personality; gold jewelry and distinctive hair/beard are recognizable. Real-world strength is not superhuman.')
add('Hulk Hogan','real','male american athlete performer tv moustache blond long_hair large yellow red catchphrase',unknown='blue green pink black white purple gloves formal',notes='Professional wrestler; blond handlebar moustache and yellow/red ring attire are iconic. No superhuman ability is asserted.')
add('Muhammad Ali','real','male american athlete dark_hair gloves peace',unknown='red blue green pink yellow black white purple formal',notes='Boxer and civil-rights figure. Boxing counts as trained hand-to-hand combat in final corrections.')
add('Serena Williams','real','female american athlete ball_sport dark_hair long_hair modern',unknown='red blue green pink yellow black white purple gloves formal',notes='Tennis champion; no fixed playing-outfit color is asserted.')
add('Colonel Sanders','real','male american business food glasses beard moustache white formal',unknown='red blue green pink yellow black purple gloves',notes='Harland Sanders, KFC founder and brand figure; white suit and facial hair are the reference.')

# Explicit review corrections keep the record of ambiguous authoring choices visible.
FIXES = {
 'mario': {'small':0},
 'princess_peach': {'family':0},
 'tails': {'young':4},
 'knuckles': {'martial':4},
 'pac_man': {'small':2,'adventurer':1,'quest':1},
 'mega_man': {'small':3},
 'yoshi': {'small':2},
 'gordon_freeman': {'red':0},
 'popeye': {'comics_origin':4},
 'charlie_brown': {'comics_origin':4},
 'snoopy': {'comics_origin':4},
 'garfield': {'comics_origin':4,'late_fiction':0,'mid_fiction':4},
 'winnie_the_pooh': {'books_origin':4,'british':4},
 'tigger': {'books_origin':4,'british':4},
 'mulan': {'royal':0,'folklore':4},
 'shrek': {'books_origin':4,'new_fiction':0,'late_fiction':4},
 'woody': {'human':0},
 'buzz_lightyear': {'human':0,'flies':0},
 'batman': {'business':4},
 'yoda': {'mid_fiction':0,'late_fiction':4,'leader':4},
 'princess_leia': {'politician':4,'fighter':3},
 'frodo_baggins': {'old_fiction':0,'mid_fiction':4},
 'aragorn': {'old_fiction':0,'mid_fiction':4,'crown':3},
 'harry_potter': {'cape':3,'animal_friend':4},
 'hermione_granger': {'cape':3,'animal_friend':4},
 'ron_weasley': {'cape':3,'animal_friend':4},
 'alice': {'small':3},
 'merlin': {'blue':2},
 'bart_simpson': {'blond':3,'small':3},
 'lisa_simpson': {'blond':3,'small':4},
 'charlie_brown': {'comics_origin':4,'small':4},
 'betty_boop': {'movie':4},
 'joker': {'old_fiction':4,'dark_hair':0},
 'harley_quinn': {'animation_origin':4,'superhero':1},
 'james_bond': {'old_fiction':0,'mid_fiction':4},
 'gandalf': {'human':0},
 'muhammad_ali': {'fighter':4,'martial':4},
}
for c in CHARS:
    c['answers'].update(FIXES.get(c['id'],{}))
    if c['id'] in ('mickey_mouse','minnie_mouse','donald_duck','goofy','bugs_bunny','daffy_duck',
                    'tweety','sylvester','tom','jerry','scooby_doo','shaggy_rogers','betty_boop'):
        c['answers']['ordinary']=4
        c['answers']['modern']=3
SOURCES['knuckles']={'url':'https://sonic.sega.jp/SonicChannel/character/knuckles.html','kind':'official publisher','scope':'Echidna species, martial arts, strength, treasure hunting and small stature checked 2026-10-05.'}
SOURCES['tails']={'url':'https://sonic.sega.jp/SonicChannel/character/tails.html','kind':'official publisher','scope':'Young fox, two tails, flight, inventor/mechanic, male and small stature checked 2026-10-05.'}
SOURCES['yoda']={'url':'https://www.starwars.com/databank/yoda','kind':'official franchise','scope':'Jedi teacher, small stature, lightsaber and Force powers checked 2026-10-05.'}
SOURCES['leia']={'url':'https://www.starwars.com/databank/leia-organa','kind':'official franchise','scope':'Human, princess, leader, senator, blaster and Luke sibling checked 2026-10-05.'}
SOURCES['kfc']={'url':'https://global.kfc.com/our-history','kind':'official company history','scope':'Harland Sanders, real business founder, food association and iconic white suit checked 2026-10-05.'}
SOURCES['isabelle']={'url':'https://www.nintendo.com/us/amiibo/detail/isabelle-amiibo-animal-crossing-series/','kind':'official publisher','scope':'Secretary role in Animal Crossing: New Leaf checked through publisher search excerpt 2026-10-05.'}
SOURCES['nobel_summary']={'url':'https://www.nobelprize.org/prizes/physics/1903/summary/','kind':'award institution','scope':'Marie Curie physics research confirmed through official search excerpt 2026-10-05; detailed facts page was blocked.'}
for ident, sourceid in [('knuckles','knuckles'),('tails','tails'),('yoda','yoda'),('princess_leia','leia'),('colonel_sanders','kfc'),('isabelle','isabelle'),('marie_curie','nobel_summary')]:
    next(c for c in CHARS if c['id']==ident)['sources'].insert(0,sourceid)
assert len(CHARS)==128,len(CHARS)
source = {'format_version':1,'title':'TANDINATOR Original Starter 128',
 'license_note':'Original questions and curated answer matrix. Character names and brands remain their owners\' property; no affiliation is implied. No Akinator database was used.',
 'portrayal_policy':'Best-known mainstream portrayals. Use UNKNOWN for conflicts, missing knowledge or distinctions that would require niche lore. Appearance uses the named familiar portrayal, not every costume or adaptation.',
 'answer_codes':{'NO':0,'PROBABLY_NO':1,'UNKNOWN':2,'PROBABLY_YES':3,'YES':4},
 'sources':SOURCES,'questions':QUESTIONS,'characters':CHARS}
Path(__file__).with_name('STARTER.JSON').write_text(json.dumps(source,ensure_ascii=True,indent=2)+'\n',encoding='ascii')
print('Wrote',len(CHARS),'characters and',len(QUESTIONS),'questions')
