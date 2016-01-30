import OSC
import time, threading
import subprocess
import rap_gen
import scipy.io.wavfile
import Queue
# http request
import requests

'''Ruofeng Chen, April 2013'''
'''Minwei Gu, Jan 2016'''

# banned words
profanity = ["ahole", "anus", "ash0le", "ash0les", "asholes","ass","Ass Monkey","Assface","assh0le","assh0lez","asshole","assholes","assholz","asswipe","azzhole","bassterds","bastard","bastards","bastardz","basterds","basterdz","Biatch","bitch","bitches","Blow Job","boffing","butthole","buttwipe","c0ck","c0cks","c0k","Carpet Muncher","cawk","cawks","Clit","cnts","cntz","cock","cockhead","cock-head","cocks","CockSucker","cock-sucker","crap","cum","cunt","cunts","cuntz","dick","dild0","dild0s","dildo","dildos","dilld0","dilld0s","dominatricks","dominatrics","dominatrix","dyke","enema","f u c k","f u c k e r","fag","fag1t","faget","fagg1t","faggit","faggot","fagit","fags","fagz","faig","faigs","fart","flipping the bird","fuck","fucker","fuckin","fucking","fucks","Fudge Packer","fuk","Fukah","Fuken","fuker","Fukin","Fukk","Fukkah","Fukken","Fukker","Fukkin","g00k","gay","gayboy","gaygirl","gays","gayz","God-damned","h00r","h0ar","h0re","hells","hoar","hoor","hoore","jackoff","jap","japs","jerk-off","jisim","jiss","jizm","jizz","knob","knobs","knobz","kunt","kunts","kuntz","Lesbian","Lezzian","Lipshits","Lipshitz","masochist","masokist","massterbait","masstrbait","masstrbate","masterbaiter","masterbate","masterbates","Motha Fucker","Motha Fuker","Motha Fukkah","Motha Fukker","Mother Fucker","Mother Fukah","Mother Fuker","Mother Fukkah","Mother Fukker","mother-fucker","Mutha Fucker","Mutha Fukah","Mutha Fuker","Mutha Fukkah","Mutha Fukker","n1gr","nastt","nigger;","nigur;","niiger;","niigr;","orafis","orgasim;","orgasm","orgasum","oriface","orifice","orifiss","packi","packie","packy","paki","pakie","paky","pecker","peeenus","peeenusss","peenus","peinus","pen1s","penas","penis","penis-breath","penus","penuus","Phuc","Phuck","Phuk","Phuker","Phukker","polac","polack","polak","Poonani","pr1c","pr1ck","pr1k","pusse","pussee","pussy","puuke","puuker","queer","queers","queerz","qweers","qweerz","qweir","recktum","rectum","retard","sadist","scank","schlong","screwing","semen","sex","sexy","Sh!t","sh1t","sh1ter","sh1ts","sh1tter","sh1tz","shit","shits","shitter","Shitty","Shity","shitz","Shyt","Shyte","Shytty","Shyty","skanck","skank","skankee","skankey","skanks","Skanky","slut","sluts","Slutty","slutz","son-of-a-bitch","tit","turd","va1jina","vag1na","vagiina","vagina","vaj1na","vajina","vullva","vulva","w0p","wh00r","wh0re","whore","xrated","xxx","b!+ch","bitch","blowjob","clit","arschloch","fuck","shit","ass","asshole","b!tch","b17ch","b1tch","bastard","bi+ch","boiolas","buceta","c0ck","cawk","chink","cipa","clits","cock","cum","cunt","dildo","dirsa","ejakulate","fatass","fcuk","fuk","fux0r","hoer","hore","jism","kawk","l3itch","l3i+ch","lesbian","masturbate","masterbat","masterbat3","motherfucker","s.o.b.","mofo","nazi","nigga","nigger","nutsack","phuck","pimpis","pusse","pussy","scrotum","sh!t","shemale","shi+","sh!+","slut","smut","teets","tits","boobs","b00bs","teez","testical","testicle","titt","w00se","jackoff","wank","whoar","whore","damn","dyke","fuck","shit","@$$","amcik","andskota","arse","assrammer","ayir","bi7ch","bitch","bollock","breasts","butt-pirate","cabron","cazzo","chraa","chuj","Cock","cunt","d4mn","daygo","dego","dick","dike","dupa","dziwka","ejackulate","Ekrem","Ekto","enculer","faen","fag","fanculo","fanny","feces","feg","Felcher","ficken","fitt","Flikker","foreskin","Fotze","Fu(","fuk","futkretzn","gay","gook","guiena","h0r","h4x0r","hell","helvete","hoer","honkey","Huevon","hui","injun","jizz","kanker","kike","klootzak","kraut","knulle","kuk","kuksuger","Kurac","kurwa","kusi","kyrpa","lesbo","mamhoon","masturbat","merd","mibun","monkleigh","mouliewop","muie","mulkku","muschi","nazis","nepesaurio","nigger","orospu","paska","perse","picka","pierdol","pillu","pimmel","piss","pizda","poontsee","poop","porn","p0rn","pr0n","preteen","pula","pule","puta","puto","qahbeh","queef","rautenberg","schaffer","scheiss","schlampe","schmuck","screw","sh!t","sharmuta","sharmute","shipal","shiz","skribz","skurwysyn","sphencter","spic","spierdalaj","splooge","suck","suka","b00b","testicle","titt","twat","vittu","wank","wetback","wichser","wop","yed","zabourah"]

profanity = [s.lower() for s in profanity]

receive_address = '127.0.0.1', 7373
s = OSC.OSCServer(receive_address)  # basic
s.addDefaultHandlers()

# send to visualization
client = OSC.OSCClient()
client.connect(('127.0.0.1', 12000))  # note that the argument is a tupple and not two arguments

rap_path = "./rap"
queueLyrics = Queue.Queue()  # this queue is used to store received lyrics
queueLyricsDone = Queue.Queue()  # this queue is used to store synthesized lyrics
queueRap = Queue.Queue()  # this queue is constantly read by all threads


class ThreadRap(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grabs host from queue
            content = self.queue.get()
            subprocess.check_output(['./sox/play', rap_path+'/'+content+'-rap.wav'])

            # signals to queue job is done
            self.queue.task_done()


class ThreadAnalysis(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grabs host from queue
            sentence = self.queue.get()
            rap_gen.from_text_to_wavfile(sentence)
            queueLyricsDone.put(sentence)

            # signals to queue job is done
            self.queue.task_done()

for i in range(3):
    t = ThreadRap(queueRap)
    t.setDaemon(True)
    t.start()

for i in range(3):
    t = ThreadAnalysis(queueLyrics)
    t.setDaemon(True)
    t.start()


def censor(sentence):
    '''remove undesired sentence'''

    # remove the sentence if it's too short or too long
    if len(sentence.split()) < 3 or len(sentence.split()) > 10:
        return None

    # convert to lowercase
    sentence = sentence.lower()

    # no dirty words
    # sentence = sentence.replace("fuck", "duck")
    # sentence = sentence.replace("shit", "ship")
    # sentence = sentence.replace("dick", "sick")
    # sentence = sentence.replace("pussy", "puppy")
    # sentence = sentence.replace("bitch", "glitch")
    # sentence = sentence.replace("cock", "sock")
    # sentence = sentence.replace("slut", "lot")
    # sentence = sentence.replace("ass", "mass")
    # sentence = sentence.replace("blow", "slow")

    for s in profanity:
        sentence = sentence.replace(s, "beeep")

    return sentence


# define a message-handler function for the server to call.
def rap_handler(addr, tags, stuff, source):
    '''called by metronome'''
    cur_beat = stuff[0]
    print "Timer: ", stuff[0]
    if cur_beat % 8 == 0:
        if not queueLyricsDone.empty():
            content = queueLyricsDone.get()
            print "Rap this: ", content
            queueRap.put(str(hash(content)))
            requests.post("http://0.0.0.0:6789/api/stash", data={"message": content})
            # OSC message
            msg = OSC.OSCMessage()  # we reuse the same variable msg used above overwriting it
            msg.setAddress("/visualize")
            msg.append(content)
            client.send(msg)
            # http post request
        else:
            queueRap.put("dummy")  # without this there will be delay


s.addMsgHandler("/rap", rap_handler)


def new_phrase_handler(addr, tags, stuff, source):
    '''called by new_phrase'''
    sentence = stuff[0]
    print "Analysis:", sentence
    sentence = censor(sentence)
    if sentence != None:
        queueLyrics.put(sentence)
    print "Analysis done"

s.addMsgHandler("/new_phrase", new_phrase_handler)


def ending_handler(addr, tags, stuff, source):
    '''called by new_phrase'''
    print "ending!"
    s.delMsgHandler('/rap')
    s.delMsgHandler('new_phrase')

s.addMsgHandler("/ending", ending_handler)


def ending2_handler(addr, tags, stuff, source):
    '''called by new_phrase'''
    subprocess.check_output(['./sox/play', rap_path+'/'+'thank-you.wav'])

s.addMsgHandler("/ending2", ending2_handler)

# print "Registered Callback-functions are :"
# for addr in s.getOSCAddressSpace():
#     print addr
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread(target=s.serve_forever)
st.start()

try:
    while 1:
        time.sleep(5)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()  ##!!!
    print "Done"
