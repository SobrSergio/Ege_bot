import os





def read_file(file_path):
    with open(file_path, encoding='utf-8') as file:
        return [line.strip() for line in file]

FILES_PATH = './files/'

ACCENTS_WORD = read_file(os.path.join(FILES_PATH, 'accents.txt'))
ACCENTS_WORD_WRONG = read_file(os.path.join(FILES_PATH, 'accents_wrong.txt'))
DICTIONARY_WORD = read_file(os.path.join(FILES_PATH, 'dictionary.txt'))
DICTIONARY_WORD_WRONG = read_file(os.path.join(FILES_PATH, 'dictionary_wrong.txt'))
NORMS_WORD = read_file(os.path.join(FILES_PATH, 'norms.txt'))
NORMS_WORD_WRONG = read_file(os.path.join(FILES_PATH, 'norms_wrong.txt'))
PARONYMS = []
EXPLANATION = []
with open(os.path.join(FILES_PATH, 'paronyms.txt'), encoding='utf-8') as file:
    for line in file.read().strip().split('###'):
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            paronyms = parts[0].strip().split(' – ')
            explanation = parts[1].split(' – ')
            PARONYMS.append(paronyms)
            EXPLANATION.append(explanation)

        
words = {
    'accents': (ACCENTS_WORD, ACCENTS_WORD_WRONG),
    'dictionary': (DICTIONARY_WORD, DICTIONARY_WORD_WRONG),
    'norms': (NORMS_WORD, NORMS_WORD_WRONG),
    'paronyms': (PARONYMS, EXPLANATION)
}
options_main = {
    'accents': ('📢 <b>Ударения</b>\n 4 задание ЕГЭ'),
    'dictionary': ('✏️ <b>Словарные слова</b>\n 9 задание ЕГЭ'),
    'norms': ('📚 <b>Морф. нормы</b>\n 7 задание ЕГЭ'),
    'GoMain_menu': ('✍️ <b>Егэ русский язык</b>'), 
    'paronyms': ('🎭 <b>Паронимы</b>\n 5 задание ЕГЭ')
}