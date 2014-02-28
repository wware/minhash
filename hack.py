import re
import sys
import time
import types
import urllib
import crcmod

from math import ceil

# crc_original = crcmod.predefined.Crc('crc-64')
# crc_original = crcmod.predefined.Crc('crc-32')

class RC4Hash:

    def __init__(self):
        self.S = [i for i in range(256)]
        self.j = 0

    def copy(self):
        r = RC4Hash()
        r.S, r.j = self.S[:], self.j
        return r

    def update(self, bytes):
        S, j, N = self.S, self.j, len(bytes)
        longbytes = int(ceil(256.0/N)) * bytes
        i = 0
        while i < 256:
            j = (j + S[i] + longbytes[i]) % 256
            S[i], S[j] = S[j], S[i]
            i += 1
        self.j = j

    def digest(self, n=16):
        S = self.S
        i = j = 0
        result = []
        for k in range(n):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            t = (S[i] + S[j]) % 256
            result.append(S[t])
        return result

    def intdigest(self, n=16):
        result = 0
        for x in self.digest(n):
            result = (result << 8) + x
        return result

    def hexdigest(self, n=16):
        return hex(self.intdigest(n))[2:]

USE_RC4 = True

size_arg = filter(lambda x: x.startswith('size='), sys.argv[1:])
hashes_arg = filter(lambda x: x.startswith('hashes='), sys.argv[1:])

SHINGLE_SIZE = size_arg and int(size_arg[0][5:]) or 2
NUM_HASHES = hashes_arg and int(hashes_arg[0][7:]) or 100
SHOW_TIMING = 'timing' in sys.argv[1:]

def processText(txt):
    tokens = re.sub('[ \t,..]+', ' ', txt).split()
    N = len(tokens)
    if USE_RC4:
        tokens = dict(map(lambda pair: (pair[0], map(ord, pair[1])), enumerate(tokens)))
    else:
        tokens = dict(enumerate(tokens))
    hashes = NUM_HASHES * [1.0e100]
    if SHOW_TIMING:
        print '{0} shingles'.format(N - SHINGLE_SIZE)
        T = time.time()
    for j in range(N - SHINGLE_SIZE):
        for i in range(NUM_HASHES):
            if USE_RC4:
                H = RC4Hash()
                update = H.update
                update(5 * [i % 256])
                for k in range(j, j + SHINGLE_SIZE):
                    update(tokens[k])
                hashes[i] = min(hashes[i], H.intdigest())
            else:
                H = crcmod.predefined.Crc('crc-64')
                update = H.update
                update(5 * chr(i % 256))
                for k in range(j, j + SHINGLE_SIZE):
                    update(tokens[k])
                hashes[i] = min(hashes[i], int(H.hexdigest(), 16))
        if j > 0 and (j % 100) == 0:
            print j, time.time() - T
    if SHOW_TIMING:
        print '{0} seconds for hashing'.format(time.time() - T)
    return hashes

def fetchHtml(url):
    txt = urllib.urlopen(url).read()
    while True:
        try:
            n = txt.index('<script')
            txt, x = txt[:n], txt[n+7:]
        except ValueError:
            break
        n = x.index('</script>')
        txt += x[n+9:]
    return re.sub('<[^>]*>', '', txt)

def wikipedia(term):
    if SHOW_TIMING:
        print term
    url = 'http://en.wikipedia.org/wiki/{0}'.format(re.sub(' ', '_', term))
    return (term, processText(fetchHtml(url)))

def gutenberg(title, number):
    if SHOW_TIMING:
        print title
    url = 'http://www.gutenberg.org/files/{0}/{0}-h/{0}-h.htm'.format(number)
    return (title, processText(fetchHtml(url)))

def hackRelated(proc1, proc2):
    related = reduce(lambda x, y: x + y,
                     map(lambda x, y: x == y and 1 or 0, proc1[1], proc2[1]))
    return (proc1[0], proc2[0], related)

things = []
if 'animals' in sys.argv[1:]:
    things = [
        wikipedia('Dog'),
        wikipedia('Wolf'),
        wikipedia('Cat'),
        wikipedia('Frog'),
        wikipedia('Toad')
    ]
elif 'big' in sys.argv[1:]:
    things = [
        gutenberg('Moby Dick', 2701),
        gutenberg('Pride and Prejudice', 1342),
        gutenberg('Huckleberry Finn', 76),
        gutenberg('Tom Sawyer', 74)
    ]
elif 'small' in sys.argv[1:]:
    things = [
        gutenberg('Huckleberry Finn', 76),
        gutenberg('Tom Sawyer', 74)
    ]

for i in range(len(things)):
    for j in range(i + 1, len(things)):
        print hackRelated(things[i], things[j])

