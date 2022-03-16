from glob import glob
import re

files = glob('pt-lemmas.txt')
output_file_name = 'Portuguese Lexicon.etax'


w_dict = {} # (lemma:form)
for f in files:

    with open(f, 'r', encoding='utf-8') as fIn:
        for line in fIn.read().splitlines():
            lemma, freq, word = line.split('\t')
            # Outputs only words that occur at least 4 times. If they occur once, they don't need to be in the lexicon anyway.
            # If they occur 2 or 3 times, it's likely an error.
            # That doesn't mean that there aren't errors in the tagger for higher frequency words, though...
            if lemma.lower() not in w_dict and int(freq) > 4:
                w_dict[lemma.lower()] = [word.lower(), lemma.lower()]

            elif int(freq) > 4:
                w_dict[lemma.lower()].append(word.lower())



alph_list = sorted(set([k for k,v in w_dict.items()]))

fOut = open(output_file_name, 'w', encoding='utf-8')

abc_set = set()
for i in alph_list:
    wordForms = list(set(w_dict[i]))
    if len(wordForms) > 1:
        first_letter = i[0].upper()
        if first_letter not in abc_set:
            abc_set.add(first_letter)
            print(f'<p><R ref="a,1:{first_letter}"/><b>{first_letter}</b></p>', file=fOut)

        print(f'<p><R ref="h,2:{i}"/> <b>{i}</b></p>', file=fOut)
        for j in sorted(wordForms):
            print(f'<p><R ref="w,3:"/> {j}</p>', file=fOut)

fOut.close()
