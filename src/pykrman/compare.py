"""Compare output transcriptions
"""
import json
import os
import re
from collections import Counter

from pykrman.stopwords import get_stopwords
from pykrman.util import read_pdf
from nlpakki.score.similarity import jaccard_similarity, cosine_similarity, smith_waterman_distance


class Wordlist:

    def __init__(self, text, space_pattern=r'[^A-Za-z]+', flags=0,
                 stopwords='default', important_words=None,
                 ignore_case=True):
        self.split_pat = re.compile(space_pattern, flags=flags)
        self.letter_pat = re.compile(r'[^A-Za-z]*')
        self.ignore_case = ignore_case
        self.important_words = [word.lower() for word in important_words] or []
        self.stopwords = self.get_stopwords(stopwords)
        self.letters = Counter(self.get_letters(text))
        self.words = self.text_to_wordlist(text)
        self.unique = set(self.words)
        self.counter = Counter(self.words)

    def get_letters(self, text):
        if self.ignore_case:
            text = text.lower()
        return self.letter_pat.sub('', text)

    def text_to_wordlist(self, text):
        if self.ignore_case:
            text = text.lower()
        return [w for w in self.split_pat.split(text) if w not in self.stopwords]

    @staticmethod
    def get_stopwords(source):
        if source == 'default':
            return get_stopwords()
        else:  # assume it's a file
            with open(source) as fh:
                return {line.strip() for line in fh}

    @classmethod
    def frompdf(cls, fp, encoding=None, **kwargs):
        return cls(read_pdf(fp), **kwargs)

    @classmethod
    def fromtext(cls, fp, encoding='utf8', **kwargs):
        with open(fp, encoding=encoding) as fh:
            return cls(fh.read(), **kwargs)

    def compare(self, text):
        """Build wordlist from text, and compare"""
        words = self.text_to_wordlist(text)
        letters = self.get_letters(text)
        unique = set(words)
        cnt = Counter(words)
        diff = self.counter - cnt
        extra = cnt - self.counter
        important_words = {}
        for word in self.important_words:
            if not word.endswith('*'):
                important_words[word] = {
                    'true_count': self.counter[word],
                    'count': cnt[word]
                }
            else:
                prefix = word[:-1]
                true_count = 0
                for w in self.counter:
                    if w.startswith(prefix):
                        true_count += self.counter[w]
                count = 0
                for w in cnt:
                    if w.startswith(prefix):
                        count += cnt[w]
                important_words[word] = {
                    'true_count': true_count,
                    'count': count,
                }
        return {
            'descriptive': {
                'total': {
                    'words': len(words),
                    'true_words': len(self.words),
                    'missing_words': sum(diff.values()),
                    'extra_words': sum(extra.values()),
                },
                'unique': {
                    'words': len(unique),
                    'true_words': len(self.unique),
                    'missing_words': len(self.counter.keys() - cnt.keys()),
                    'extra_words': len(cnt.keys() - self.counter.keys()),
                }
            },
            'word_similarity': {
                'jaccard': jaccard_similarity(self.unique, unique),
                'cosine': cosine_similarity(self.counter, cnt),
                # don't penalize insertions due to OCR inserting too much cruff
                'swd': smith_waterman_distance(self.words, words, mismatch=-2, deletion=-2, insertion=-0.5)
            },
            'letter_similarity': {
                'cosine': cosine_similarity(self.letters, letters),
                'swd': smith_waterman_distance(self.letters, letters)
            },
            'important_words': important_words
        }


def compare_ocr_pdf(true_pdf, *ocr_versions, important_words=None,
                    ignore_case=True, encoding='utf8'):
    if os.path.isfile(true_pdf):
        if true_pdf.endswith('.pdf'):
            wl = Wordlist.frompdf(true_pdf, important_words=important_words,
                                  ignore_case=ignore_case, encoding=encoding)
        else:
            wl = Wordlist.fromtext(true_pdf, important_words=important_words,
                                   ignore_case=ignore_case, encoding=encoding)
    else:  # is just text
        wl = Wordlist(true_pdf, important_words=important_words,
                      ignore_case=ignore_case)

    results = []
    if len(ocr_versions) == 1:
        base = ocr_versions[0]
        ocr_versions = [os.path.join(base, fn) for fn in os.listdir(base)]
    for ocr in ocr_versions:
        if os.path.isfile(ocr):
            with open(ocr, encoding=encoding) as fh:
                text = fh.read()
        elif os.path.isdir(ocr):
            texts = []
            for fn in os.listdir(ocr):
                with open(os.path.join(ocr, fn), encoding=encoding) as fh:
                    texts.append(fh.read())
            text = '\n'.join(texts)
        elif isinstance(ocr, tuple):
            ocr, text = ocr
        else:
            text = ocr
        res = json.dumps(wl.compare(text))
        if ocr:
            results.append((ocr, res))
        else:
            results.append((res,))
    return results


def process(true_pdf, output, ocr_versions, important_words=None,
            case_sensitive=False, encoding='utf8'):
    results = compare_ocr_pdf(true_pdf, *ocr_versions,
                              important_words=important_words,
                              ignore_case=not case_sensitive,
                              encoding=encoding)
    with open(output, 'w', encoding=encoding) as out:
        for result in results:
            out.write('\n'.join(result) + '\n')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-i', '--true-pdf',
                        help='Source pdf file (or equivalent dictionary file)')
    parser.add_argument('-o', '--output',
                        help='Output text file with analysis in json format')
    parser.add_argument('-v', '--ocr-versions', nargs='+',
                        help='Text output of OCR attempts; specified directory is treated'
                             ' as one item')
    parser.add_argument('--important-words', nargs='+',
                        help='Important words to specifically keep track of.')
    parser.add_argument('--case-sensitive', action='store_true', default=False,
                        help='Do not ignore case.')
    parser.add_argument('--encoding', default='utf8',
                        help='Default encoding for reading/writing')
    args = parser.parse_args()
    process(**vars(args))
