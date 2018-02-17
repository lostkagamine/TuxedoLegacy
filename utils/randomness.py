import random

def random_colour():
    return random.randint(0x000000, 0xFFFFFF)

def bad_shuffle(s):
    s = s.split(' ')
    return ' '.join([random.choice(s) for i in s])
