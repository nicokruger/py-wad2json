import wad
import mapedit
import struct
import collections


class NodeParser:
    SHORT_SIZE = 2
    LONG_SIZE = 4

    def __init__(self, data):
        self.data = data
        self.index = 0
        self.nodes = [self.__get_node() for i in range(len(self.data) / 28)]

    def __get_node(self):
        o = collections.namedtuple("node", ["partition", "rightBB", "leftBB", "right", "left"])
        o.partition = self.get_line()
        o.rightBB = self.get_bb()
        o.leftBB = self.get_bb()
        o.right = self.get_short()
        o.left = self.get_short()
        return o

    def get_line(self):
        x, y, dx, dy = struct.unpack("=hhhh", self.data[self.index:self.index + self.SHORT_SIZE * 4])
        self.index += self.SHORT_SIZE * 4
        return x, y, dx, dy

    def get_bb(self):
        y2, y1, x1, x2 = struct.unpack("=hhhh", self.data[self.index:self.index + self.SHORT_SIZE * 4])
        self.index += self.SHORT_SIZE * 4
        return x1, y1, x2, y2

    def get_short(self):
        i = struct.unpack("=H", self.data[self.index:self.index + self.SHORT_SIZE])
        self.index += self.SHORT_SIZE
        return i[0]

    def peek_short(self):
        i = struct.unpack("=H", self.data[self.index:self.index + self.SHORT_SIZE])
        return i[0]


def Node(nodeparser, node):
    bit = 32768
    right = node.right
    left = node.left
    if right & bit != 0:
        right = right ^ bit
    else:
        right = Node(nodeparser, nodeparser.nodes[right])

    if left & bit != 0:
        left = left ^ bit
    else:
        left = Node(nodeparser, nodeparser.nodes[left])

    return {
        "partition": node.partition,
        "rightBB": node.rightBB,
        "leftBB": node.leftBB,
        "right": right,
        "left": left
    }


def nodes(wadfile, map):
    w = wad.WAD(wadfile)
    mapentry = w.maps[map]
    m = mapedit.MapEditor(mapentry)
    nodeparser = NodeParser(m.nodes.data)
    return Node(nodeparser, nodeparser.nodes[len(nodeparser.nodes) - 1])
