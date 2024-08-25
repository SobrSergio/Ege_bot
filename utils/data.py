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

words = {
    'accents': (ACCENTS_WORD, ACCENTS_WORD_WRONG),
    'dictionary': (DICTIONARY_WORD, DICTIONARY_WORD_WRONG),
    'norms': (NORMS_WORD, NORMS_WORD_WRONG)
}

options_main = {
    'accents': ('📢 <b>Ударения</b>\n 4 задание ЕГЭ'),
    'dictionary': ('✏️ <b>Словарные слова</b>\n 9 задание ЕГЭ'),
    'norms': ('📚 <b>Морф. нормы</b>\n 7 задание ЕГЭ'),
    'GoMain_menu': ('✍️ <b>Егэ русский язык</b>')
}