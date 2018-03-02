from six import Iterator
import io
import sys
import re
from datetime import datetime
import chardet
import codecs


def get_encoding(filename):
    f = io.open(filename, mode='rb')
    raw = f.read(8192)
    f.close()
    guess = chardet.detect(raw)
    return guess.get("encoding")


def is_start(d):
    if d.startswith("<") and d.endswith(">") and not d.endswith("/>") and not d.startswith("</"):
        return True
    return False


def is_end(d):
    if d.startswith("</"):
        return True
    if d.endswith("/>"):
        return True
    if d.endswith("?>"):
        return True
    return False


# returns true if datum is composed only of newlines, returns, or spaces
def is_ignore(d):
    test = d
    test = test.replace("\n", "")
    test = test.replace("\r", "")
    test = test.replace("\t", "")
    test = test.replace(" ", "")
    if len(test) == 0:
        return True
    return False


exceptions = 0

cdataEndRE = re.compile("]]>")


def str_match(source, offset, target):
    if len(target) > len(source) - offset:
        return False
    for i in xrange(offset, offset + len(target)):
        if source[i] != target[i - offset]:
            return False
    return True


def has_datum(chunk, chunkStart):
    if chunkStart >= len(chunk):
        return -1

    # datum always starts at 0 index
    # we return -1 if there is no datum
    # other wise we return last index of datum
    # we have a start or end tag

    if str_match(chunk, chunkStart, "<![CDATA["):
        for i in xrange(chunkStart + 9, len(chunk) - 2):
            if str_match(chunk, i, "]]>"):
                return i + 3
        return -1

    if chunk[chunkStart] == "<":
        # it seems xrange is faster than regex for this
        # search = re_greater.search(chunk)
        # idx = -1
        # try:
        #    idx = search.regs[0][0] + 1
        # except:
        #    pass
        # return id

        # we have an element
        # look ahead for closing brace
        for i in xrange(chunkStart, len(chunk)):
            if chunk[i] == ">":
                return i + 1
    else:
        # it seems xrange is faster than regex for this
        # search = re_less.search(chunk)
        # idx = -1
        # try:
        #    idx = search.regs[0][0]
        # except:
        #    pass
        # return idx

        # we have text data
        # look forward for opening brace
        for i in xrange(chunkStart, len(chunk)):
            if chunk[i] == "<":
                return i

    return -1


class DatumIterator(Iterator):

    def __init__(self, filename, encoding, block_size):
        self.filename = filename
        self.file = io.open(filename, mode='r', encoding=encoding)
        self.block_size = block_size  # block_size is # bytes to read at a time from file stream
        self.has_next = False
        self.chunk = ""
        self.chunkStart = 0

    def __iter__(self):
        return self

    def __next__(self):

        go = True

        while 1:

            chunk_length = len(self.chunk)

            # check for datum in chunk
            datum_end = has_datum(self.chunk, self.chunkStart)

            if datum_end > 0:
                # get datum
                datum = self.chunk[self.chunkStart:datum_end]
                # remove datum from remaining chunk
                self.chunkStart = datum_end
                return datum
            else:
                self.chunk = self.chunk[self.chunkStart:]
                self.chunkStart = 0
                # used to check if we've hit EOF
                chunk_length = len(self.chunk)
                # make sure we have data
                self.chunk += self.file.read(self.block_size)
                # if pre-read == pre-read+read, we're at EOF
                if chunk_length == len(self.chunk):
                    go = False

            # stop if we're out of data
            if not go:
                raise StopIteration()


infile = sys.argv[1]

charset = get_encoding(infile)

# outfile = infile[0:infile.rindex(".")]+".trns.xml"
# out = codecs.open(outfile, mode='w', encoding=charset)
# out = io.open(outfile, mode='w', encoding=charset)

start_time = datetime.now()

if len(sys.argv) > 2:
    try:
        result = codecs.lookup(sys.argv[2])
        charset = sys.argv[2]
    except:
        pass

iterator = DatumIterator(infile, charset, 8192)

indent = 0

prevStart = False
prevEnd = False

for d in iterator:

    d = d.encode(charset)

    if is_ignore(d):
        continue

    if d.startswith("<![CDATA["):
        sys.stdout.write(d)
        continue

    start = is_start(d)
    end = is_end(d)

    if start and end:
        sys.stdout.write("\n" + d.rjust(indent * 3 + len(d)))
        prevStart = True
        prevEnd = True
    elif start and not end:
        sys.stdout.write("\n" + d.rjust(indent * 3 + len(d)))
        indent += 1
        prevStart = True
        prevEnd = False
    elif end and not start:
        indent -= 1
        if prevEnd and not prevStart:
            sys.stdout.write("\n" + d.rjust(indent * 3 + len(d)))
        else:
            sys.stdout.write(d)
        prevStart = False
        prevEnd = True
    else:
        sys.stdout.write(d)

time = datetime.now() - start_time
reg3 = re.compile("\\d+:\\d(\\d:\\d+\\.\\d{4})")
time = re.search(reg3, unicode(time))
time = "Runtime: %ss" % (time.group(1).encode("utf-8"))
sys.stderr.write("\n" + time + "\n")
sys.stderr.write("character encoding " + charset + "\n")
