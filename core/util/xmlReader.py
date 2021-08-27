from xml.dom.minidom import Element, Text, parse


class XMLReader:
    def __init__(self, path):
        self.tree = parse(path)

    def to_json(self):
        return self.__init_self_data(self.tree.documentElement)

    def __init_self_data(self, node):
        data = self.__get_attributes(node)
        nodes = self.__elements(node.childNodes)
        if type(nodes) in [str, int, bool]:
            if not data:
                return ''.join([n.strip() for n in nodes.split('\n')]) if type(nodes) is str else nodes
            data['nodeText'] = nodes
        elif type(data) is dict:
            data.update(
                self.__init_child_data(nodes)
            )
            data = data if data != {} else ''
        return data

    def __init_child_data(self, nodes):
        data = self.__check_node_type(nodes)
        for node in nodes:
            if node.tagName in data:
                if type(data[node.tagName]) is list:
                    data[node.tagName].append(self.__init_self_data(node))
                else:
                    data[node.tagName] = self.__init_self_data(node)
        return data

    def __get_attributes(self, node):
        attrs = {}
        for key in node.attributes.keys():
            attr = node.attributes[key]
            attrs[attr.name] = self.__trans_type(attr.value)
        return attrs

    def __elements(self, node):
        nodes = []
        node_text = ''

        for item in node:
            if type(item) is Element:
                nodes.append(item)
            if type(item) is Text:
                node_text = self.__clean_symbol(item.data)

        if node_text != '':
            return self.__trans_type(node_text)
        return nodes

    @staticmethod
    def __clean_symbol(text):
        return text.strip('\n\t ')

    @staticmethod
    def __check_node_type(nodes):
        nodes_type = {}
        for node in nodes:
            if node.tagName not in nodes_type:
                nodes_type[node.tagName] = {}
            else:
                nodes_type[node.tagName] = []
        return nodes_type

    @staticmethod
    def __trans_type(text: str):
        text = text.strip(' ')

        if text.isdigit():
            return int(text)

        if text.lower() in ['false', 'true']:
            return text.lower() == 'true'

        return text


def read_xml(path):
    return XMLReader(path).to_json()
