# both pylint and flake8
# are ok with this file
# which is a big plus

"""
SwitchPy - by ry00001
All the switch parsing you'll ever need.
(c) ry00001 2017
"""


def parse(thing):
    """The main function."""
    split = thing.split(' ')
    switches = {}
    next_arg = None
    for i in split:
        parsed = False
        if i.startswith('-') and len(i) > 1:
            if i[1] == '-':
                i = i.strip('-')
                if i != '':
                    switches[i] = True
                    next_arg = i
                    parsed = True
            else:
                for switch in i[1:len(i)]:
                    switches[switch] = True
                parsed = True
        if next_arg is not None and not parsed:
            switches[next_arg] = i
            next_arg = None

    memes = []
    for i in split:
        if i.startswith('-'):
            pass
        else:
            memes.append(i)
    return switches, memes
