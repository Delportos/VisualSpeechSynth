import sys
import os
from speechsynth import SimpleSpeechSynth, vowels
import pygame
import numpy as np
import sounddevice as sd
import threading
import time


class VisualSpeechSynth(SimpleSpeechSynth):
    def __init__(self):
        super().__init__()

        # Pygame visual display
        pygame.init()

        # init fonts
        pygame.font.init()
        self.font = pygame.font.Font(None,36)

        
        self.screen_width = 400
        self.screen_height = 400
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Talking Synthesizer")
        


        #load spritesheet
        spritesheetPath = '/Users/frankgallo/Desktop/Programming/VisualSpeechSynth/sprites/mouthspritesbig.png'
        self.spritesheet = pygame.image.load(spritesheetPath).convert_alpha()

        #define size of each sprite frame
        self.sprite_width = 200
        self.sprite_height = 200

        # text input properties
        self.input_box = pygame.Rect(50, 300, 300, 40)
        self.input_text = ""
        self.input_active = False
        self.text_color = pygame.Color('black')
        self.input_box_color = pygame.Color('lightgray')

        self.mouth_positions = {
            'ah':(0,0),
            'ee':(0,1),
            'eh': (0, 2),
            'oh': (0, 3),
            'u':  (0, 4),
            'm':  (1, 0),
            'l':  (1, 1),
            'd':  (1, 2),
            't':  (1, 3)

        }

        #init with neutral mouth pos
        self.screen.fill((173, 216, 230)) #light blue
        self.draw_mouth('m')
        self.draw_input_box()
        pygame.display.flip()
    
    def draw_input_box(self):
        #drasw the box
        pygame.draw.rect(self.screen, self.input_box_color, self.input_box,2)

        #render the text
        text_surface = self.font.render(self.input_text, True, self.text_color)

        #Ensuer text wont overflow the input box
        width = max(300, text_surface.get_width() + 10)
        self.input_box.w = width

        #center the text vertically and maintain left alignment
        text_y = self.input_box.y + (self.input_box.height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (self.input_box.x + 5, text_y))


    def get_sprite(self,row,col):
            """Extract a single sprite from the spreadsheet/"""

            sprite = pygame.Surface((self.sprite_width,self.sprite_height),pygame.SRCALPHA)

            x = col * self.sprite_width
            y = row * self.sprite_height

            #copy the specific sprite from the spritesheet
            sprite.blit(self.spritesheet,(0,0),(x,y,self.sprite_width,self.sprite_height))

            return sprite

    def draw_mouth(self, sound):
        # Fill the background
        #print("Drawing mouth...")
        self.screen.fill((255,255,255)) #light blue

        #get sprite positon for this sound
        row, col = self.mouth_positions.get(sound, (1,4)) #default to closed mouth sprite

        #get appropriate sprite
        mouth_sprite = self.get_sprite(row, col)

        #calculate position to center the sprite
        sprite_x = (self.screen_width - self.sprite_width) // 2
        sprite_y = (self.screen_height - self.sprite_height) // 2

        #draw sprite to screen
        self.screen.blit(mouth_sprite,(sprite_x,sprite_y))

        # Update the display
        pygame.display.flip()
    
    

    def play_synchronized(self,sound,mouth_positions, durations):
        """
        Play audio and animate mouth in sync using precise timing
        """
        total_duration = sum(durations)
        time_points = np.cumsum([0] + durations[:-1]) #start time for each pos


        #Create animation thread
        def animate():
            start_time = time.time()
            current_pos = 0

            while current_pos < len(mouth_positions):
                current_time = time.time() - start_time

                #Find current mouth positon based on elapsed time
                #if the time has changed, then we update the mouth, and then set cur pos fwd
                while (current_pos < len(time_points) and
                       current_time >= time_points[current_pos]):
                    self.draw_mouth(mouth_positions[current_pos])
                    current_pos += 1

                #small delay to prevent excessive cpu usage
                time.sleep(0.016)

                #check if animation should end
                if current_time >= total_duration:
                    break
            self.draw_mouth('m')


        #Start animation thread
        anim_thread = threading.Thread(target=animate)
        anim_thread.start()

        sd.play(sound, self.sample_rate)
        sd.wait()

        anim_thread.join

    def process_word(self, word):
        # Initialize lists for the word
        word_formants = []
        word_durations = []
        word_vibrato = []
        word_pitch = []
        mouth_positions = [] 

        
        duration = 0.3
        vibrato = False
        pitchmod = 0


        sound_map = {
            'i': ('ee', vowels['ee']),
            'a': ('ah', vowels['ah']),
            'e': ('eh', vowels['eh']),
            'o': ('oh', vowels['oh']),
            'u': ('u', vowels['u']),
            'm': ('m', vowels['m']),
            'l': ('l', vowels['l']),
            'd': ('d', vowels['d']),
            't': ('t', vowels['t']),
        }

        for char in word:
            if char in sound_map:
                pos, formant = sound_map[char]
                word_formants.append(formant)
                word_durations.append(duration)
                word_vibrato.append(vibrato)
                word_pitch.append(pitchmod)
                mouth_positions.append(pos)
            elif char == '~':
                vibrato = True
            elif char == '_':
                vibrato = False
            elif char == '+':
                pitchmod += 1
            elif char == '-':
                pitchmod -= 1
            elif char == ">":
                duration = max(0.1, duration - 0.05)
            elif char == '<':
                duration = min(0.5, duration + 0.05)
            elif char == '|':
                sd.sleep(200)
                time.sleep(0.2)
            elif char == '/':
                sd.sleep(100)
                time.sleep(0.1)

        if word_formants:
            sound = self.makeSoundSequence(word_formants, word_durations, 
                                         word_vibrato, word_pitch)
            self.play_synchronized(sound, mouth_positions, word_durations)
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                        #toggle input box active state
                        if self.input_box.collidepoint(event.pos):
                            self.input_active = True
                            self.input_box_color = pygame.Color('dodgerblue2')
                        else:
                            self.input_active = False
                            self.input_box_color = pygame.Color('white')
                        self.draw_input_box()
                        pygame.display.flip()
                elif event.type == pygame.KEYDOWN:
                    if self.input_active:
                        if event.key == pygame.K_RETURN:
                            #process the input text
                            words = self.input_text.split()
                            for word in words:
                                self.process_word(word)
                                sd.sleep(100) #pause between words
                            self.input_text = " " #clear input after processing
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                            self.input_text = " "
                        else:
                            self.input_text += event.unicode
                        
                        #redraw input box with new text
                        self.draw_input_box()
                        pygame.display.flip()
            # small sleep
            time.sleep(0.016)
        pygame.quit()


# Main loop
if __name__ == "__main__":
    synth = VisualSpeechSynth()
    synth.run()

    """
    ==========================================================
    to run in the terminal instead of in the pygame window
    ==========================================================

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
    """