import mapedit
import wad
import collections
import sys

if len(sys.argv) != 2:
	print "enter filename"
	sys.exit(1)

outfile = sys.argv[1]

class WrappedLinedef:
	def __init__(self, vx_a, vx_b):
		self.vx_a = vx_a
		self.vx_b = vx_b

w = wad.WAD("doom.wad")
e1m1 = w.maps['E1M1']


sectors_sidedefs = collections.defaultdict(list)

m = mapedit.MapEditor(e1m1)

[sectors_sidedefs[sidedef.sector].append((i,sidedef)) for i,sidedef in enumerate(m.sidedefs)]

def find_linedef_from_sidedef(linedefs, sidedef):
	for linedef in linedefs:
		if linedef.front == sidedef:
			return linedef;
		elif linedef.back == sidedef:
			l = WrappedLinedef(linedef.vx_b, linedef.vx_a)
			return l
			
	#return [l for l in linedefs if (l.front == sidedef) or (l.back == sidedef)][0]

sectors_linedefs = collections.defaultdict(list)

#[sectors_linedefs[sector].append(find_linedef_from_sidedef(m.linedefs, sidedef[0])) for sidedef in sectors_sidedefs[sector] for sector in sectors_sidedefs.keys()]

[sectors_linedefs[sector].append(find_linedef_from_sidedef(m.linedefs, sidedef[0])) for sector in sectors_sidedefs.keys() for sidedef in sectors_sidedefs[sector]]

def sigh(l, item):
	try:
		l.index(item)
	except:
		return -1

def order_linedefs(linedefs):
	
	edge_links_forward = {}
	edge_links_backward = {}

	vertices = [];
	for l in linedefs:
		edge_links_forward[l.vx_a] = l.vx_b
		edge_links_backward[l.vx_b] = l.vx_a
		vertices.append(l.vx_a)
		vertices.append(l.vx_b)
	
	new_edges = []
	v = linedefs[0].vx_b
	visited = []
	# Rewind
	while (v in edge_links_backward) and (not v in visited):
		visited.append(v)
		v = edge_links_backward[v]
	
	end = edge_links_forward[v]

	finished = []
	while end != None and not end in finished:
		new_linedef = WrappedLinedef(v, end)
		finished.append(v)
		finished.append(end)

		new_edges.append(new_linedef)
		tmp = end
		v = end
		try:
			end = edge_links_forward[tmp]
		except:
			end = None

	return new_edges

for sector,linedefs in sectors_linedefs.iteritems():
	print "SECTOR:", sector
	for linedef in order_linedefs(linedefs):
	#for linedef in linedefs:
		vx_a = m.vertexes[linedef.vx_a]
		vx_b = m.vertexes[linedef.vx_b]

		print "   LINEDEF: %.2f,%.2f -> %.2f,%.2f" % (vx_a.x, vx_a.y, vx_b.x, vx_b.y)


print "----------------------------------------------"
print " JSON "
print "----------------------------------------------"

json = '{ "zones": ['
polygons = []
for sector,linedefs in sectors_linedefs.iteritems():
	points =  ",".join(["[%.2f,%.2f]" % (m.vertexes[l.vx_a].x/4.0 + 100, m.vertexes[l.vx_a].y/4.0 + 1200) for l in order_linedefs(linedefs)]),
	polygons.append(points)

json += ",".join([' {"points" : [%s], "pops" : [0], "texture" : "name", "label":"a" }' % (p) for p in polygons[:1]])

	#print ", $V($.2f,%.2f)" % (m.vertexes[order_linedefs(linedefs)[-1].vx_b].x, m.vertexes[order_linedefs(linedefs)[-1].vx_b].y),
json += "]}"
print json

open(outfile,"w").write(json)
