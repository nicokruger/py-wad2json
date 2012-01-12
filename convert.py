import mapedit
import wad
import collections
import sys
from StringIO import StringIO
import json
import base64
import os.path

import nodes

if len(sys.argv) != 4:
    print "enter filename, iwad, mapname"
    sys.exit(1)

outfile,iwad,mapname = sys.argv[1:]


class DoomExporter:
    def __init__(self,wadfile,mapname,texturereader):
        print "wadfile",wadfile
        self.w = wad.WAD(wadfile)
        self.mapentry = self.w.maps[mapname]
        self.texturereader = texturereader

        m = mapedit.MapEditor(self.mapentry)
        self.m = collections.namedtuple("doom_map", ["sectors", "linedefs", "segs", "ssectors", "sidedefs", "vertexes", "things"])
        self.m.sectors = m.sectors
        self.m.linedefs = m.linedefs
        self.m.segs = m.segs
        self.m.ssectors = m.ssectors
        self.m.sidedefs = m.sidedefs
        self.m.vertexes = m.vertexes
        self.m.things = m.things
        
        self.nodes = nodes.nodes(wadfile, mapname, self.m)
        #self.nodes = None
        self.export()

        for thing in self.m.things:
            if thing.type == 1:
                player1 = [thing.x, thing.y]
        
        map = {
            "sectors" : self.sectors, 
            "vertices" : list(self.vertices),
            "sidedefs" : self.sidedefs,
            "linedefs" : self.linedefs,
            "ssectors" : self.ssectors,
            "segs" : self.segs,
            "doom_ssectors" : self.doom_ssectors,
            "texturedata" : [], #self.texturedata, 
            "player1" : player1, 
            "extents":self.extents
        }
        map["nodes"] = self.nodes
        
        print json.dumps(map, sort_keys=True, indent=4)
        self.json = json.dumps(map, sort_keys=True, indent=4)

    def export(self):

        self.textures = self.__gettextures(self.m)

        self.sectors = [{"z_ceil": s.z_ceil, "z_floor":s.z_floor, "light":s.light} for s in self.m.sectors]
        self.linedefs = [{"vx_a" : l.vx_a, "vx_b" : l.vx_b, "right":l.front, "left":l.back} for l in self.m.linedefs]
        self.vertices = [{"x":v.x, "y":v.y} for v in self.m.vertexes]
        self.sidedefs = [{"sector":s.sector} for s in self.m.sidedefs]
        self.segs = 	[{"vx_a":seg.vx_a,"vx_b":seg.vx_b,"line":seg.line,"side":seg.side} for seg in self.m.segs]
        self.doom_ssectors = [{"seg_a":ssector.seg_a,"numsegs":ssector.numsegs} for ssector in self.m.ssectors]
        
        self.ssector_to_sector = [self.get_seg_sector(self.m.segs[ssector.seg_a:ssector.seg_a+ssector.numsegs]) for ssector in self.m.ssectors]
        self.ssectors = []
        for i,ssector in enumerate(self.m.ssectors):
            s = {}
            s["segs"] = [{"vx_a":seg.vx_a, "vx_b":seg.vx_b,"line":seg.line,"side":seg.side} for seg in self.m.segs[ssector.seg_a:ssector.seg_a+ssector.numsegs]]
            s["sector"] = self.ssector_to_sector[i]
            self.ssectors.append(s)
        
        self.texturedata = {}
        for texturename in set(self.textures.values()):
            print "TEX---",texturename
            self.texturedata[texturename] = self.texturereader.getdata(texturename)
    
        self.extents = {
            "x1":min([v.x for v in self.m.vertexes]), 
            "x2":max([v.x for v in self.m.vertexes]), 
            "y1":min([v.y for v in self.m.vertexes]),
            "y2":max([v.y for v in self.m.vertexes]),
        }

        #out = StringIO()
        print "extents",self.extents
        

    def _a(self, line,side): # python2 lambdas are really restrictive, so have to have this function
        if side == 0:
            print line
            return self.m.sidedefs[self.m.linedefs[line].front].sector 
        elif side == 1:
            return self.m.sidedefs[self.m.linedefs[line].back].sector
        raise "what does side %i mean?" % side
        
    def get_seg_sector(self,segs):
        # find the first one that is not 65536 - special glbsp node
        for s in segs:
            if s != 65535:
                return self._a(s.line,s.side)

        raise "seg doesn't have a sector!"
        
    def __gettextures(self, m):
        textures = {}

        a = 0
        for sector in m.sectors:
            for texture in texture_finder(sector.tx_floor.lower()):
                textures[a] = texture
                a+=1

        return textures




class WrappedLinedef:
    def __init__(self, vx_a, vx_b):
        self.vx_a = vx_a
        self.vx_b = vx_b

def texture_finder(texture):
    animated_textures = [
        ["NUKAGE1", "NUKAGE2", "NUKAGE3"],
        ["FWATER1", "FWATER2", "FWATER3","FWATER4"],
        ["SWATER1", "SWATER2", "SWATER3", "SWATER4"],
        ["LAVA1", "LAVA2", "LAVA3", "LAVA4"],
        ["BLOOD1", "BLOOD2", "BLOOD3"],
        ["RROCK05", "RROCK06", "RROCK07", "RROCK08"],
        ["SLIME01", "SLIME02", "SLIME03", "SLIME04"],
        ["SLIME05", "SLIME06", "SLIME07", "SLIME08"],
        ["SLIME09", "SLIME10", "SLIME11", "SLIME12"]
    ]
    try:
        return [x.lower() for x in filter(lambda x: texture.upper() in x, animated_textures)[0]]
    except IndexError:
        return [texture]
    


class TextureReader:
    def __init__(self, basepath):
        self.basepath = basepath
    
    def getdata(self, texturename):
        texturedata = base64.b64encode(open(os.path.join(self.basepath, texturename + ".png"), "r").read())
        return "data:image/png;base64," + texturedata

def Map(texturedata, player1, extents, sectors, vertexes, linedefs, sidedefs, ssectors):
    return { 
        "sectors" : sectors, 
        "vertexes" : vertexes,
        "sidedefs" : sidedefs,
        "linedefs" : linedefs,
        "ssectors" : ssectors,
        "texturedata" : texturedata, 
        "player1" : player1, 
        "extents":extents 
    }

    
if __name__ == "__main__":
    
    de = DoomExporter(iwad, mapname, TextureReader("/home/nicok/Downloads/jsdoom"))

    
    print "----------------------------------------------"
    print " WROTE "
    print "----------------------------------------------"

    print "%i vertices" % (len(de.vertices))
    print "%i linedefs" % (len(de.linedefs))
    print "%i sidedefs" % (len(de.sidedefs))
    print "%i ssectors" % (len(de.ssectors))
    print "%i sectors" % (len(de.sectors))
    print "%i nodes" % (len(de.nodes))
    open(outfile,"w").write(de.json)


