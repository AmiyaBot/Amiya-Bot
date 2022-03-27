from core.util import remove_punctuation, chinese_to_digits, text_to_pinyin, cut_by_jieba
from core.builtin.message import Message


def text_convert(msg: Message, origin, initial):
    """
    消息文本的最终处理

    :param msg:     Message 对象
    :param origin:  预处理消息文本
    :param initial: 未经预处理的原始消息文本
    :return:        Message 对象
    """
    msg.text = remove_punctuation(origin)
    msg.text_digits = chinese_to_digits(msg.text)
    msg.text_origin = origin
    msg.text_initial = initial

    chars = cut_by_jieba(msg.text) + cut_by_jieba(msg.text_digits)

    words = list(set(chars))
    words = sorted(words, key=chars.index)

    msg.text_cut = words
    msg.text_cut_pinyin = [text_to_pinyin(char) for char in words]

    return msg
