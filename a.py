import mapedit
import wad
import collections
import sys
from StringIO import StringIO
import json
import base64
import os.path

if len(sys.argv) != 4:
	print "enter filename, iwad, mapname"
	sys.exit(1)

outfile,iwad,mapname = sys.argv[1:]

class WrappedLinedef:
	def __init__(self, vx_a, vx_b):
		self.vx_a = vx_a
		self.vx_b = vx_b

class TextureReader:
	def __init__(self, basepath):
		self.basepath = basepath
	
	def getdata(self, texturename):
		print texturename
		texturedata = base64.b64encode(open(os.path.join(self.basepath, texturename + ".png"), "r").read())
		if texturename == "floor4_8":
			print texturedata
		return "data:image/png;base64," + texturedata

def Map(sectors,texturedata, player1):
	return { "sectors" : sectors, "texturedata" : texturedata, "player1" : player1 }

class DoomExporter:
	def __init__(self,wadfile,mapname,texturereader):
		self.w = wad.WAD(wadfile)
		self.mapentry = self.w.maps[mapname]
		self.texturereader = texturereader

		self.m = mapedit.MapEditor(self.mapentry)
		
		self.export()

	def scalex(self,x):
		return x
	def scaley(self,y):
		return y

	def export(self):
		
		player1 = self.__find_player_start(self.m, 1)
		player1 = [self.scalex(player1[0]), self.scaley(player1[1])]

		textures = self.__gettextures(self.m)
		texturedata = {}
		for texturename in set(textures.values()):
			texturedata[texturename] = self.texturereader.getdata(texturename)

		sectors_linedefs = self.__getlinedefs_per_sector(self.m, self.__getsidedefs_per_sector(self.m))

		for sector,linedefs in sectors_linedefs.iteritems():
			for linedef in LinedefOrder(linedefs):
				vx_a = self.m.vertexes[linedef.vx_a]
				vx_b = self.m.vertexes[linedef.vx_b]

				print "   LINEDEF: %.2f,%.2f -> %.2f,%.2f" % (vx_a.x, vx_a.y, vx_b.x, vx_b.y)

		self.json = '{ "sectors": ['
		sectors = []
		for sector,linedefs in sectors_linedefs.iteritems():
			linedefs = sectors_linedefs[sector]
			points =  [(self.scalex(self.m.vertexes[l.vx_a].x), self.scaley(self.m.vertexes[l.vx_a].y)) for l in ReverseLinedefs(LinedefOrder(linedefs))]
			texture = textures[sector]
			label = "polygon" + str(sector)

			sectors.append({ "points" : points, "texture" : texture, "label" : label })
	
		out = StringIO()
		json.dump(Map(sectors, texturedata, player1), out)
		self.json = out.getvalue()

		#self.json += ",".join([' {"points" : [%s], "texture" : "%s", "label":"%s" }' % (p[0][0],p[1],"polygon"+str(i)) for i,p in enumerate(polygons)])
		#self.json += "]}"



	# create linkage between from sector to sidedef
	def __getsidedefs_per_sector(self, m):

		sectors_sidedefs = collections.defaultdict(list)

		for i,sidedef in enumerate(m.sidedefs):
			sectors_sidedefs[sidedef.sector].append((i,sidedef))
		return sectors_sidedefs

	def __getlinedefs_per_sector(self, m, sectors_sidedefs):
		sectors_linedefs = collections.defaultdict(list)
		for sector,sidedefs in sectors_sidedefs.iteritems():
			sidedefs = sectors_sidedefs[sector]
			for sidedef in sidedefs:
				sectors_linedefs[sector].append(self.__find_linedef_from_sidedef(m.linedefs, sidedef[0]))
		
		return sectors_linedefs

	def __gettextures(self, m):
		textures = {}

		for i,sector in enumerate(m.sectors):
			textures[i] = sector.tx_floor.lower()

		return textures

	def __find_linedef_from_sidedef(self, linedefs, sidedef):
		for linedef in linedefs:
			if linedef.front == sidedef:
				return linedef;
			elif linedef.back == sidedef:
				l = WrappedLinedef(linedef.vx_b, linedef.vx_a)
				return l

	def __find_player_start(self, m, player):
		for thing in m.things:
			if thing.type == player:
				return [thing.x,thing.y]

def LinedefOrder(linedefs):
	
	edge_links_forward = {}
	edge_links_backward = {}

	vertices = [];
	for l in linedefs:
		edge_links_forward[l.vx_a] = l.vx_b
		edge_links_backward[l.vx_b] = l.vx_a
		vertices.append(l.vx_a)
		vertices.append(l.vx_b)

	v = linedefs[0].vx_b
	visited = []

	# Rewind
	while (v in edge_links_backward) and (not v in visited):
		visited.append(v)
		v = edge_links_backward[v]

	end = edge_links_forward[v]
	START = [v,end]
	finished = []
	new_edges = []
	while end != None and not [v,end] in finished:
		new_linedef = WrappedLinedef(v, end)
		finished.append([v,end])

		new_edges.append(new_linedef)
		tmp = end
		v = end
		try:
			end = edge_links_forward[tmp]
		except:
			end = None

	return new_edges

def ReverseLinedefs(linedefs):
	linedefscopy = list(linedefs)
	linedefscopy.reverse()
	reversed_linedefs = []
	for linedef in linedefscopy:
		l = WrappedLinedef(linedef.vx_b, linedef.vx_a)
		reversed_linedefs.append(l)
	return reversed_linedefs

if __name__ == "__main__":
	de = DoomExporter(iwad, mapname, TextureReader("/home/nico.kruger/Downloads/jsdoom"))

	
	print "----------------------------------------------"
	print " JSON "
	print "----------------------------------------------"
	print de.json
	open(outfile,"w").write(de.json)


