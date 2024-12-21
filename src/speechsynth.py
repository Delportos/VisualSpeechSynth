import numpy as np
from scipy import signal
import sounddevice as sd

class SimpleSpeechSynth:
    def __init__(self):
        self.sample_rate = 11100 #normal sample rate for standard audio
    
    def makeSound(self,duration,pitch,formants):
        #time array
        t = np.linspace(0,duration,int(self.sample_rate*duration))
        
        attackTime = 0.02
        releaseTime = 0.02
        envelope = np.ones_like(t)
        attack_samples = int(attackTime * self.sample_rate)
        release_samples = int(releaseTime * self.sample_rate)

        envelope[:attack_samples] = np.sin(np.linspace(0,np.pi/2,attack_samples)) ** 2
        envelope[-release_samples:] = np.sin(np.linspace(np.pi/2,0,release_samples)) ** 2

        #base voice with sawtooth wave
        voice = signal.sawtooth(2 * np.pi * pitch * t) + (signal.square(2 * np.pi * pitch * t))
        voice = voice * envelope

        #alter the sound with formants
        sound = voice.copy()
        #bandpass filter to amplify our formant bands
        for formant in formants:
            b,a = signal.butter(2,
                                [max((formant - 100) / (self.sample_rate / 2),0.01),
                                 min((formant + 100) / (self.sample_rate / 2), 0.99)],
                                 btype = 'band')
            #applies filter
            sound = signal.lfilter(b,a,sound)
        
        #normalizes audio by dividing by abs max (all vals now fall between 1 and -1)
        sound = sound / np.max(np.abs(sound))

        return sound

    def makeSoundSequence(self, sounds, durations, vibrato_marks, pitch_changes, basePitch = 120):
        '''
        Create a sequence of sounds as one continuous word
        sounds: list of formant sets to use
        duratiosn: list of durations for each sound
        vibrato_marks: list of bools indicating which sounds should have vibrato
        pitch_changes: list of semitone changes ( +1,-1,0) for each sound
        basePitch: starting pitch before modificaitons
        '''
        #Create all the raw sounds without envelopes
        raw_samples = []
        def get_modified_pitch(semitones, base):
            return base * (2 ** (semitones/12))
        

        vibrato_rate = 5.5
        vibrato_depth = 3
        vibrato_onset = 0.1

        for formants,duration, use_vibrato, pitch_change in zip(sounds,durations,
                                        vibrato_marks,pitch_changes):
            #calculate samples for this sound
            t = np.linspace(0,duration,int(self.sample_rate * duration))

            current_pitch = get_modified_pitch(pitch_change, basePitch)

            if use_vibrato:
                #ccreate a gradial onset for the vibrato
                vibrato_envelope = 1 - np.exp(-t / vibrato_onset)
                #more gentle pitch modulation
                vibrato = current_pitch + (vibrato_depth * vibrato_envelope *
                                 np.sin(2 * np.pi * vibrato_rate * t))
                voice = signal.sawtooth(2 * np.pi * vibrato * t)
            else:
                #regular w/o vibrato
                voice = signal.sawtooth(2 * np.pi * current_pitch * t)


            #apply formant filters
            sound = voice.copy()
            for formant in formants:
                b,a = signal.butter(2,
                                    [max((formant - 1) / (self.sample_rate / 2), 0.01 ),
                                     min((formant + 100) / (self.sample_rate / 2), 0.99)],
                                     btype='band')
                sound = signal.lfilter(b,a,sound)
            raw_samples.append(sound)

        #combine all generated sounds into one continuous array
        fullWord = np.concatenate(raw_samples)

        #create one envelope for the whole word
        total_duration = len(fullWord) / self.sample_rate
        t = np.linspace(0, total_duration, len(fullWord))
        envelope = np.ones_like(t)

        attack_samples = int(0.02 * self.sample_rate) #20ms attack
        release_samples = int(0.02 * self.sample_rate) #20ms release
        envelope[:attack_samples] = np.sin(np.linspace(0, np.pi/2, attack_samples)) ** 2
        envelope[-release_samples:] = np.sin(np.linspace(np.pi/2, 0, release_samples)) ** 2

        #apply the envelope to word
        fullWord = fullWord * envelope

        fullWord = fullWord / (np.max(np.abs(fullWord)))

        return fullWord



    #plays the sound
    def playSound(self, sound):
        sd.play(sound, self.sample_rate)
        sd.wait()


vowels = {
    'ah': [600,1100,2590],
    'ee': [290, 2250, 2800],
    'eh': [400,1700,2600],
    'oh': [400,800,2600],
    'u': [440, 900, 2338.8],
    'm': [163.8,1382.3,2365.1],
    'l': [163.8,900,2365.1],
    'd': [312, 1100, 2860],
    't': [300, 500,4330]
    #'r': [312.8,1134.5,1420.2]
}