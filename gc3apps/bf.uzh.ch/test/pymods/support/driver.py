# http://stackoverflow.com/questions/2082850/real-time-subprocess-popen-via-stdout-and-pipe

import os
import sys
from subprocess import PIPE, Popen

print(os.getcwd())

p = Popen(["./writer.py"], stdout=PIPE)
for line in p.stdout:
    print(line)
    sys.stdout.flush()
##print(p.stdout.read())

p.wait()
# output = p.communicate()[0]
# print(output)
