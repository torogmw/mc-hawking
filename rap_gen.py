import subprocess
from numpy import *
from scipy import *
import wave
import scipy.io.wavfile
import scipy.signal
import random
import pylab
import pdb

'''By Ruofeng Chen, April 2013'''

voices = ["Albert", "Bad News", "Bahh", "Bells", "Boing", "Bubbles", "Cellos", "Deranged", "Good News", "Hysterical", "Pipe Organ", "Trinoids", "Whisper", "Zarvox"]

pulses = {}
pulses[1] = [0]
pulses[2] = [0, 4]
pulses[3] = [0, 4, 8]
pulses[4] = [12, 16, 20, 24]
pulses[5] = [8, 12, 16, 20, 24]
pulses[6] = [6, 8, 12, 16, 20, 24]
pulses[7] = [6, 8, 10, 12, 22, 24, 28]
pulses[8] = [6, 8, 10, 12, 22, 24, 26, 28]
pulses[9] = [6, 8, 10, 12, 16, 20, 24, 26, 28]
pulses[10] = [4, 6, 8, 10, 12, 16, 20, 24, 26, 28]
pulses[11] = [4, 6, 8, 10, 12, 16, 18, 20, 24, 26, 28]
pulses[12] = [4, 6, 8, 10, 12, 16, 18, 20, 22, 24, 26, 28]
pulses[13] = [2, 4, 6, 8, 10, 12, 16, 18, 20, 22, 24, 26, 28]
pulses[14] = [0, 2, 4, 6, 8, 10, 12, 16, 18, 20, 22, 24, 26, 28]
pulses[15] = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
pulses[16] = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

# ratios = [1, 1.1, 1.2, 1.1, 1, 1.1, 1.2, 1.1, 1, 1.1, 1.2, 1.1, 1, 1.1, 1.2, 1.1]

synth_path = "./synth"
rap_path = "./rap"

def time_stretch_half(dafxin):
    ''''''
    hopsize = 480 # sounds good using this parameter
    framesize = 2 * hopsize
    hannWin = hanning(framesize)
    framenum = dafxin.size / hopsize - 1
    dafxout = zeros(hopsize*(framenum/2)+framesize)
    for n in range(framenum):
        if n % 2 == 0:
            dafxout[n/2*hopsize:n/2*hopsize+framesize] = dafxout[n/2*hopsize:n/2*hopsize+framesize] + dafxin[n*hopsize:n*hopsize+framesize] * hannWin
    return dafxout

def synth(words, voice="Fred"):
    print words
    for word in words:
        fullcmd = ['say', '-v', voice, '-o', synth_path+'/'+str(hash(word))+'.wav', '--data-format=LEI16@44100', word]
        subprocess.check_output(fullcmd)

def align_to_beats(everything):
    ''' YO YO '''
    tempo = 140
    intvl = 0.25 / (tempo / 60.) * 44100.
    total_len = 8 / (tempo / 60.) * 44100.

    data_list = []
    for tup in everything:
        for i in range(len(tup[1])):
            data_list.append(tup[0][tup[1][i]:tup[2][i]])

    fs, rapdata = scipy.io.wavfile.read(open('drum_1bar.wav', 'r'))
    rapdata = float32(rapdata / float(2**16))
    rapdata = mean(rapdata, 1)
    rapdata = rapdata * 0.2
    # rapdata = zeros(total_len * 1.5) # if you don't want accompaniment
    
    total_voice_len = sum([data.size for data in data_list])
    syllable_num = len(data_list)
    if syllable_num > 16:
        syllable_num = 16

    # this will result in overlapping words
    pulse = pulses[syllable_num]
    for s in range(syllable_num):
        start = pulse[s] * intvl
        if s < syllable_num - 1 and data_list[s].size > 1.5 * (pulse[s+1] - pulse[s]) * intvl:
            data_list[s] = time_stretch_half(data_list[s])

        if s == 0:
            rapdata[start:start+data_list[s].size] = rapdata[start:start+data_list[s].size] + data_list[s] * 2.
        elif pulse[s] % 4 == 0:
            rapdata[start:start+data_list[s].size] = rapdata[start:start+data_list[s].size] + data_list[s] * 1.2
        else:
            rapdata[start:start+data_list[s].size] = rapdata[start:start+data_list[s].size] + data_list[s]

        # pylab.plot(rapdata)
        # pylab.show()

    # delete the tailing zeros
    first_zero = rapdata.size-1
    while rapdata[first_zero] == 0:
        first_zero = first_zero - 1
    rapdata = rapdata[0:first_zero]

    # delete the heading few samples
    rapdata = rapdata[0.2*44100:-1]

    rapdata = rapdata / max(abs(rapdata)) * 0.4
    rapdata = array(rapdata * float(2**16), dtype=int16)
    return rapdata

def find_onsets_and_offsets(data):
    th = 0
    hopsize = 512
    framenum = data.size / hopsize

    # find all onsets
    energy0 = 0
    onsets = []
    offsets = []
    for n in range(framenum):
        energy1 = sum(data[n*hopsize:(n+1)*hopsize] ** 2) / hopsize
        if energy0 <= th and energy1 > th:
            ind = n*hopsize
            onsets.append(ind)
            # from this onset on, find its corresponding offset
            n2 = n
            energy2 = energy1
            while (n2+1)*hopsize <= data.size and energy2 > th:
                energy2 = sum(data[n2*hopsize:(n2+1)*hopsize] ** 2) / hopsize
                n2 = n2 + 1
            if (n2+1)*hopsize > data.size:
                offsets.append(data.size-1)
            else:
                offsets.append(n2*hopsize)
        energy0 = energy1

    if len(onsets) != len(offsets):
        print "Big problem!!! Onsets != Offsets"
    # for all words that are too short, merge them with the shorter neighbor
    if len(onsets) > 1:
        while True:
            short_count = 0
            for i in range(len(onsets)):
                if offsets[i] - onsets[i] < 44100 * 0.2:
                    short_count = short_count + 1
            if short_count == 0:
                break
            for i in range(len(onsets)):
                if offsets[i] - onsets[i] < 44100 * 0.2:
                    if i >= 1 and i <= len(onsets)-2:
                        if offsets[i-1] - onsets[i-1] < offsets[i+1] - onsets[i+1]:
                            onsets.pop(i)
                            offsets.pop(i-1)
                        else:
                            onsets.pop(i+1)
                            offsets.pop(i)
                    elif i == 0:
                        onsets.pop(i+1)
                        offsets.pop(i)
                    else:
                        onsets.pop(i)
                        offsets.pop(i-1)
                    break
    return array(onsets, int), array(offsets, int)

def from_text_to_wavfile(sentence):
    words = sentence.split(" ")
    synth(words)
    everything = []
    for word in words:
        fs, data = scipy.io.wavfile.read(open(synth_path+'/'+str(hash(word))+'.wav', 'r'))
        data = float32(data / float(2**16))
        if fs != 44100:
            print "warning: fs is not 44100!!!!!!"
        onsets, offsets = find_onsets_and_offsets(data)
        everything.append((data, onsets, offsets))
    rapdata = align_to_beats(everything)
    scipy.io.wavfile.write(rap_path+'/'+str(hash(sentence))+'-rap.wav', 44100, rapdata)

if __name__ == '__main__':

    # generate the audio
    sentence = "hello world this is minwei"
    from_text_to_wavfile(sentence)
