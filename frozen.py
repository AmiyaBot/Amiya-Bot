import sys
import jieba

if hasattr(sys, 'frozen'):
    jieba.set_dictionary('./dict.txt')
