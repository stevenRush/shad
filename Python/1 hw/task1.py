__author__ = 'Evgeny Eltyshev'
from string import punctuation
import re
import sys
import random

def words(fileobj):
    r = re.compile(r'[\s{}]+'.format(re.escape(punctuation)))
    for line in fileobj:
        for word in re.findall(r"[\w']+|[.,!?;]", line):
            yield word

if __name__ == "__main__":
    fileobj = open(sys.argv[1])
    for word in words(fileobj):
        if len(word) < 3:
            print word,
            continue
        middle_indexes = range(len(word)-2)
        random.shuffle(middle_indexes)
        letters = [word[0]]
        for index in middle_indexes:
            letters.append(word[index + 1])
        letters.append(word[-1])
        print ''.join(letters),