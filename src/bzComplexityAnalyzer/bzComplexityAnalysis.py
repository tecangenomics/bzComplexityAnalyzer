import bz2
import random
import dataclasses
import statistics
import typing


class Alphabet(object):
    '''Object for holding various alphabet spaces.  This should leave it easy to add alphabets.'''

    def __init__(self, ignoreCase=True):
        self.ignoreCase = ignoreCase

    def dna(self):
        alphabet = "ATGC"
        if not self.ignoreCase:
            alphabet += "atgc"
        return list(alphabet)

    def alpha(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if not self.ignoreCase:
            alphabet += "abcdefghijklmnopqrstuvwxyz"
        return list(alphabet)

    def numeric(self):
        alphabet = "1234567890"
        return list(alphabet)

    def symbol(self):
        alphabet = "~!@#$%^&*()_+{}|:\"<>?`-=[]\\;',./ "
        return list(alphabet)

    def alphanumeric(self):
        return self.alpha() + self.numeric()

    def alphanumericSymbol(self):
        return self.alpha() + self.numeric() + self.symbol()


@dataclasses.dataclass()
class SequenceCompressionData:
    length: int
    averageMinimumCompressedLength: float
    average: float
    standardDeviation:float
    _distribution: statistics.NormalDist = None

    def __post_init__(self):
        self._distribution = statistics.NormalDist(self.average, self.standardDeviation)

    def compressionZScore(self, probandCompressionLength:int) -> float:
        adjustedCompressedLength = probandCompressionLength - self.averageMinimumCompressedLength
        deviationFromAverage = adjustedCompressedLength - self.average
        compressionSigma = deviationFromAverage / self.standardDeviation
        return compressionSigma

    def compressionPercentile(self, probandCompressionLength:int) -> float:
        adjustedCompressedLength = probandCompressionLength - self.averageMinimumCompressedLength
        percentile = self._distribution.cdf(adjustedCompressedLength)
        return percentile


class Analyzer:
    '''Uses the bz2 library to give an estimate of how much entropy is in a string of text.  Designed to be used with DNA sequence.  Self.alphabet is going to be an easy to access and modify variably by design.  It will be a list that users can directly add to or remove from as needed.  Iterations probably won't need to be changed unless dealing with performance issues, especially for long sequences'''

    def __init__(self, alphabet="dna", ignoreCase=True, iterations=1000):
        assert type(iterations) == int and iterations > 0, "Iterations must be a positive integer."
        assert alphabet, "Alphabet cannot be an empty space (no empty lists, sets, tuples or strings allowed)"
        if iterations < 10:
            raise Warning(
                "Iteration count should be at least 10 (and probably 100 or more) to be reliable and generate values that reproduce well")
        self.baselines = {}
        self.iterations = iterations
        self.ignoreCase = ignoreCase
        self.alphabet = []
        if type(alphabet) in (list, set, tuple):
            self.alphabet = list(alphabet)
        elif type(alphabet) == str:
            alphabet = alphabet.lower()
            if alphabet == "dna":
                self.alphabet = Alphabet(ignoreCase).dna()
            elif alphabet == "alpha":
                self.alphabet = Alphabet(ignoreCase).alpha()
            elif alphabet == "numeric":
                self.alphabet = Alphabet(ignoreCase).numeric()
            elif alphabet == "symbol":
                self.alphabet = Alphabet(ignoreCase).symbol()
            elif alphabet == "alphanumeric":
                self.alphabet = Alphabet(ignoreCase).alphanumeric()
            elif alphabet in ("alphanumericsymbol", "keyboard"):
                self.alphabet = Alphabet(ignoreCase).alphanumericSymbol()
            else:
                raise ValueError(
                    "Alphabet cannot be a string unless naming a pre-defined set.  Passed value: %s.  If defining a custom alphabet space, please pass it as a list.")
        else:
            raise ValueError(
                "Alphabet must be a string, tuple, set, or a string naming a pre-defined set of characters")

    def getAverageMinimumCompressedLength(self, length:int) -> float:
        minimumCompressedLengths = []
        for letter in self.alphabet:
            minimumCompressedLengths.append(self.getBzipByteLength(letter * length))
        averageMinimumCompressedLength = statistics.mean(minimumCompressedLengths)
        return averageMinimumCompressedLength

    def getAverageRandomCompressedLengthAndStandardDeviation(self, length:int, averageMinimumCompressedLength:float=None, iterations:int=None) -> typing.Tuple[float, float]:
        if not iterations:
            iterations = self.iterations
        if averageMinimumCompressedLength is None:
            averageMinimumCompressedLength = self.getAverageMinimumCompressedLength(length)
        randomStringCompressedLengths = []
        for i in range(iterations):
            randomSequence = "".join([random.choice(self.alphabet) for j in range(length)])
            randomStringCompressedLengths.append(self.getBzipByteLength(randomSequence) - averageMinimumCompressedLength)
        mean = statistics.mean(randomStringCompressedLengths)
        stdev = statistics.stdev(randomStringCompressedLengths)
        return mean, stdev

    def addLengthToBaselineTable(self, length) -> typing.Tuple[float, float, float]:
        random.seed(length)
        averageMinimumCompressedLength = self.getAverageMinimumCompressedLength(length)
        averageRandomCompressedLength, averageRandomCompressedStandardDeviation = self.getAverageRandomCompressedLengthAndStandardDeviation(length, averageMinimumCompressedLength)
        compressionDataObject = SequenceCompressionData(length, averageMinimumCompressedLength, averageRandomCompressedLength, averageRandomCompressedStandardDeviation)
        self.baselines[length] = compressionDataObject
        return averageMinimumCompressedLength, averageRandomCompressedLength, averageRandomCompressedStandardDeviation

    def getBzipByteLength(self, stringToCompress) -> int:
        if self.ignoreCase:
            stringToCompress = stringToCompress.upper()
        byteString = str.encode(stringToCompress)
        return len(bz2.compress(byteString))

    def getCompressionPercentile(self, probandString:str) -> float:
        probandString = str(probandString)
        length = len(probandString)
        if not length in self.baselines:
            self.addLengthToBaselineTable(length)
        return self.baselines[length].compressionPercentile(self.getBzipByteLength(probandString))

    def getCompressionZScore(self, probandString: str) -> float:
        probandString = str(probandString)
        length = len(probandString)
        if not length in self.baselines:
            self.addLengthToBaselineTable(length)
        return self.baselines[length].compressionZScore(self.getBzipByteLength(probandString))


if __name__ == "__main__":
    analyzer = Analyzer(iterations=10000)
    probandStrings = [
        "ATATATATATATATATATATATATATATATATATATATAT",
        "GATGGATCCTAGACGAGGGCCAATATGCTAATGCTAACCT",
        "GCGCCACTATGATCACATGGTGTGATTTGGTGTCATTTGG",
        "GATCCGGGTCCACGAAGTAATAGCGAGCAAGACAGACAGG",
        "TGACGAAAGATGGAAGCGTTGAGGCGTGTCGTGTCAGAAC",
        "ATGTACAGTGGCACACGTACGGTACGTACGTATGGTTGCT",
        "TCCACCACCACAAGTAGAGCCAGCTCGCGGCTGTGCGCGC",
        "GCTGGCTCTACTTGTGGTGGTGGACGGACGGCGCTCTTTT",
        "CGCTGGACTCGACGGCGGCGGCGAGGTCGTTGCGGCCCGC",
        "TTAATATAGAATTCTATGGAATTCACTCAGCAAATAACAC",
        "GGGAGGGGATGGGGAGCATTGCGGAGGCACGCGCAAGTTA",
        "ACAGCGACGGTTATATTAAGGAAAGGAATATGCGGATAAG",
        "ATCTTGGATCGATGGGTAACTAGGGATGAAGAAGAAGATG",
        "GCGATGCATGCATAAGTGGCACATCCAAATCCACTATTAC",
        "ACAGTCACAGTCACCAGCAGTAGTTGTTGCGATTCTAAAG",
        "AAAACAAGGGTTTCAGGTTTCATGGTATGTGCTTTCTTAG",
        "AAAGCAACCATGCTGAAAACTTTTGTTTTGTTATTTTGTC",
        "AGAGCCTCCTCTCCTACAACTGCTTTCATGGCTTGAACAT",
        "CGTCCACCACCACAAGTAGAGCCAGCTCGCGGCTGTGCGC",
        "TGCGATGCATGCATAAGTGGCACATCCAAATCCACTATTA",
        "ATATATATATATATATATATATATATATATATATATATAT",
        "GATCATCGAGCATCATGACTGCATGACTGCATCATACTAC",
        "ACGATCGATCGATCGATCGATCGATCGATCGATCGATCGC",
        "GGGTGGAGGCGGGAGGGGTGCGGGGGTGGCGGGAGGGGCG"
    ]
    for probandString in probandStrings:
        sigma = analyzer.getCompressionZScore(probandString)
        percentile = analyzer.getCompressionPercentile(probandString)
        sigma = round(sigma, 4)
        percentile = round(percentile, 4)
        print("%s\t%s\t%s" %(probandString, sigma, percentile))

