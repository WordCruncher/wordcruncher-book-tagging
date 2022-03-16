import re
import os
from glob import glob

files = glob('tagged/*.etax')
output_folder_name = 'new_etax'
sentence_level_number = 4

def isAlphanumeric(string):
    # WordCruncher does messy things with punctuation within a word. 
    # Here, we wrap a word whenever at least one character in the word is not alphanumeric.
    if not re.search(r'^\w+$', string):
        return f'<ch>{string}</ch>'
    return string


def replace(file):
    with open(file, 'r', encoding='utf-8') as file_in:
        data = file_in.read().splitlines()

    for idx, line in enumerate(data):
        sentence_numbers = set()

        # Find all <w pos="" lemma="" feats="">...</w>
        words = re.findall(r' ?<w.+?>.+?</w>', line)
        for word in words:
            newString = ''
            # Add a <zs/> if the regex starts with a space
            if word.startswith(' '):
                newString += '<zs/>'
            
            pos = isAlphanumeric(re.search(r' pos1?="(.+?)"', word).group(1))
            xpos = isAlphanumeric(re.search(r' xpos1?="(.+?)"', word).group(1))
            lemma = isAlphanumeric(re.search(r' lemma1?="(.+?)"', word).group(1))
            feats = re.search(r' feats1?="(.+?)"', word).group(1).split('|')
            feats = [isAlphanumeric(i) for i in feats]
            sentence_number = re.search(r' sentId="(.+?)"', word).group(1)
            if 'None' in feats:
                feats = []
            wordText = isAlphanumeric(re.search(r'<w.+?>(.+?)</w>', word).group(1))
            
            # Add Sentence Reference Level if it's a new number
            if sentence_number not in sentence_numbers:
                sentence_numbers.add(sentence_number)
                newString += f'<R ref="S,{sentence_level_number}:{sentence_number}"/>'

            # Check for alphanumericity
            newString += f'{wordText}_{pos}<T st="l"> {lemma.upper()}_{pos.upper()}</T>{"".join(["""<T st="f">""" + feat + "</T>" for feat in feats])}'
            line = line.replace(word, newString)
        data[idx] = line

    basename = os.path.basename(file)
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name)
    with open(f'{output_folder_name}/{basename}', 'w', encoding='utf-8') as file_out:
        for line in data:
            print(line, file=file_out)



for f in files:
    replace(f)