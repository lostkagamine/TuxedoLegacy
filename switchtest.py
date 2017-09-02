from utils import switches
import sys
print(switches.parse_switches(' '.join(sys.argv[1:len(sys.argv)])))