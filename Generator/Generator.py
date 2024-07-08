from os import walk
from os import path
from os.path import exists
import trie
import json
from collections import OrderedDict
import itertools
import random
import sys

template_name = "template.json"
keyboard_vers = "keyboard_version"
keyboard_keys = "keys"
lesson_vers = "lesson_version"
lesson_lang = "lang"
lesson_name = "lesson.json"
lesson_parts = "parts"
text_ext = ".txt"
json_ext = ".json"
base_dir = "./"
pars_keys = {"#":"Simple", "$":"Shift", "@":"Ctrl", "*":"Alt"}
part_stripe_size = 70
sort_stripe_size = 20
part_stripe_size_arg = "--pss"
sort_stripe_size_arg = "--sss"

def get_res_list(path, is_file = True):
    for (dirpath, dirnames, filenames) in walk(path):
        return filenames if is_file else dirnames
    return []

def find_file_with(dir_path, part_name, part_text = ""):
    for file_name in get_res_list(dir_path):
        if part_name in file_name:
            file_path = path.join(dir_path, file_name)
            if part_text:
                with open(file_path, 'r') as file:
                    if part_text not in file.read():
                        return ""
            return file_path
    return ""

def dir_is_valid_task(dir_path):
    # файла урока нет
    if exists(path.join(dir_path, lesson_name)):
        print(f"Warning! In the directory [{dir_path}] already exist resulting file [{lesson_name}]. Task will be skipped.")
        return False
    # есть файл с клавиатурой
    keyboard_file = find_file_with(dir_path, json_ext, keyboard_vers)
    if keyboard_file:
        if find_file_with(dir_path, text_ext):
            return True
        else:
            print(f"Error! Not exist text file with words in task directory [{dir_path}].")
    else:
        print(f"Error! Not exist keyboard file in task directory [{dir_path}].")
    return False

def load_json(path):
    with open(path) as f:
        _dict = json.load(f)
        if not _dict:
            print(f"Error! Json file [{path}] is broken.")
        return _dict

def save_json(path, dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dict, f, ensure_ascii=False, indent=4)

# заменить символы клавиш на символы локальной клавиатуры
def swith_local(template, keyboard):
    kb_symbs = keyboard[keyboard_keys]
    result = OrderedDict()
    for key in template:
        key_name = ""
        key_mode = ""
        keys = {}
        # проходим по ключу шаблона
        for char in key:
            # нашли символ режима клавиши
            if char in pars_keys:
                # уже записали имя клавиши шаблона
                if key_name:
                    # записываем в промежуточный словарь ключа пары "имя кнопки" - режим.
                    keys[key_name] = pars_keys[char]
                # нашли символ режима - значит пишем новое имя клавиши
                key_name = ""
                # запоминаем режим для последней клавиши в шаблоне ключа
                key_mode = char
            else:
                # записываем имя клавиши из шаблона
                key_name += char
        # сохраним имя последней клавиши из шаблона
        if key_name:
            keys[key_name] = pars_keys[key_mode]
        new_key = ""
        for name in keys:
            symb = kb_symbs[name]
            for switch_key in symb:
                if symb[switch_key] == keys[name]:
                    new_key += switch_key
                    break
        if new_key:
            result[new_key] = template[key]
    return result

# комбинации из символов ключа
def shuffle(key):
    permutations = list(itertools.permutations(list(key)))
    result_list = []
    for char_arr in permutations:
        result_list.append("".join(char_arr))
    return result_list

# выбрать указанное количество рандомных символов из переданной последовательности
def random_list_from(source, count):
    result_list = []
    if source:
        if len(source) < count:
            count = len(source)
        while count > 0:
            random_item = random.choice(source)
            if random_item not in result_list:
                result_list += random_item
                count -= 1
    return result_list

# вставить слова в массив source из символов строки insert_symbols, размером count в случайном месте и в случайном количестве.
def insert_random(source, insert_symbols, count = 1):
    symb_size = len(insert_symbols)
    source_size = len(source)
    if symb_size == 0 or source_size == 0:
        return

    # сколько слов вставляем
    insert_words_count = 1 if source_size < 4 else random.randint(1, int(source_size / 2))
    result_insert = {}
    while insert_words_count:
        result_insert[0 if source_size == 1 else random.randint(0, source_size - 1)] = "".join(random_list_from(insert_symbols, 1 if count == 1 else random.randint(1, count)))
        insert_words_count -= 1

    ind_list = list(result_insert.keys())
    ind_list.sort(reverse=True)
    for index in ind_list:
        source.insert(int(index), result_insert[index])

# отсортировать с приоритетом список переданных слов по ключу.
# key - ключ по которому отбираем слова для приоритетной установки
# words - список строк который будем сортировать
# capit - если символ в ключе в верхнем регистре - Установить в слове первую букву в верхний регистр
def sort_lead_key(key, words = []):
    # работаем со словами в нижнем регистре
    key_low = key.lower()
    # в словарь складываем слова начинающиеся с символа из ключа - вставим их первыми в массиве
    tmp_dict = {}
    for char in key_low:
        tmp_dict[char] = []

    for word in reversed(words):
        if word[0] in tmp_dict:
            # если символ ключа в верхнем регистре - сохранить слово с заглавной буквы
            tmp_dict[word[0]].append(word if word[0].upper() not in key else word.capitalize())
            words.remove(word)

    result = []
    # если списки слов с начинающихся с символа ключа очень большие - подрежем их, иначе в финальный набор могут войти не все слова
    for char in key_low:
        tmp_dict[char][:sort_stripe_size]
        result += tmp_dict[char]
    # перемешаем приоритетные слова, чтобы пользователь не уставал вводить одну и ту же большую букву
    random.shuffle(result)
    return result + words

def from_dict_to_lesson_format(parts_dict, version, kb_lang):
    result = {}
    result[lesson_vers] = version
    result[lesson_lang] = kb_lang
    parts = {}
    n = 1
    for part in parts_dict:
        parts[f'{n:03}_{part}'] = " ".join(parts_dict[part])
        n += 1
    result[lesson_parts] = parts
    return result


def generate():
    global part_stripe_size
    global sort_stripe_size
    for arg in sys.argv[1:]:
        arg_spl = arg.split('=')
        if len(arg_spl) == 2:
            if arg_spl[0] == part_stripe_size_arg and arg_spl[1].isdigit():
                part_stripe_size = int(arg_spl[1])
            if arg_spl[0] == sort_stripe_size_arg and arg_spl[1].isdigit():
                sort_stripe_size = int(arg_spl[1])

    # по умолчанию шаблон урока берём из корня
    template_path = path.join(base_dir, template_name)
    if exists(template_path):
        template = load_json(template_path)
        # директории внутри текущей  - это задачи на генерацию урока содержащие набор необходимых файлов
        dir_list = get_res_list(base_dir, False)
        if len(dir_list) == 0:
            print("Error! No directories with a generating task.")
        else:
            for dir_name in dir_list:
                if dir_name == "__pycache__":
                    continue
                dir_path = path.join(base_dir, dir_name)
                # файлы для генерации урока есть в директории задачи?
                if dir_is_valid_task(dir_path):
                    local_template = template
                    local_template_path = path.join(dir_path, template_name)
                    # если есть локальный файл шаблона используем его
                    if exists(local_template_path):
                        local_template = load_json(local_template_path)
                    print("Run task -> " + dir_name)
                    keyboard_file = find_file_with(dir_path, json_ext, keyboard_vers)
                    kb_dict = load_json(keyboard_file)
                    # из файла клавиатуры извлекаем символы раскладки для локали по указанным клавишам
                    switched_local = swith_local(local_template, kb_dict)
                    # префиксное дерево
                    symb_trie = trie.Trie()
                    symb_trie.add_text_file(find_file_with(dir_path, text_ext))
                    # символы которые были ранее и с которыми можно составлять слова
                    optional_symbs = ""
                    digits = ""
                    punctuation = ""
                    # храним прошлую часть, подставим её если ни одного слова не будет найдено и разбавим символами из ключа
                    part = []
                    for key in switched_local:
                        curr_digits = ""
                        curr_punct = ""

                        for char in key:
                            if char.isalpha():
                                if char.lower() not in optional_symbs:
                                    optional_symbs += char.lower()
                                continue
                            if char.isdigit():
                                digits += char
                                curr_digits += char
                                continue
                            punctuation += char
                            curr_punct += char

                        # перестановки из ключа
                        shuffle_keys = shuffle(key)

                        # если символов меньше трёх перестановок будет мало - дублируем.
                        if len(key) < 4:
                            shuffle_keys += shuffle_keys.copy()

                        # слова из префиксного дерева
                        # опциональных символов будет много, поэтому выбираем только ограниченное количество.
                        part_tmp = list(symb_trie.symbols_search(key, optional_symbs))
                        # отбираем в приоритетном порядке слова начинающиеся с символов из ключа
                        part_tmp = sort_lead_key(key, part_tmp)
                        # в ключе были алфавитные символы
                        if part_tmp:
                            part = part_tmp
                            # добавим цифр из ключа
                            if curr_digits:
                                insert_random(part, curr_digits, 3)
                            # добавим символов пунктуации из ключа
                            if curr_punct:
                                insert_random(part, curr_punct, 1)
                            # добавим цифр предыдущих ключей
                            if digits:
                                insert_random(part, digits, 3)
                            # добавим символов пунктуации из предыдущих ключей
                            if punctuation:
                                insert_random(part, punctuation, 1)
                            # обрежем часть (список слов) до нужной длины
                            part = part[:part_stripe_size]
                        else:
                            # удалим перестановки прошлого ключа
                            #if len(part) >= part_stripe_size:
                             #   part = part[len(shuffle_keys):]
                            # смешаем, чтоб не выглядело одинаково
                            random.shuffle(part)
                            if curr_digits:
                                insert_random(part, curr_digits, 3)
                            if curr_punct:
                                insert_random(part, curr_punct, 1)
                        shuffle_keys += part
                        if len(shuffle_keys) < part_stripe_size:
                            shuffle_keys *= int(part_stripe_size / len(shuffle_keys))


                        switched_local[key] = shuffle_keys
                        print(key, switched_local[key])
                    # сохранить сгенерированный урок в файл на диск
                    save_json(path.join(dir_path, lesson_name), from_dict_to_lesson_format(switched_local, kb_dict[keyboard_vers], path.splitext(path.basename(keyboard_file))[0]))
    else:
        print("Error! Not exists template file in current directory.")
    pass


generate()
