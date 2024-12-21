import sys
import os
from speechsynth import SimpleSpeechSynth
import pygame
import numpy as np
from speechsynth import vowels
import sounddevice as sd

class VisualSpeechSynth(SimpleSpeechSynth):
    def __init__(self):
        super().__init__()

        # Pygame visual display
        pygame.init()
        self.screen_width = 400
        self.screen_height = 400
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Talking Synthesizer")

        # Define colors
        self.background_color = (240, 240, 255)  # light blue-grey
        self.mouth_color = (50, 50, 50)  # dark grey
        
        # Initial screen setup
        self.screen.fill(self.background_color)
        pygame.display.flip()

    def draw_mouth(self, width, height):
        # Fill the background
        self.screen.fill(self.background_color)

        # Calculate center of screen
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Draw the mouth as an ellipse
        pygame.draw.ellipse(self.screen, 
                          self.mouth_color,
                          (center_x - width//2, center_y - height//2, width, height))

        # Update the display
        pygame.display.flip()

    def process_word(self, word):
        # Initialize lists for the word
        word_formants = []
        word_durations = []
        word_vibrato = []
        word_pitch = []
        pitchmod = 0
        duration = 0.3
        vibrato = False

        # Process each character
        for char in word:
            # Handle modifiers
            if char == '~':
                vibrato = True
            elif char == '_':
                vibrato = False
            elif char == '+':
                pitchmod += 1
            elif char == '-':
                pitchmod -= 1
            elif char == '|':
                sd.sleep(250)
            elif char == '/':
                sd.sleep(200)
            elif char == '>':
                duration -= 0.05
            elif char == '<':
                duration += 0.05
            else:
                # Process sounds and collect parameters
                if char == 'i':
                    word_formants.append(vowels['ee'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(70, 20)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                elif char == 'a':
                    word_formants.append(vowels['ah'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(60, 40)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                elif char == 'e':
                    word_formants.append(vowels['eh'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(50, 30)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                elif char == 'o':
                    word_formants.append(vowels['oh'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(30, 30)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                elif char == 'u':
                    word_formants.append(vowels['u'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(20, 20)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                #'consonants'
                elif char == 'm':
                    word_formants.append(vowels['m'])
                    word_durations.append(duration)
                    word_vibrato.append(vibrato)
                    word_pitch.append(pitchmod)
                    self.draw_mouth(40, 5)
                    pygame.time.wait(int(duration * 500))  # Convert to milliseconds
                
        # Generate and play the complete word
        if word_formants:
            sound = self.makeSoundSequence(word_formants, word_durations, 
                                         word_vibrato, word_pitch)
            self.playSound(sound)

# Main loop
if __name__ == "__main__":
    synth = VisualSpeechSynth()

    print("Visual Speech Synthesizer")
    print("Enter text to speak (or 'quit' to exit)")

    while True:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get input and process it
        writing = input("Enter sounds: ")
        if writing.lower() == 'quit':
            break

        # Process each word in the input
        words = writing.split()
        for word in words:
            synth.process_word(word)
            sd.sleep(100)  # Pause between words

    # Cleanup
    pygame.quit()