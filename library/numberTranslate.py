character_relation = {
    '零': 0,
    '一': 1,
    '二': 2,
    '两': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
    '十': 10,
    '百': 100,
    '千': 1000,
    '万': 10000,
    '亿': 100000000
}
start_symbol = ['一', '二', '两', '三', '四', '五', '六', '七', '八', '九', '十']
more_symbol = list(character_relation.keys())


def chinese_to_digits_in_sentence(sentence: str):
    symbol_str = ''
    found = False
    for item in sentence:
        if item in start_symbol:
            if not found:
                found = True
            symbol_str += item
        else:
            if found:
                if item in more_symbol:
                    symbol_str += item
                    continue
                else:
                    digits = str(chinese_to_digits(symbol_str))
                    sentence = sentence.replace(symbol_str, digits, 1)
                    symbol_str = ''
                    found = False

    if symbol_str:
        digits = str(chinese_to_digits(symbol_str))
        sentence = sentence.replace(symbol_str, digits, 1)

    return sentence


def chinese_to_digits(chinese: str):
    total = 0
    r = 1
    for i in range(len(chinese) - 1, -1, -1):
        val = character_relation[chinese[i]]
        if val >= 10 and i == 0:
            if val > r:
                r = val
                total = total + val
            else:
                r = r * val
                # total = total + r * x
        elif val >= 10:
            if val > r:
                r = val
            else:
                r = r * val
        else:
            total = total + r * val
    return total
