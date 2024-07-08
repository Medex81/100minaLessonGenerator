from collections import defaultdict
import re
import pickle
from os import path
import atexit

class Trie:
    """
    Implement a trie with insert, search, and startsWith methods.
    """
    min_word_size = 2
    _dump_path = ""
    _is_load_dump = False

    def __init__(self):
        atexit.register(self.cleanup)
        self.root = defaultdict()

    def cleanup(self):
        self.save_to_disk()


    # @param {string} word
    # @return {void}
    # Inserts a word into the trie.
    def insert(self, word):
        current = self.root
        for letter in word:
            current = current.setdefault(letter, {})
        current.setdefault("_end")

    # @param {string} word
    # @return {boolean}
    # Returns if the word is in the trie.
    def search_word(self, word):
        current = self.root
        for letter in word:
            if letter not in current:
                return False
            current = current[letter]
        if "_end" in current:
            return True
        return False

    def symbols_search(self, symbols, optional_symbols = ""):
        words = []
        self.search_words_by_symbols(symbols.lower(), optional_symbols, self.root, words)
        return set(words)

    def search_words_by_symbols(self, symbols, optional_symbols, current, words, accum = ""):
        for letter in symbols:
            if letter in current:
                accum += letter
                accum = self.search_words_by_symbols(symbols, optional_symbols, current[letter], words, accum)

        if "_end" in current:
            for symb in symbols:
                if symb in accum:
                    words.append(accum)
                    break
        else:
            for letter in optional_symbols:
                if letter in current and letter not in symbols:
                    accum += letter
                    accum = self.search_words_by_symbols(symbols, optional_symbols, current[letter], words, accum)

        accum = accum[:-1]
        return accum

    # @param {string} prefix
    # @return {boolean}
    # Returns if there is any word in the trie
    # that starts with the given prefix.
    def startsWith(self, prefix):
        current = self.root
        for letter in prefix:
            if letter not in current:
                return False
            current = current[letter]
        return True

    def add_text_file(self, file_path):
        self._dump_path = path.join(path.dirname(file_path), "dump.pkl")
        if path.isfile(self._dump_path):
            self.load_from_disk()
            self._is_load_dump = True
            return True
        added_words_count = 0
        with open(file_path, 'r') as file:
            print("Preprocess text...")
            text = re.findall(r"[\w']+", file.read().lower())
            text = set(text)
            print("Adding words to trie...")
            for word in text:
                if len(word) < self.min_word_size or word.count(word[0]) == len(word):
                    continue
                self.insert(word)
                added_words_count += 1
        print("insert words -> ", added_words_count)
        if added_words_count > 0:
            return True
        return False

    def save_to_disk(self):
        if self._is_load_dump:
            return
        if self._dump_path:
            with open(self._dump_path, "wb") as file:
                pickle.dump(self.root, file)
                print(f"Save trie dump to {self._dump_path}")
        else:
            print("Error! Trie path is empty. Call add_text_file method first.")

    def load_from_disk(self):
        with open(self._dump_path, "rb") as file:
            self.root = pickle.load(file)
            print(f"Loaded trie dump from {self._dump_path}")
