import csv
import re
import sys
import math
import time
import functools
import ntpath

from collections import defaultdict
from string import lower

class NeedMore(Exception):
    pass


def timeit(message_before='', message_after=''):
    def timeit_wrap(func):
        @functools.wraps(func)
        def newfunc(*args, **kwargs):
            if message_before != '':
                print(message_before)
            start_time = time.time()
            ret_val = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            print(message_after + ' in {} ms\n'.format(
                int(elapsed_time * 1000)))
            return ret_val

        return newfunc

    return timeit_wrap


class FreqCounter:

    __slots__ = 'total_count tag_counts'.split()

    def __init__(self):
        self.total_count = 0
        self.tag_counts = defaultdict(int)

    def count(self, tag_list = list()):
        self.total_count += 1

        for tag in tag_list:
            self.tag_counts[tag] += 1


''' Trie implementation got from https://github.com/dhain/trie '''

class Node(object):
    """Internal representation of Trie nodes."""
    __slots__ = 'parent key nodes value'.split()
    no_value = object()

    def __init__(self, parent, key, nodes, value):
        self.parent = parent
        self.key = key
        self.nodes = nodes
        self.value = value

    @property
    def keypath(self):
        n = self
        keypath = [n.key for n in iter(lambda: n.parent, None) if n.key]
        keypath.reverse()
        keypath.append(self.key)
        return keypath

    def walk(self):
        nodes = [self]
        while nodes:
            node = nodes.pop()
            if node.value is not node.no_value:
                yield node
            nodes.extend(node.nodes[key] for key in sorted(node.nodes, reverse=True))


class Trie(object):
    """A simple prefix tree (trie) implementation.
    If attempting to access a node without a value, but with descendents,
    NeedMore will be raised. If there are no descendents, KeyError will be
    raised.
    Usage:
    >>> import trie
    >>> from pprint import pprint
    >>> t = trie.Trie()
    >>> t['foobaz'] = 'Here is a foobaz.'
    >>> t['foobar'] = 'This is a foobar.'
    >>> t['fooqat'] = "What's a fooqat?"
    >>> pprint(list(t))
    [['f', 'o', 'o', 'b', 'a', 'r'],
     ['f', 'o', 'o', 'b', 'a', 'z'],
     ['f', 'o', 'o', 'q', 'a', 't']]
    >>> pprint(list(t.iteritems()))
    [(['f', 'o', 'o', 'b', 'a', 'r'], 'This is a foobar.'),
     (['f', 'o', 'o', 'b', 'a', 'z'], 'Here is a foobaz.'),
     (['f', 'o', 'o', 'q', 'a', 't'], "What's a fooqat?")]
    >>> t['foo']
    Traceback (most recent call last):
        ...
    NeedMore
    >>> t['fooqux']
    Traceback (most recent call last):
        ...
    KeyError: 'fooqux'
    >>> t.children('fooba')
    {'r': 'This is a foobar.', 'z': 'Here is a foobaz.'}
    >>> del t['foobaz']
    >>> pprint(list(t.iteritems()))
    [(['f', 'o', 'o', 'b', 'a', 'r'], 'This is a foobar.'),
     (['f', 'o', 'o', 'q', 'a', 't'], "What's a fooqat?")]
    """

    def __init__(self, root_data=Node.no_value, mapping=()):
        """Initialize a Trie instance.
        Args (both optional):
            root_data:  value of the root node (ie. Trie('hello')[()] == 'hello').
            mapping:    a sequence of (key, value) pairs to initialize with.
        """
        self.root = Node(None, None, {}, root_data)
        self.extend(mapping)

    def extend(self, mapping):
        """Update the Trie with a sequence of (key, value) pairs."""
        for k, v in mapping:
            self[k] = v

    def __setitem__(self, k, v):
        n = self.root
        for c in k:
            n = n.nodes.setdefault(c, Node(n, c, {}, Node.no_value))
        n.value = v

    def _getnode(self, k):
        n = self.root
        for c in k:
            try:
                n = n.nodes[c]
            except KeyError:
                raise KeyError(k)
        return n

    def __getitem__(self, k):
        n = None
        try:
            n = self._getnode(k)
        except KeyError:
            self[k] = FreqCounter()
            n = self._getnode(k)
        if n.value is Node.no_value:
            n.value = FreqCounter()
        return n.value

    def __delitem__(self, k):
        n = self._getnode(k)
        if n.value is Node.no_value:
            raise KeyError(k)
        n.value = Node.no_value
        while True:
            if n.nodes or not n.parent or n.value is not Node.no_value:
                break
            del n.parent.nodes[n.key]
            n = n.parent

    def children(self, k):
        """Return a dict of the immediate children of the given key.
        Example:
        >>> t = Trie()
        >>> t['foobaz'] = 'Here is a foobaz.'
        >>> t['foobar'] = 'This is a foobar.'
        >>> t.children('fooba')
        {'r': 'This is a foobar.', 'z': 'Here is a foobaz.'}
        """
        n = self._getnode(k)
        return dict((k, n.nodes[k].value)
                    for k in n.nodes
                    if n.nodes[k].value is not Node.no_value)

    def __iter__(self):
        """Yield the keys in order."""
        for node in self.root.walk():
            yield node.keypath

    def iteritems(self):
        """Yield (key, value) pairs in order."""
        for node in self.root.walk():
            yield node.keypath, node.value

    def itervalues(self):
        """Yield values in order."""
        for node in self.root.walk():
            yield node.value

class TopChart:
    TOP_COUNT = 10
    cmpr = staticmethod(lambda a, b: a[1] < b[1] if a[2] == b[2] else a[2] < b[2])

    def __init__(self):
        self.top = list()

    def add_word(self, word, pxy, pmi, px):
        if len(self.top) < TopChart.TOP_COUNT:
            self.top.append((word, pxy, pmi, px))
            self.__sort()
            return

        if TopChart.cmpr(self.top[-1], (word, pxy, pmi, px)):
            self.top.append((word, pxy, pmi, px))
            self.__sort()
            self.top.pop()

    def __sort(self):
        self.top.sort(key=lambda item: (item[2], item[1]), reverse=True)


class CosineSimilCalculator:
    def __init__(self):
        self.lengths = defaultdict(int)
        self.scalar_prods = defaultdict(int)

    def process(self, freq_counter):
        tag_counts = freq_counter.tag_counts
        for tag1 in tag_counts:
            for tag2 in tag_counts:
                if tag1 == tag2:
                    self.lengths[tag1] += tag_counts[tag1] ** 2
                elif tag1 < tag2:
                    prod_part = tag_counts[tag1] * tag_counts[tag2]
                    self.scalar_prods[(tag1, tag2)] += prod_part

    def get_simil_coef(self, tag1, tag2):
        key = (tag1, tag2) if tag1 < tag2 else (tag2, tag1)
        length1 = math.sqrt(self.lengths[tag1])
        length2 = math.sqrt(self.lengths[tag2])

        if length1 * length2 == 0:
            return 0

        return float(self.scalar_prods[key]) / length1 / length2

TAG_LIST = ('c++', 'c', 'java', 'perl', 'python', 'ruby')

def sort_out_tags(tag_list):
    refined_tags = []

    for tag in tag_list:
        if lower(tag) in TAG_LIST:
            refined_tags.append(lower(tag))

    return refined_tags

reg = re.compile('[A-Za-z]+')
def get_words(text):
    return reg.findall(text)

def build_trie(csv_file):
    trie = Trie()
    csv_reader = csv.reader(csv_file)
    print("Analyzing...")
    for index, row in enumerate(csv_reader):
        if index == 0:
            continue

        tag_list = sort_out_tags(row[8:13])


        if index > 0 and index % 5000 == 0:
            print ("{} done...".format(index))

        if len(tag_list) == 0:
            continue

        words = get_words(row[6]) + get_words(row[7])
        for word in words:
            trie[word].count(tag_list)
    return trie

def process_trie(trie):
    tops = {tag: TopChart() for tag in TAG_LIST}
    cosine_calc = CosineSimilCalculator()
    cos_proc = cosine_calc.process
    log = math.log
    for word, freq_counter in trie.iteritems():
        word = ''.join(word)
        px = freq_counter.total_count
        cos_proc(freq_counter)
        for tag in freq_counter.tag_counts:
            pxy = freq_counter.tag_counts[tag]
            if pxy == 0:
                continue

            pmi = log(float(pxy) / px, 2)
            tops[tag].add_word(word, pxy, pmi, px)

    for tag in TAG_LIST:
        print("Top for {}:".format(tag))
        print('\n'.join([x[0] for x in tops[tag].top]))
        print('-'*40)

    for tag1 in TAG_LIST:
        for tag2 in TAG_LIST:
            if tag1 < tag2:
                print("{0} is similar to {1} for about {2:.4f}".format(tag1, tag2, cosine_calc.get_simil_coef(tag1, tag2)))

def filter_trie(trie):
    for word, freq_counter in trie.iteritems():
        if freq_counter.total_count < 5:
            del(trie[''.join(word)])

@timeit(message_after='Work done')
def main():
    if len(sys.argv) < 2:
        print("USAGE: {0} <filename>".format(ntpath.basename(sys.argv[0])))
        exit(0)

    csv_file = open(sys.argv[1], 'rb')
    trie = build_trie(csv_file)
    filter_trie(trie)
    process_trie(trie)


if __name__ == '__main__':
    main()