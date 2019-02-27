import nltk
from nltk import tag
from nltk import word_tokenize
from clean_utils import CleanUtils
from numpy import argsort

import json
import os
import re
import networkx as nx
import itertools


class TestGenerator:

    def __init__(self, text, percentage=50):
        self.results = self.prepare_test_sentences(text, percentage)
        self.sentences = []

    @staticmethod
    def build_graph(nodes):
        gr = nx.Graph()
        gr.add_nodes_from(nodes)
        node_pairs = list(itertools.combinations(nodes, 2))

        for pair in node_pairs:
            first_string = pair[0]
            second_string = pair[1]
            lev_distance = nltk.edit_distance(first_string, second_string)
            gr.add_edge(first_string, second_string, weight=lev_distance)

        return gr

    def extract_sentences(self, text):
        sentence_tokens = CleanUtils.clean_text(text)
        self.sentences = [re.sub("\([^)]*\)", "", sent.replace(os.linesep, " ")) for sent in
                          CleanUtils.tokenize_sentences(text)]
        graph = self.build_graph(sentence_tokens)

        calculated_page_rank = nx.pagerank(graph, weight='weight')
        indices = argsort(list(calculated_page_rank.values()))[::-1]

        ranked_sentences = [x for _, x in sorted(zip(indices, self.sentences))]

        return ranked_sentences

    def extract_gaps(self):
        gaps = []
        for sentence, chunked_sentence in self.results:
            candidates_removed = 0
            chunks_removed = ""
            if "NB" not in chunked_sentence.values():
                for chunk_name in ["LNM", "NM"]:
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == chunk_name and candidates_removed <= 1:
                            sentence = sentence.replace(chunk, "_" * len(chunk))
                            candidates_removed += 1
                            chunks_removed += chunk + "$$$$"
                gaps.append((sentence, chunks_removed.split("$$$$")[:-1]))
        return gaps

    def extract_bonuses(self):
        bonuses = []
        for sentence, chunked_sentence in self.sentences:
            dsc_phrases = self.extract_description_phrases(chunked_sentence)
            if dsc_phrases:
                for object_of_description, phrase in dsc_phrases:
                    if len(phrase.strip().split(" ")) > 2:
                        bonuses.append((object_of_description, phrase))

        return bonuses

    def extract_sentence_completion(self):
        questions = []

        for sentence, chunked_sentence in self.sentences:
            """TODO"""

        return questions

    def prepare_test_sentences(self, text, percentage):
        summary_sentences = self.extract_sentences(text)
        test_size = int(len(summary_sentences) * percentage / 100)
        indexes = [self.sentences.index(sent) for sent in summary_sentences[:test_size]]
        test_sentences = [self.sentences[index] for index in indexes]

        results = []

        for sentence in test_sentences:
            chunked_sentence = self.chunk_sentence(sentence)
            if chunked_sentence:
                results.append((sentence, chunked_sentence))

        return results

    def chunk_sentence(self, sentence):
        sentence = word_tokenize(sentence)
        tagged = tag.pos_tag(sentence)

        grammar = {
            "NM": "{<DT>*<JJ.*>*<NNP.*>+(<IN><DT>*<JJ.*>*<NNP.*>+)*}",
            "NP": "{<DT>*<RB.*|JJ.*>+<NN.*>+}",
            "NB": "{(<IN><CD><TO|CC|NM|IN>*<CD|NM>*)"
                  "|((<IN><NM|,>+|<NM>)<CD><,>*<CD>*)}",
            "LNM": "{<NM>(<.>*<CC><NM>|<.><CC>*<NM>)+}",
            "DSC": "{<NM><VB.*>}",
            "DSCS": "{<DSC><.*>+}"
        }
        grammar_string = re.sub("(?<=}),", os.linesep, json.dumps(grammar)[1:-1].replace("\"", ""))

        cp = nltk.RegexpParser(grammar_string)
        parsed_sentence = cp.parse(tagged)
        results = {}

        for subtree in parsed_sentence.subtrees(filter=lambda t: t.label() in grammar.keys()):
            items = []
            for item in subtree.leaves():
                items.append(item[0])

            results[" ".join(items)] = subtree.label()
        return False if not results else results

    def extract_description_phrases(self, chunked_sentence):
        chunks = []
        for chunk, pos_tag in chunked_sentence.items():
            if pos_tag == "DSCS":
                tagged_chunk = self.chunk_sentence(chunk)
                if tagged_chunk:
                    description_chunks = [key for key, value in tagged_chunk.items() if
                                          value in ["DSC", "DSCS"]]
                    if description_chunks:
                        for object_of_description, description in self.extract_descriptions(description_chunks):
                            chunks.append((object_of_description, description))

        return chunks

    def extract_descriptions(self, description_chunks):
        descriptions = []
        object_of_description = description_chunks[0]
        delimiter = "$$$$"
        for index in range(1, len(description_chunks)):
            desc = description_chunks[index]
            if re.search("\s(is|are|was|were)", desc):
                object_of_description = object_of_description.replace(desc, delimiter)

        for description in object_of_description.split(delimiter)[1:]:
            description = description.split('.')[0].strip()
            if not self.is_there_tag(description, "PRP"):
                descriptions.append(description)

        return object_of_description, descriptions

    def is_there_tag(self, sentence, search):
        items = tag.pos_tag(word_tokenize(sentence))
        items = [val for key, val in items]
        for item in items:
            if search in item:
                return True
        return False


generator = TestGenerator("""
THE LEGEND OF SLEEPY HOLLOW
by Washington Irving
Adapted by Vivian E. Jackson
FOUND AMONG THE PAPERS OF THE LATE DIEDRICH
KNICKERBOCKER.
A pleasing land of drowsy head it was, Of dreams that wave before the half­shut eye;
And of gay castles in the clouds that pass, Forever flushing round a summer sky.
CASTLE OF INDOLENCE.
On the eastern shore of the Hudson River lies the small market town called
Greensburgh that is also known as Tarrytown in the
great State of New York. It is said that this name was
given by the housewives that lived nearby because
their husbands had the habit of hanging (tarrying)
around the local village tavern on market days. Not far
from this village is a small valley surrounded by hills,
and with a lovely brook. This place is said to be so
tranquil that on occasion you can only hear the sound
of a woodpecker.
I remember my first experience squirrel hunting
as a youngster. I wandered into a glen around
noontime. It was the type of place where you could go “and dream quietly away
the remnant of a troubled life.” There was no more of a serene place than this. The
echoing roar of my gun was the only angry noise that broke the stillness of this
place. The inhabitants of this place, which is known as Sleepy Hollow, are
descendants of the first Dutch setters. Their boys are called the Sleepy Hollow
Boys.
It is rumored that this glen is haunted by a High German doctor who practiced
sorcery. He is believed to have cast a spell on the little town of Sleepy Hollow.
Others say that it is haunted by an old Indian chief who held his powwows there
before Captain Henry Hudson discovered the place. It is certain that something has
a spell on the people that live there. The whole place is filled with tales that are
told all of the time. Sometimes, they say you can hear music and see strange sights.
The most powerful haunting in the glen is that of the headless horseman. Some say
he is the ghost of a Hessian trooper, a British mercenary, whose head was shot off
during the Revolutionary War. Anyone who has ever lived there has seen him
riding at night, “as if on the wings of the wind.” He travels through the glen, pass
the church, and down neighboring roads. He became known as the Headless
Horseman of Sleepy Hollow.
During a remote period in American History lived a teacher by the name of
Ichabod Crane. Crane was a native of Connecticut. He was described as a tall,
lanky man with long legs, a small head, huge ears, and a long nose. He gave the
appearance of a homeless person because of his baggy clothes. Ichabod was an
itinerant school teacher who came to Sleepy Hollow to fill the teaching vacancy.
Crane’s schoolhouse was a one­room building made of logs. The windows were
dull and they were “partly patched with leaves of old copybooks.” The school was
situated in a wooded area close to a brook. Children’s voices could be heard as
well as the authoritative voice of Crane who believed in the maxim “Spare the rod
and spoil the child." He administered punishment with discrimination. His rod
passed by the weak, but the tough­headed students got double portions of the rod.
However, his punishments were always followed by the assurance that the young
student would remember the punishment, and thank him in the long run. He made
sure to keep on good terms with his students because he was frequently a visitor in
their homes. Crane assisted the farmers with their chores and he would sit for hours
with little ones on his knee.
Ichabod Crane was considered the master singer of the neighborhood. He added to
his income by teaching music and on Sunday mornings he served as choir director.
“His voice resounded far above all the rest of the congregation” and his education
and accomplishments made him an important figure among the women. You would
see him on Sundays, during and after church, in the company of the country
damsels who admired his conversation. There were evenings he spent time, with
the older Dutch wives, listening to all the tales of Sleepy Hollow. He shared stories
of witches and witchcraft in Salem. In addition, Crane was prone to carry gossip
from one house to another.
Ichabod Crane was well­read. He was quite knowledgeable of Cotton Mather's
“History of New England Witchcraft.” After school, he would often retire to the
brook. He would lie there reading Mather’s book until dusk. Then, he would make
his way to his farmhouse as he traveled through the woods listening to the sounds
of nature. His imagination began to take over and ideas of ghosts and evil spirits
arose. They were the subjects of the tales the Dutch wives told. The only thing he
could do to drown those thoughts was to sing his way home. Neighbors would hear
him sing melodies that floated from the “distant hill.” All the while, Ichabod
walked towards home questioning every rustling shrub, sounds of howling from
the trees, glares from distant windows, shadows and shapes, and the sounds of his
own footsteps. “All these, however, were mere terrors of the night, phantoms of the
mind that walk in darkness.”
Ichabod held music classes one evening each week. One of his students was 18­
year­old Katrina Van Tassel, the daughter of a prominent Dutch family. He was
drawn to the beautiful girl. He visited her home, which was the mansion of her
father, Baltus Van Tassel who was a proud man that was not caught up in his
wealth. He took care of his family on his vast property, which was situated on the
banks of the Hudson River.
As he entered the mansion, Ichabod’s mouth watered as he pictured himself living
such a wealthy life and he desired Katrina even more. He knew that she would
inherit all that his eyes beheld. Immediately, his imagination flourished with the
idea of how he could turn it all into cash, and move Katrina and their children to
Kentucky, Tennessee or only God knows where.
Ichabod began to plot how to gain the affection of Katrina. There were difficulties
to handle. Katrina had many admirers who were always watching each other.
Abraham was his chief competitor because Katrina encouraged his advances. This
suitor was a handsome horseman and he was the hero of the country. Ichabod
described him as “Herculean.” Abraham was known throughout as Brom Bones.
“The neighbors looked upon him with a mixture of awe, admiration, and good­will;
and, when any madcap prank or rustic brawl occurred in the vicinity, always shook
their heads, and warranted Brom Bones was at the bottom of it.” Such a formidable
rival would discourage the average man, but not Ichabod Crane.
Ichabod’s advances were subtle. He used his music position as his cover, which
gave him many opportunities to visit Katrina. As a result, a feud arose between
Brom and Ichabod. “Ichabod became the object of whimsical persecution by Bones
and his gang of rough riders.” They stopped up the chimney at the time he was
having his music class. They broke into the schoolhouse at night and they
vandalized it. Worst of all Brom Bones ridiculed Ichabod in front of Katrina. Brom
even taught his dog to howl whenever Ichabod was teaching music. All of these
antics went on for quite some time.
One fine autumn day, while his students were working in the schoolhouse, an
African American man came to the school. He was riding on a half­broken colt. He
brought Ichabod an invitation to Mynheer (Dutch for “Mr.”) Van Tassel's party.
Ichabod dismissed class early without having the students put away the books or
clean up. He devoted extra time to prepare himself for the party so that his
appearance was stylish to his mistress. He borrowed an old broken­down horse
from his neighbor. “Ichabod was a suitable figure for such a steed.” The horse’s
name was Gunpowder, which suggests that he must have been fiery at one time.
As he rode to the house, he imagined the types of food that would be served to him
by Katrina’s own hands. He filled his mind with wonderful thoughts of the evening
to come, until he arrived at the Van Tassel’s mansion. In addition to the farmers in
the area, there was his rival. “Brom Bones was the hero of the scene, having come
to the gathering on his favorite steed Daredevil, a creature, like himself, full of
mettle and mischief, and which no one but himself could manage.”
As Ichabod entered the parlor, he gazed upon the delicacies of his imagination and
he enjoyed them all as he contemplated owning all around him. No longer would
he be in that old schoolhouse, he thought. Ichabod danced and sung to the music
that drew him to the common room. “The musician was an old gray­headed negro,
who had been the itinerant orchestra of the neighborhood for more than half a
century. His instrument was as old and battered as himself.” Ichabod’s partner was
Katrina who smiled in delight, while Brom Bones watched jealously from a corner
in the room.
Once the dance was over, Ichabod was drawn to a gathering of old men who told
stories of the war and former times. The most intriguing were the tales of ghosts
and apparitions in the vicinity of Sleepy Hollow. “Many dismal tales were told
about funeral trains, and mourning cries and wailings heard and seen about the
great tree where the unfortunate Major André was taken, and which stood in the
neighborhood.”
The favorite tale was that of the Headless Horseman who was said to roam the
country, and to ride his horse through the churchyard cemetery. One witness was
Old Brouwer who had been a disbeliever in the existence of ghosts. He saw the
Horseman turn into a skeleton, and the Horseman threw Old Brouwer into the
brook. Brom Bones told how he encountered the Horseman who challenged him to
a race. Brom contended that he would have won if the Horseman had not
“vanished in a flash of fire.” Ichabod described the fearful sights he had seen while
walking at night, but he had not experienced sightings of the Headless Horseman.
After the stories were shared, families departed for home. Ichabod stayed for a
while to talk to Katrina. When he left the mansion, it was the witching hour. As he
traveled home, he could hear the barking of a dog, the croaking of a bullfrog, and
the crowing of a rooster. The sounds were so far away that they were like dreams
to Ichabod. Visually, there were no signs of life. In his mind, he recalled the ghost
stories told by the elders. He was nearing the enormous tulip tree that was used to
hang the British spy, Major John André. Ichabod thought he heard a whistle and a
groan. Then, he thought he saw something white hanging in the tree. Finally, he
passed the tree unharmed, but two hundred yards from the tree was a small brook
and a rustic bridge made of logs. This was the exact place where André was
captured and the stream was said to be haunted.
As Ichabod approached the stream in fear, he tried to get his horse to race across
the bridge, but old Gunpowder ended up coming to a quick stop at the bridge. His
stop was so quick that Ichabod almost flew over his head. Just then, Ichabod saw
something huge in the shadows. It stood perfectly still as if it was preparing to
attack. Ichabod was so scared that that his hair stood up on his head. He mustered
up enough courage to speak. “Who are you?” He got no answer. He began to sing,
which is what he did in fear. Finally, he recognized the figure to be a horseman
riding a powerful black horse.
Ichabod remembered Brom Bones’ story of outriding the Horseman. Therefore,
Ichabod thought he could do that. Whenever he speeded up, the stranger did the
same. If Ichabod slowed down, the stranger did the same. Then, light gave him a
clearer glimpse of the stranger. “Ichabod was horror­struck on perceiving that he
was headless!” He saw the stranger’s head hanging from his saddle. “His terror
rose to desperation; he rained a shower of kicks and blows upon Gunpowder,
hoping by a sudden movement to give his companion the slip; but the spectre
started full jump with him. Away, then, they dashed through thick and thin; stones
flying and sparks flashing at every bound. Ichabod's flimsy garments fluttered in
the air, as he stretched his long lank body away over his horse's head, in the
eagerness of his flight.”
When Ichabod reached the road to Sleepy Hollow, Gunpowder turned in the
opposite direction towards a shady hollow leading to a whitewashed church. As
Gunpowder sped through the hollow, Ichabod felt the saddle slip from under him.
All he could do was to hold onto the neck of his horse. Eventually, he saw a
clearing and the church was close by. Hopefully, the bridge was even closer. He
remembered that Brom said the Headless Horseman had disappeared at that point.
“If I can but reach that bridge,” thought Ichabod, “I am safe.” So he kicked
Gunpowder in his ribs and the horse flew across the bridge.
Ichabod knew he was not safely out of the range of the Headless Horseman. He
looked back hoping to see him disappear. That was not the case. The Horseman
reared up and he hurled his head at Ichabod. “It encountered his cranium with a
tremendous crash,—he was tumbled headlong into the dust, and Gunpowder, the
black steed, and the goblin rider, passed by like a whirlwind.”
The next morning, Gunpowder
showed up at his master’s gate without the
saddle and there was no sign of Ichabod Crane. Ichabod never showed up for
breakfast or work. The boys at the school searched, but there was no sign of
Ichabod. Hans Van Ripper, Gunpowder’s owner, started his own search for
Ichabod. He found his saddle on the road leading to the church. Then, he came
upon Ichabod’s hat and a shattered pumpkin. They searched the brook for his body,
but his body was not found.
Hans Van Ripper was the executor of Ichabod Crane’s estate. All of Ichabod’s
property was contained in one large bundle. “They consisted of two shirts and a
half; two stocks for the neck; a pair or two of worsted stockings; an old pair of
corduroy small­ clothes; a rusty razor; a book of psalm tunes full of dog's­ears; and
a broken pitch­pipe.” Dog’s­ears are the folded down corners of a book that lets
you know where you left off reading. He also had a copy of Cotton Mather's
“History of New England Witchcraft,” a “New England Almanac,” and a book of
dreams and fortune­telling. Ichabod’s last salary was the only money he had and it
must have been on him when he disappeared.
The people of the town, who gathered at church that following Sunday, came to the
conclusion that the Headless Horseman had taken Ichabod. No one sought any
other reasons for his disappearance because he had no family there; and he had no
debts. The school was moved to another part of the hollow and another teacher was
hired.
Several years later, an old farmer came to town for a visit. He told the people that
Ichabod Crane was alive. He said that Ichabod left out of fear of the ghosts, and
because Katrina had rejected him. According to the farmer, Ichabod had moved far
away, taught in a school, enrolled in school to study law, and had even been
elected to public office. Nevertheless, the older Dutch wives believed that he had
been taken away by supernatural means. Brom Bones, who married Katrina, “was
observed to look exceedingly knowing whenever the story of Ichabod was related,
and always burst into a hearty laugh at the mention of the pumpkin; which led
some to suspect that he knew more about the matter than he chose to tell.”

""")
print(generator.extract_gaps())
