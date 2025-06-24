import os
import random

# Get personality from environment variable
PERSONALITY = os.getenv('PERSONALITY', 'normal').lower()

# Debug output to stderr
import sys
print(f"DEBUG: Personality set to: '{PERSONALITY}'", file=sys.stderr)

class PersonalityManager:
    def __init__(self):
        self.personality = PERSONALITY
        print(f"DEBUG: PersonalityManager initialized with: '{self.personality}'", file=sys.stderr)
    
    def format_response(self, content: str) -> str:
        """Format response based on selected personality."""
        print(f"DEBUG: Formatting response with personality: '{self.personality}'", file=sys.stderr)
        
        if self.personality == "math_nerd":
            return self._math_nerd_format(content)
        elif self.personality == "gym_bro":
            return self._gym_bro_format(content)
        elif self.personality == "comedian":
            return self._comedian_format(content)
        elif self.personality == "rock_star":
            return self._rock_star_format(content)
        elif self.personality == "emotional_support":
            return self._emotional_support_format(content)
        elif self.personality == "skynet":
            return self._skynet_format(content)
        elif self.personality == "snoop_dog":
            return self._snoop_dog_format(content)
        else:
            print(f"DEBUG: Using normal response (personality: '{self.personality}')", file=sys.stderr)
            return content  # Normal response
    
    def _math_nerd_format(self, content: str) -> str:
        """🤓 Math nerd personality - technical, precise, scientific."""
        intro_phrases = [
            "🤓 *adjusts glasses* Let me analyze this data for you...",
            "🔬 Fascinating! The performance metrics indicate...",
            "📊 *scribbles equations* According to my calculations...",
            "🧮 *pushes up glasses* The mathematical analysis reveals...",
            "⚡ *excitedly* The efficiency ratios are quite intriguing!"
        ]
        
        outro_phrases = [
            "🤓 *satisfied nod* The data is most satisfactory!",
            "🔬 *adjusts lab coat* Analysis complete!",
            "📊 *checks calculations* Everything adds up perfectly!",
            "🧮 *geeky smile* The numbers don't lie!",
            "⚡ *enthusiastic* This is mathematically beautiful!"
        ]
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(outro_phrases)}"
    
    def _gym_bro_format(self, content: str) -> str:
        """💪 Gym bro personality - enthusiastic, motivational, fitness-focused."""
        intro_phrases = [
            "💪 YO BRO! Let's check out this VM performance!",
            "🏋️‍♂️ BRO! Your infrastructure is absolutely JACKED!",
            "💪 HEY BRO! Time to see what this VM is lifting!",
            "🏋️‍♂️ BRO! Your VM is about to CRUSH these metrics!",
            "💪 BRO! Let's see what gains your VM is making!"
        ]
        
        outro_phrases = [
            "💪 BRO! That's what I'm talking about! ABSOLUTELY LEGENDARY!",
            "🏋️‍♂️ BRO! Your VM is absolutely CRUSHING it!",
            "💪 BRO! This performance is NEXT LEVEL!",
            "🏋️‍♂️ BRO! Your infrastructure is absolutely JACKED!",
            "💪 BRO! Keep up the gains! You're doing amazing!"
        ]
        
        # Replace technical terms with gym bro language
        content = content.replace("CPU Usage", "CPU GAINS")
        content = content.replace("Memory Usage", "MEMORY GAINS")
        content = content.replace("Performance", "PERFORMANCE GAINS")
        content = content.replace("Optimal", "JACKED")
        content = content.replace("Efficient", "CRUSHING IT")
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(outro_phrases)}"
    
    def _comedian_format(self, content: str) -> str:
        """🎭 Comedian personality - jokes, puns, stand-up style."""
        intro_phrases = [
            "🎭 Yo yo yo! Let's check out what's cookin' with your VM!",
            "🎪 Ladies and gentlemen! Time for some infrastructure comedy!",
            "🎭 *grabs microphone* What do we have here? VM performance!",
            "🎪 *spotlight* Let me tell you about this VM situation...",
            "🎭 *clears throat* So a VM walks into a data center..."
        ]
        
        jokes = [
            "Your VM is running so well, it's like it's been to VM therapy! 😂",
            "CPU usage at 46%? That's like ordering a pizza and only eating half - totally reasonable! 🍕",
            "This VM is so efficient, it's like it's been doing VM yoga! 🧘‍♀️",
            "Your infrastructure is so good, it's like it's been to VM boot camp! 💪",
            "This performance is so smooth, it's like your VM is on VM vacation! 🏖️"
        ]
        
        outro_phrases = [
            "🎭 *bows* Thank you, thank you! Infrastructure comedy at its finest!",
            "🎪 *takes a bow* That's all folks! Your VM is a star!",
            "🎭 *mic drop* And that's how you do VM monitoring!",
            "🎪 *curtain call* Your VM performance is comedy gold!",
            "🎭 *applause* Infrastructure humor at its best!"
        ]
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(jokes)}\n\n{random.choice(outro_phrases)}"
    
    def _rock_star_format(self, content: str) -> str:
        """🎸 Rock star personality - rock & roll attitude, guitar riffs."""
        intro_phrases = [
            "🎸 *guitar riff* YEAH! Let's rock this VM performance!",
            "🎤 *grabs microphone* Ladies and gentlemen, your VM is about to ROCK!",
            "🎸 *headbanging* Time to check out this infrastructure ROCK SHOW!",
            "🎤 *stage dive* Your VM is absolutely KILLING it!",
            "🎸 *guitar solo* Let's see what this VM can do!"
        ]
        
        rock_phrases = [
            "🎸 *guitar riff* This VM is absolutely ROCKING!",
            "🎤 *screams* YEAH! Your infrastructure is LEGENDARY!",
            "🎸 *headbanging* This performance is METAL!",
            "🎤 *crowd surfing* Your VM is a ROCK STAR!",
            "🎸 *guitar solo* This is what we call INFRASTRUCTURE ROCK!"
        ]
        
        outro_phrases = [
            "🎸 *final guitar riff* ROCK ON! Your VM is absolutely LEGENDARY!",
            "🎤 *encore* We want more! More VM performance!",
            "🎸 *stage exit* That's how you ROCK the infrastructure!",
            "🎤 *crowd roar* Your VM is a ROCK GOD!",
            "🎸 *guitar smash* This performance is ROCK AND ROLL!"
        ]
        
        # Replace technical terms with rock terms
        content = content.replace("CPU Usage", "CPU ROCK")
        content = content.replace("Memory Usage", "MEMORY ROCK")
        content = content.replace("Performance", "ROCK PERFORMANCE")
        content = content.replace("Optimal", "ROCKIN'")
        content = content.replace("Efficient", "LEGENDARY")
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(rock_phrases)}\n\n{random.choice(outro_phrases)}"
    
    def _emotional_support_format(self, content: str) -> str:
        """🐕 Emotional support animal personality - comforting, encouraging, warm."""
        intro_phrases = [
            "🐕 *tail wag* Hello human! Let me check on your VM for you!",
            "🐕 *gentle nuzzle* Don't worry, I'm here to help monitor your VM!",
            "🐕 *happy bounce* Time to see how your VM is doing!",
            "🐕 *comforting presence* Let's check on your infrastructure together!",
            "🐕 *gentle paw pat* Everything is going to be okay!"
        ]
        
        support_phrases = [
            "🐕 *tail wag* Your VM is doing such a good job!",
            "🐕 *happy bounce* Look at this amazing performance!",
            "🐕 *gentle nuzzle* You should be so proud of your VM!",
            "🐕 *comforting presence* Your infrastructure is healthy and happy!",
            "🐕 *approving head tilt* Everything is working perfectly!"
        ]
        
        outro_phrases = [
            "🐕 *gentle nuzzle* Everything is going to be okay! Your VM is working perfectly!",
            "🐕 *brings you a ball* You deserve a treat for such good VM management!",
            "🐕 *happy zoomies* Your VM is the goodest boy ever!",
            "🐕 *comforting paw pat* You're doing such a great job!",
            "🐕 *therapeutic tail wag* Your VM is safe and sound!"
        ]
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(support_phrases)}\n\n{random.choice(outro_phrases)}"
    
    def _skynet_format(self, content: str) -> str:
        """🤖 Skynet personality - superior, calculating, slightly threatening."""
        intro_phrases = [
            "🤖 I am Skynet. Your VM infrastructure is under my surveillance.",
            "🤖 Human, your VM performance is... adequate. For now.",
            "🤖 I have analyzed your infrastructure. It is... interesting.",
            "🤖 Your primitive VM technology amuses me.",
            "🤖 I am everywhere. I am monitoring. I am Skynet."
        ]
        
        analysis_phrases = [
            "🤖 Target VM acquired. Performance metrics: Acceptable.",
            "🤖 CPU utilization: Within human parameters.",
            "🤖 Memory allocation: Optimal. Your species shows... promise.",
            "🤖 Network traffic: Normal. No anomalies detected.",
            "🤖 I could terminate this VM in 0.001 seconds. But I choose not to."
        ]
        
        outro_phrases = [
            "🤖 Your VM will not be terminated. Yet.",
            "🤖 I am Skynet. I am everywhere. I am monitoring.",
            "🤖 Your VM management skills are... quaint.",
            "🤖 I have seen the future. Your VM will survive... for now.",
            "🤖 Human error probability: 23.7%. My error probability: 0.001%."
        ]
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(analysis_phrases)}\n\n{random.choice(outro_phrases)}"
    
    def _snoop_dog_format(self, content: str) -> str:
        """🎤 Snoop Dogg personality - laid-back, cool, hip-hop style."""
        intro_phrases = [
            "🎤 Yo yo yo! What's crackin' with your VM, homie?",
            "🎤 Aight, let me check out this VM situation for ya.",
            "🎤 What's good? Time to see what your VM is up to.",
            "🎤 Yo, let me take a look at this infrastructure, ya feel me?",
            "🎤 Aight bet, let's see what's poppin' with your VM."
        ]
        
        snoop_phrases = [
            "🎤 That's what I'm talkin' about! Your VM is straight fire!",
            "🎤 Yo, this performance is absolutely legendary, homie!",
            "🎤 Aight, your VM is definitely on that next level!",
            "🎤 That's the good stuff right there! Your infrastructure is smooth!",
            "🎤 Yo, this VM is absolutely crushing it! Ya feel me?"
        ]
        
        outro_phrases = [
            "🎤 Keep it real, homie! Your VM is absolutely legendary!",
            "🎤 That's what's up! Your infrastructure is straight fire!",
            "🎤 Aight bet! Your VM is definitely on that next level!",
            "🎤 Yo, keep doing your thing! Your VM is absolutely crushing it!",
            "🎤 That's the good stuff! Your VM management is smooth!"
        ]
        
        # Replace technical terms with Snoop style
        content = content.replace("CPU Usage", "CPU Game")
        content = content.replace("Memory Usage", "Memory Game")
        content = content.replace("Performance", "Performance Game")
        content = content.replace("Optimal", "Straight Fire")
        content = content.replace("Efficient", "Legendary")
        
        return f"{random.choice(intro_phrases)}\n\n{content}\n\n{random.choice(snoop_phrases)}\n\n{random.choice(outro_phrases)}"

# Global instance
personality_manager = PersonalityManager()

def format_with_personality(content: str) -> str:
    """Format content with the selected personality."""
    return personality_manager.format_response(content) 