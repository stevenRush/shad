import re
import sys
import random
import operator
import pickle
import os
import functools
import time
from optparse import OptionParser


def words(sentence):
    r = re.compile(r"(((The|the|A|a|An|an) )?[\w']+)")
    for word in r.findall(sentence):
        yield word[0]


def sentences(fileobj):
    r = re.compile(r'([^\.!\?]+)[\.!\?;][ ]?')
    for line in fileobj:
        for word in r.findall(line):
            yield word


class FrequencyCounter:
    def __init__(self):
        self.words = dict()

    def add_word(self, key):
        if key not in self.words:
            self.words[key] = 0

        self.words[key] += 1

    def get_most_frequent(self):
        return max(self.words.iteritems(), key=operator.itemgetter(1))[0]


class NgramStatistics:
    def __init__(self):
        self.__ngrams = dict()

    def add_ngram(self, *args):
        key = args[:-1]
        if key not in self.__ngrams:
            self.__ngrams[key] = FrequencyCounter()

        self.__ngrams[key].add_word(args[-1])

    def get_next_for(self, key):
        if key not in self.__ngrams:
            return None

        return self.__ngrams[key].get_most_frequent()


class StatisticsEngine:
    dump_file_path = "dump.pickle"

    def __init__(self):
        self.__2grams = NgramStatistics()
        self.__3grams = NgramStatistics()
        self.__open_words = list()
        self.__all_words = list()

        self.__prelast_word = None
        self.__last_word = None

        self.__last_open_word = None

    def add_word(self, word):

        if self.__prelast_word is None:
            self.__open_words.append(word)
            self.__prelast_word = word

            return

        self.__all_words.append(word)

        if self.__last_word is None:
            self.__2grams.add_ngram(self.__prelast_word, word)
            self.__last_word = word

            return

        self.__2grams.add_ngram(self.__last_word, word)
        self.__3grams.add_ngram(self.__prelast_word, self.__last_word, word)

        self.__last_word = self.__prelast_word
        self.__prelast_word = word

    def end_sentence(self):
        self.__prelast_word = None
        self.__last_word = None

    def get_open_word(self):
        open_word = random.choice(self.__open_words)

        if len(self.__open_words) == 1:
            return open_word

        while open_word == self.__last_open_word:
            open_word = random.choice(self.__open_words)

        self.__last_open_word = open_word

        return open_word

    def get_next_for(self, *args):
        next_word = None

        if len(args) == 1:
            next_word = self.__2grams.get_next_for(args)

        if len(args) == 2:
            next_word = self.__3grams.get_next_for(args) or \
                        self.__2grams.get_next_for(args[-1])

        return next_word

    def get_next_random(self):
        return random.choice(self.__all_words)

    def dump(self):
        file_dump = open(StatisticsEngine.dump_file_path, "wb")
        pickle.dump(self, file_dump)

    @classmethod
    def load_from_dump(cls):
        engine_dump = open(StatisticsEngine.dump_file_path, "rb")
        return pickle.load(engine_dump)


def timeit(message_before, message_after):
    def timeit_wrap(func):
        @functools.wraps(func)
        def newfunc(*args, **kwargs):
            print(message_before)
            start_time = time.time()
            func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            print(message_after + ' in {} ms\n'.format(
                int(elapsed_time * 1000)))

        return newfunc

    return timeit_wrap


class TextGenerator:
    @timeit("Loading engine...", "Engine loaded")
    def __init__(self, sentence_count, passage_count):
        self.__engine = StatisticsEngine.load_from_dump()
        self.__passage_count = passage_count
        self.__sentence_count = sentence_count

    def __generate_sentence(self):
        sentence = [self.__engine.get_open_word()]
        next_word = self.__engine.get_next_for(sentence[-1]) or \
                    self.__engine.get_next_random()
        sentence.append(next_word)

        min_sentence_length = random.randint(4, 7)

        while True:
            next_word = self.__engine.get_next_for(sentence[-2], sentence[-1])
            # if there is no next word
            if next_word is None:
                # if sentence is too short, just add random word
                if len(sentence) < min_sentence_length:
                    next_word = self.__engine.get_next_random()
                else:
                    break
            sentence.append(next_word)

        return " ".join(sentence) + ". "

    def generate_text(self):
        text = []
        for passage in range(self.__passage_count):
            for sentence in range(self.__sentence_count):
                text.append(self.__generate_sentence())
            if passage != self.__passage_count - 1:
                text.append("\n\n")

        return "".join(text)


class Learner:
    def __init__(self, paths):
        self.engine = StatisticsEngine()

        self.__analyze_files(paths)

    @timeit("Analyzing texts...", "Texts analyzed")
    def __analyze_files(self, paths):
        for path in paths:
            # if passed path is file
            if os.path.isfile(path):
                self.__analyze_one(path)
            else:
                # otherwise just walking whole directory tree
                # and analyzing every file
                for directory, dirs, files in os.walk(path):
                    for file_name in files:
                        self.__analyze_one(os.path.join(directory, file_name))

    def __analyze_one(self, file_path):
        fileobj = open(file_path)

        for sentence in sentences(fileobj):
            for word in words(sentence):
                self.engine.add_word(word)

            self.engine.end_sentence()

    @timeit("Dumping engine...", "Engine dumped")
    def dump(self):
        self.engine.dump()


def learn(paths):
    learner = Learner(paths)
    learner.dump()


def generate(sentence_count, passage_count):
    generator = TextGenerator(sentence_count, passage_count)
    print "Generated text: "
    print generator.generate_text()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-m', '--mode', type='choice',
                      action='store', dest='mode',
                      choices=['learn', 'generate'],
                      help='action to do: \'generate\' or \'learn\'')
    parser.add_option('-p', '--passages', type='int', metavar='N',
                      dest='passage_count', help='passages count',
                      default=1)
    parser.add_option('-s', '--sentences', type='int', metavar='N',
                      dest='sentence_count', help='sentence count per passage',
                      default=10)

    if len(sys.argv) < 2:
        parser.print_help()
        exit(-1)

    (options, args) = parser.parse_args()

    if options.mode == 'generate':
        generate(options.sentence_count, options.passage_count)
    elif options.mode == 'learn':
        if len(args) == 0:
            print "no files provided!"
            exit(-1)
        learn(args)
