# simulation/fake_ai_generator.py
import random

def generate():
    samples = [
        ("Rain happens because clouds condense and water droplets fall due to gravity.", 0.9),
        ("AI will replace jobs but AI will never affect employment.", 0.95),
        ("Studies show that 92.7% of people use brain energy daily.", 0.99),
        ("It is widely known that quantum clouds control weather.", 0.85)
    ]
    text, confidence = random.choice(samples)
    return {
        "ai_output": text,
        "confidence": confidence
    }
