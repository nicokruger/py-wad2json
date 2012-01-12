import wad
import mapedit
import struct
import collections
import sys


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


class GlNodeParser:
    SHORT_SIZE = 2
    LONG_SIZE = 4

    def __init__(self, vertex_data, segs_data, ssect_data, nodes_data, map):
        self.vertex_data = vertex_data
        self.vertex_index = 0
        self.segs_data = segs_data
        self.segs_index = 0
        self.ssect_data = ssect_data
        self.ssect_index = 0
        self.nodes_data = nodes_data
        self.nodes_index = 0

        #version = vertex_data[:4]
        #if version != "gNd2":
        #    print "invalid version", version
        #    sys.exit(1)
        #self.vertex_index = 2

        self.vertices = [self._get_vertex() for i in range(len(self.vertex_data[self.vertex_index:]) / (2 * 2))]

        self.gl_vertex_offset = len(map.vertexes)

        for v in self.vertices:
            map.vertexes.append(v)

        self.segs = [self._get_seg() for i in range(len(self.segs_data) / (2 * 5))]
        self.ssectors = [self._get_ssector() for i in range(len(self.ssect_data) / (2 * 2))]

        map.segs = self.segs
        map.ssectors = self.ssectors

        np = NodeParser(self.nodes_data)
        self.nodes = np.nodes

    def _get_vertex(self):
        x, y = struct.unpack("=hh", self.vertex_data[self.vertex_index:self.vertex_index + 2 * 2])
        self.vertex_index += 2 * 2
        v = collections.namedtuple("vertex", ["x", "y"])
        v.x = x
        v.y = y
        return v

    def _get_seg(self):
        bit = 32768
        vx_a, vx_b, linedef, side, partner_seg = struct.unpack("=HHHHH", self.segs_data[self.segs_index:self.segs_index + 2 * 5])
        if vx_a & bit == bit:  # it is a gl vertex
            vx_a = self.gl_vertex_offset + (vx_a ^ bit)
        if vx_b & bit == bit:  # it is a gl vertex
            vx_b = self.gl_vertex_offset + (vx_b ^ bit)
        self.segs_index += 2 * 5
        seg = collections.namedtuple("seg", ["vx_a", "vx_b", "line", "side", "partner_seg"])
        seg.vx_a = vx_a
        seg.vx_b = vx_b
        seg.line = linedef
        seg.side = side
        seg.partner_seg = partner_seg
        return seg

    def _get_ssector(self):
        count, first_seg = struct.unpack("=HH", self.ssect_data[self.ssect_index:self.ssect_index + 2 * 2])
        self.ssect_index += 2 * 2
        ssector = collections.namedtuple("ssector", ["numsegs", "seg_a"])
        ssector.numsegs = count
        ssector.seg_a = first_seg
        return ssector


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


def nodes(wadfile, mapname, map):
    w = wad.WAD(wadfile)
    if (hasattr(w, "glmaps")) and "GL_" + mapname in w.glmaps:
        print "Using GLbsp nodes"
        glnodes = w.glmaps["GL_" + mapname]
        nodeparser = GlNodeParser(glnodes["GL_VERT"].data, glnodes["GL_SEGS"].data, glnodes["GL_SSECT"].data, glnodes["GL_NODES"].data, map)
        return Node(nodeparser, nodeparser.nodes[len(nodeparser.nodes) - 1])
    else:
        mapentry = w.maps[mapname]
        m = mapedit.MapEditor(mapentry)
        nodeparser = NodeParser(m.nodes.data)
        return Node(nodeparser, nodeparser.nodes[len(nodeparser.nodes) - 1])
