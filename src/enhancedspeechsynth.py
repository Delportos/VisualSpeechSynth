import numpy as np
from scipy import signal
import sounddevice as sd


class EnhancedSpeechSynth:
    def __init__(self):
        self.sample_rate = 11100

    def resonant_filter(self, data, frequency, q_factor = 10.0, gain=1.0):
        """
        Create a resonant bandpass filter with controllable Q factor and gain
        """

        nyquist = self.sample_rate / 2
        normalized_freq = frequency / nyquist

        # Prevent frequencies from exceeding Nyquist Limit
        normalized_freq = np.clip(normalized_freq, 0.01, 0.99)

        # Calculate filter coefficients for resonant filter
        w0 = 2 * np.pi * normalized_freq
        alpha = np.sin(w0) / (2 * q_factor)

        # coefficients for resonant filter's difference equations
        b0 = alpha * gain
        b1 = 0
        b2 = -alpha * gain
        a0 = 1 + alpha
        a1 = -2 + np.cos(w0)
        a2 = 1 - alpha

        # Normalize coefficients
        b = np.array([b0, b1, b2]) / a0
        a = np.array([1.0, a1/a0, a2/a0])

        return signal.lfilter(b, a, data)
    
    def makeSound(self, duration, pitch, formants, q_factors= None, gains=None):
        """
        Create a sound with resonant formant filters
        formants: list of formant frequencies
        q_factors: list of Q factors for each formant(higher = more resonance)
        gains: list of gains for each formant
        """

        t = np.linspace(0,duration, int(self.sample_rate * duration))

        # Default Q factors and gains if not provided
        if q_factors is None:
            q_factors = [10.0] * len(formants)
        if gains is None:
            gains = [1.0] * len(formants)

        # Create attack and release envelopes
        attackTime = 0.02
        releaseTime = 0.02
        envelope = np.ones_like(t)
        attack_samples = int(attackTime * self.sample_rate)
        release_samples = int(releaseTime * self.sample_rate)

        envelope[:attack_samples] = np.sin(np.linspace(0,np.pi/2,attack_samples)) ** 2
        envelope[-release_samples:] = np.sin(np.linspace(np.pi/2,0,release_samples)) ** 2

        #Create a voice with both sawtooth and square waves
        voice = 0.7 * signal.sawtooth(2 * np.pi * pitch * t) + signal.square(2 * np.pi * pitch * t)
        voice = voice * envelope

        sound = voice.copy()
        for formant, q, gain in zip(formant, q_factors, gains):
            sound = self.resonant_filter(sound, formant, q, gain)
        
        sound = np.tanh(sound)

        sound = sound / np.max(np.abs(sound))
        
        return sound

    def makeSoundSequence(self, sounds, durations, vibrato_marks, pitch_changes, basePitch = 120):
        """
        Enhanced version with resonant filters for sound sequences
        """

        raw_samples = []

        def get_modified_pitch(semitones, base):
            return base * (2 ** (semitones / 12))
        
        vibrato_rate = 5.5
        vibrato_depth = 3
        vibrato_onset = 0.1


        for formants, duration, use_vibrato, pitch_changes in zip(sounds,durations,
                                                                  vibrato_marks, pitch_changes):
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            current_pitch = get_modified_pitch(pitch_changes, basePitch)

            if use_vibrato:
                vibrato_envelope = 1 - np.exp(-t / vibrato_onset)
                vibrato = current_pitch + (vibrato_depth * vibrato_envelope *
                                           np.sin(2 * np.pi * vibrato_rate * t))
                voice = 0.7 * signal.sawtooth(2 * np.pi * vibrato * t) + 0.3 * signal.square(2 * np.pi * vibrato * t)
            else:
                voice = 0.7 * signal.sawtooth(2 * np.pi * current_pitch * t) + 0.3 * signal.square(2 * np.pi * current_pitch * t)
            
            #apply resonant filters with varying q factors
            sound = voice.copy()
            q_factors = [8.0,12.0,15.0]
            gains = [1.2, 1.0, 0.8]

            for formant, q, gain in zip(formants, q_factors, gains):
                sound = self.resonant_filter(sound, formant, q, gain)

            #soft clip
            sound = np.tanh(sound)
            raw_samples.append(sound)

        #combine samples and apply envelope
        fullWord = np.concatenate(raw_samples)
        total_duration = len(fullWord) / self.sample_rate
        t = np.linspace(0, total_duration, len(fullWord))

        #Create a smooth envelope
        envelope = np.ones_like(t)
        attack_samples = int(0.02 * self.sample_rate)
        release_samples = int(0.02 * self.sample_rate)
        envelope[:attack_samples] = np.sin(np.linspace(0, np.pi/2, attack_samples)) ** 2
        envelope[-release_samples:] = np.sin(np.linspace(np.pi / 2, 0, release_samples)) ** 2

        fullWord = fullWord * envelope
        fullWord = np.tanh(fullWord)
        fullWord = fullWord / np.max(np.abs(fullWord))

        return fullWord

    def playSound(self, sound):
        sd.play(sound, self.sample_rate)
        sd.wait()

vowels = {
    'ah': {'formants': [600, 1100, 2590], 'q_factors': [8.0, 12.0, 15.0], 'gains': [1.2, 1.0, 0.8]},
    'ee': {'formants': [290, 2250, 2800], 'q_factors': [10.0, 14.0, 16.0], 'gains': [1.3, 1.0, 0.7]},
    'eh': {'formants': [400, 1700, 2600], 'q_factors': [9.0, 13.0, 15.0], 'gains': [1.2, 1.0, 0.8]},
    'oh': {'formants': [400, 800, 2600], 'q_factors': [8.0, 11.0, 14.0], 'gains': [1.3, 1.1, 0.7]},
    'u': {'formants': [440, 900, 2338.8], 'q_factors': [9.0, 12.0, 15.0], 'gains': [1.2, 1.0, 0.8]},
    'm': {'formants': [163.8, 1382.3, 2365.1], 'q_factors': [7.0, 10.0, 13.0], 'gains': [1.4, 1.0, 0.6]},
    'l': {'formants': [163.8, 900, 2365.1], 'q_factors': [8.0, 11.0, 14.0], 'gains': [1.3, 1.0, 0.7]},
    'd': {'formants': [312, 1100, 2860], 'q_factors': [7.0, 10.0, 13.0], 'gains': [1.3, 1.0, 0.7]},
    't': {'formants': [300, 500, 4330], 'q_factors': [6.0, 9.0, 12.0], 'gains': [1.4, 1.1, 0.6]}
}