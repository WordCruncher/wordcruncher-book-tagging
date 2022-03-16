import os
import re
import sys
from bs4 import BeautifulSoup as BS
from glob import glob
import stanza
from tqdm import tqdm as progress

lemmas = {}
# TODO: Change this to the 2-letter language code for your language.
# See the possible language taggers here: https://stanfordnlp.github.io/stanza/available_models.html
lang = 'pt'
files = glob(f'original/PT-Scriptures2015.etax')
output_folder_name = 'tagged'
# If there is content that you don't want tagged, then add the full HTML start tag to it. 
tags_to_skip= ['<x>', '<p st="c">', '<trow>']


class ETAXTagger:
    def __init__(self, etaxFile, outputPath, tagger, lang='en', tags_to_skip=['<x>']):
        self.etaxFile = etaxFile
        self.POSetaxFile = f'{outputPath}POS-{os.path.basename(etaxFile)}'
        self.outputPath = outputPath
        self.lang = lang
        self.tags_to_skip = tags_to_skip
        self.tagger = tagger
        self.tag()

    def tag(self):
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)
        with open(self.etaxFile, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        fOut = open(self.POSetaxFile, 'w', encoding='utf-8')
        for l in progress(lines):
            newline = ''
            # Only tag lines that have a length greater than 0.
            if len(l.strip()) == 0:
                continue

            # Create a regex string that can identify tags that have the "noindex" character property (e.g., <x>...</x>)
            skipTags = self.regextags_to_skip()
            # Find all tags that should be skipped.
            tag_search = re.findall(rf'{skipTags}|(?:<[/\?]?[^>]+?>)', l)
            # Replace all tags with the Mongolian character ༣. Change this if Mongolian is the tagged language.
            for tag in tag_search:
                l = l.replace(tag, '   א   ')
            # Add space around common "problem" characters (e.g., em-dash and underscore)
            l = self.clean_line(l)
            # Search through string by limiting the string's scope to what's not been tagged yet.
            # This is so that words like "the" do not get tagged multiple times at the beginning of a sentence.
            maxCharIndex = 0
            lineData = []
            # Manage Duplicates
            startChars = []

            lineLength = len(l)
            # This is designed to identify what whitespace isn't tagged and add it to the lineData as well.
            currentReadIndex = 0

            sentenceIndex = 0
            for sent in self.tagger(l).sentences:
                sentenceIndex += 1
                for word in sent.words:
                    characterSearch = re.search(
                        r'start_char=(\d+?)\|end_char=(\d+?)$', word.parent.misc)
                    startChar = int(characterSearch.group(1))
                    if startChar not in startChars:
                        startChars.append(startChar)
                        duplicate = False
                    else:
                        duplicate = True

                    endChar = int(characterSearch.group(2))
                    actualText = l[startChar:endChar]
                    pos = word.pos
                    xpos = word.xpos
                    if '$' in word.pos:
                        pos = word.pos.replace('$', 'S')
                    lemma = word.lemma

                    # Collect lemma information to create lexicon dictionary if needed.
                    if 'א' not in lemma:
                        if f'{lemma.upper()}_{pos}' not in lemmas:
                            lemmas[f'{lemma.upper()}_{pos}'] = {
                                'freq': 0,
                                'words': []
                            }
                        lemmas[f'{lemma.upper()}_{pos}']['freq'] += 1

                        if actualText.lower() not in lemmas[f'{lemma.upper()}_{pos}']['words']:
                            lemmas[f'{lemma.upper()}_{pos}']['words'].append(actualText.lower())

                    feats = word.feats
                    isTag = False
                    # If the text is a replaced tag, then find it's true value in tag_search list.
                    if 'א' in actualText:
                        isTag = True
                    # Escape the characters <, >, &, and "

                    if duplicate:
                        lineData[-1]['text2'] = actualText
                        lineData[-1]['pos2'] = pos
                        lineData[-1]['xpos2'] = xpos
                        lineData[-1]['lemma2'] = lemma
                        lineData[-1]['feats2'] = feats
                        lineData[-1]['isDuplicate'] = duplicate
                    else:
                        lineData.append({
                            'start': startChar,
                            'end': endChar,
                            'text': actualText,
                            'pos': pos,
                            'xpos': xpos,
                            'feats': feats,
                            'lemma': lemma,
                            'isTag': isTag,
                            'isDuplicate': duplicate,
                            'end_line_data': None,
                            'sentence_index': sentenceIndex,
                            'prefix_text': l[currentReadIndex:startChar]
                        })
                    currentReadIndex = endChar
                    ibrk = 0
            lineData.append({
                'end_line_data': l[currentReadIndex:]
            })


            sentenceIndexSet = set()
            for idx, word in enumerate(lineData):
                # Check to see if it's the end of the line
                if 'end_line_data' in word and word['end_line_data'] != None:
                    newline += word['end_line_data']
                # Check to see if it's a tag.
                elif word['isTag']:
                    newline += word['prefix_text'] + word['text']
                elif word['isDuplicate']:
                    newline += f'{word["prefix_text"]}<w pos1="{word["pos"]}" xpos1="{word["xpos"]}" lemma1="{word["lemma"]}" feats1="{word["feats"]}" pos2="{word["pos2"]}" xpos2="{word["xpos2"]}" lemma2="{word["lemma2"]} feats2="{word["feats2"]}" sentId="{word["sentence_index"]}">{word["text"]}</w>'
                else:
                    newline += f'{word["prefix_text"]}<w pos="{word["pos"]}" xpos="{word["xpos"]}" lemma="{word["lemma"]}" feats="{word["feats"]}" sentId="{word["sentence_index"]}">{word["text"]}</w>'
            newline = re.sub(r'  —  ', r'<zs/>—<zs/>', newline)
            newline = re.sub(r'  _  ', r'<zs/>_<zs/>', newline)
            newline = re.sub(r'  \|  ', '<zs/>|<zs/>', newline)
            newline = re.sub(r'&AMP;', r'&amp;', newline)
            newline = re.sub(
                r'&(?!amp;)(?!quot;)(?!lt;)(?!gt;)', r'&amp;', newline)
            for tag in tag_search:
                newline = re.sub(r'   א   ', tag, newline, 1)


            newline += '</s>'
            print(newline, file=fOut)
        # Close the file
        fOut.close()

        with open(f'{lang}-lemmas.txt', 'w', encoding='utf-8') as fOut:
            for k, v in lemmas.items():
                for word in v['words']:
                    print(f'{k}\t{v["freq"]}\t{word}', file=fOut)

    def clean_line(self, l):
        l = re.sub(r'&amp;', r'&', l)
        l = re.sub(chr(65279), r'', l)
        l = re.sub(r'—', r'  —  ', l)
        l = re.sub(r'_', r'  _  ', l)
        l = re.sub(r'\|', ' | ', l)
        return re.sub(r'<ch>(.+?)</ch>', r'\1', l)

    def regextags_to_skip(self):
        newList = []
        for i in self.tags_to_skip:
            name = re.search(r'^<(\w+?)[ >]', i).group(1)
            newList.append(f'(?:{i}.+?</{name}>)')
        return '|'.join(newList)

    def regexEscape(self, string):
        currentSearchString = string.replace('.', '\.')
        currentSearchString = currentSearchString.replace('*', '\*')
        currentSearchString = currentSearchString.replace('+', '\+')
        currentSearchString = currentSearchString.replace('[', '\[')
        currentSearchString = currentSearchString.replace(']', '\]')
        currentSearchString = currentSearchString.replace('{', '\{')
        currentSearchString = currentSearchString.replace('}', '\}')
        currentSearchString = currentSearchString.replace('?', '\?')
        currentSearchString = currentSearchString.replace('(', '\(')
        currentSearchString = currentSearchString.replace(')', '\)')
        currentSearchString = currentSearchString.replace('$', '\$')
        currentSearchString = currentSearchString.replace('^', '\^')
        currentSearchString = currentSearchString.replace('|', '\|')
        return currentSearchString



def initializeTagger(lang):
    try:
        return stanza.Pipeline(lang)
    except:
        stanza.download(lang)
        return stanza.Pipeline(lang)


tagger = initializeTagger(lang)


for f in files:
    print(f)
    ETAXTagger(f, f'{output_folder_name}/', lang=lang, tagger=tagger, tags_to_skip=tags_to_skip)
