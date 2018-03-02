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


re_CDATA_end = re.compile("]]>")


def has_datum(chunk):

    # datum always starts at 0 index
    # we return -1 if there is no datum
    # other wise we return last index of datum
    # we have a start or end tag

    if chunk.startswith("<![CDATA["):
        search = re_CDATA_end.search(chunk)
        if search is None:
            return -1
        return search.regs[0][0] + 3

    if chunk.startswith("<"):
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
        for i in xrange(len(chunk)):
            if chunk[i] == ">":
                return i+1
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
        for i in xrange(len(chunk)):
            if chunk[i] == "<":
                return i

    return -1


class DatumIterator(Iterator):

    def __init__(self, filename, encoding, block_size):
        self.filename = filename
        self.file = io.open(filename, mode='r', encoding=encoding)
        self.block_size = block_size  # block_size is # bytes to read at a time from file stream
        self.has_next = False
        self.encoding = encoding
        self.chunk = ""

    def __iter__(self):
        return self

    def __next__(self):

        go = True

        while 1:

            # check for datum in chunk
            datum_end = has_datum(self.chunk)
            if datum_end > 0:
                # get datum
                datum = self.chunk[0:datum_end]
                # remove datum from remaining chunk
                self.chunk = self.chunk[datum_end:]
                return datum
            else:
                # used to check if we've hit EOF
                current_length = len(self.chunk)
                # get more data
                self.chunk += self.file.read(self.block_size).encode(self.encoding)
                new_length = len(self.chunk)
                # if pre-read == pre-read+read, we're at EOF
                if current_length == new_length:
                    go = False

            # stop if we're out of data
            if not go:
                raise StopIteration()


infile = sys.argv[1]

charset = get_encoding(infile)

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

    if is_ignore(d):
        continue

    if d.startswith("<![CDATA["):
        sys.stdout.write(d)
        continue

    start = is_start(d)
    end = is_end(d)

    if start and end:
        sys.stdout.write("\n"+d.rjust(indent * 3 + len(d)))
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
sys.stderr.write("\n"+time+"\n")
sys.stderr.write("character encoding " + charset + "\n")