__author__ = 'Evgeny Eltyshev'

import os
import sys

class ColumnProcessor:
    KNOWN_VALUES_CAPTION = "known_values"
    UNIQUE_CAPTION = "uniq"
    MEAN_CAPTION = "mean"
    MEDIAN_CAPTION = "median"
    MIN_CAPTION = "min"
    MAX_CAPTION = "max"
    VARIANCE_CAPTION = "var"

    def __init__(self, column_name):
        self.column_name = column_name
        self.values = list()
        self.undefined_values_count = 0

    def add_value(self, value):
        if (value == "None"):
            self.undefined_values_count += 1
            return

        self.values.append(int(value))

    def print_stats(self):
        self.__calculate_stats()
        print "{0}: ".format(self.column_name)
        print "{0}: {1:.2f}".format(self.KNOWN_VALUES_CAPTION, self.known_values_share)
        print "{0}: {1}".format(self.UNIQUE_CAPTION, self.unique_values_count)
        print "{0}: {1:.2f}".format(self.MEAN_CAPTION, self.mean)
        print "{0}: {1}".format(self.MEDIAN_CAPTION, self.median)
        print "{0}: {1}".format(self.MIN_CAPTION, self.min)
        print "{0}: {1}".format(self.MAX_CAPTION, self.max)
        print "{0}: {1:.1f}".format(self.VARIANCE_CAPTION, self.variance)
        print "\n"

    def __calculate_stats(self):
        values_sum = sum(self.values)
        values_square_sum = sum((x ** 2 for x in self.values))
        values_count = len(self.values);

        self.mean = float(values_sum) / values_count    #unbiased sample mean
        sample_variance = float(values_square_sum) / values_count - self.mean ** 2
        self.variance = float(values_count) / (values_count - 1) * sample_variance #unbiased sample variance

        sorted_values = sorted(self.values)
        if (values_count % 2 == 0):
            k = values_count / 2
            self.median = (sorted_values[k] + sorted_values[k+1]) / 2
        else:
            self.median = sorted_values[(values_count + 1) / 2]
        self.unique_values_count = len(set(self.values))
        self.min = min(self.values)
        self.max = max(self.values)
        self.known_values_share = 1 - float(self.undefined_values_count) / values_count


class FileProcessor:
    def __init__(self, file_path):
        self.file_name = os.path.basename(file_path)
        self.file = open(file_path, 'r')

        self.column_processors = []
        column_names = self.file.readline()[:-1].split(',')
        self.column_count = len(column_names)
        for column_name in column_names:
            self.column_processors.append(ColumnProcessor(column_name))

        self.row_count = 0

        self.process()


    def process(self):
        for line in self.file:
            column_values = line.split(',')
            self.row_count += 1
            for index in range(self.column_count):
                self.column_processors[index].add_value(column_values[index])

    def print_stats(self):
        print "File {0} {1} rows, {2} cols.\n".format(self.file_name, self.row_count, self.column_count)

        for col_proc in self.column_processors:
            col_proc.print_stats()

if __name__ == "__main__":
    file_path = sys.argv[1]

    file_processor = FileProcessor(file_path)
    file_processor.process()
    file_processor.print_stats()
