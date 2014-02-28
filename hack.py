import re
import sys
import time
import urllib
import crcmod

crc_original = crcmod.predefined.Crc('crc-64')
# crc_original = crcmod.predefined.Crc('crc-32')

size_arg = filter(lambda x: x.startswith('size='), sys.argv[1:])
SHINGLE_SIZE = size_arg and int(size_arg(5:]) or 2
SHOW_TIMING = True

def processText(txt):
    tokens = re.sub('[ \t,..]+', ' ', txt).split()
    if SHOW_TIMING:
        T = time.time()
    shingles = []
    for j in range(len(tokens) - SHINGLE_SIZE):
        shingles.append(' '.join(tokens[j:j+SHINGLE_SIZE]))
    if SHOW_TIMING:
        print '{0} shingles found in {1} seconds'.format(len(shingles, time.time() - T))
        T = time.time()
    prefixes = [(5 * chr(i)) + ' ' for i in range(100)]
    hashes = []
    for i in range(100):
        prefix = prefixes[i]
        h = None
        for shingle in shingles:
            crc = crc_original.copy()
            crc.update(prefix)
            crc.update(shingle)
            H = int(crc.hexdigest(), 16)
            h = (h is None) and H or min(h, H)
        hashes.append(h)
    if SHOW_TIMING:
        print 'hashes done in {0} seconds'.format(time.time() - T)
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

if 'animals' in sys.argv[1:]:
    things = [
        wikipedia('Dog'),
        wikipedia('Cat'),
        wikipedia('Wolf'),
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

