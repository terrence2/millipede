'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
import melano.py.ast as py


class BasicBlock:
	'''A node in a control flow graph.  Tracks accesses and overrides to names so that we can compute
		dominators for names in order to emit better code.
	'''
	def __init__(self, label, *parents):
		super().__init__()

		# descriptive - used only to print the graph
		self.label = label

		# links -- e.g. the control flow
		self.parents = list(parents)
		self.children = []

		# the list of name accesses in this block
		self.actions = []

		# set true for the starting node in the cfg -- used to check that we are not starting our 
		#		graph processing in the wrong place.
		self.is_head = False

		# set true for the ending node in the cfg -- used to check that we are not starting our 
		#		graph processing in the wrong place.
		self.is_tail = False

		# set true for blocks that represent an exception handler -- e.g. that an exception did occur in some
		#		block that is a parent of the exception handling block.  This invalidates any liveout from a preceding
		#		node because those statements may not have been reached.  (Obviously if an exception occurs, but
		#		does not land in an exception handler then we don't have to worry about executing code that depends
		#		on references in the preceeding blocks, because we won't be running code -- the exception will have
		#		caused us to exit.)
		self.is_exception_block = False

		# This set contains all variables stored to in this block.
		self.varkill = set()

		# This set contains all "upwards exposed" variables -- those loaded in this block before they are 
		#		stored to in this block.  
		self.uevar = set()

		# This set contains the liveout variables from all parent nodes.
		# A variable v is live at point p iff there is a path from p to a use of v along which v is not redefined.
		self.liveout = set()

		# Names that are assigned to already on entry into this basic block from _every_ path.
		self.varavail = set()


	def add_action(self, action_type, value):
		self.actions.append((action_type, value))


	def analyze(self):
		assert self.is_head

		self._compute_local(set())


	def _compute_local(self, visited):
		if id(self) in visited: return
		visited.add(id(self))

		for ty, value in self.actions:
			if ty == py.Load:
				if value not in self.varkill:
					self.uevar.add(value)

			if ty == py.Store:
				self.varkill.add(value)

		for child in self.children:
			child._compute_local(visited)


	def show(self, fp, lvl=0, visited=None):
		if not visited: visited = set()
		if id(self) in visited: return
		visited.add(id(self))

		pad = '\t' * lvl
		fp.write(pad + 'BB {} ({})\n'.format(self.label, id(self)))

		fp.write(pad + '-----\n')
		fp.write(pad + 'actions:' + '\n')
		for action in self.actions:
			fp.write(pad + '\t' + '* {} {}\n'.format(*action))

		fp.write(pad + 'varkill:' + '\n')
		for val in self.varkill:
			fp.write(pad + '\t* ' + str(val) + '\n')

		fp.write(pad + 'uevar:' + '\n')
		for val in self.uevar:
			fp.write(pad + '\t* ' + str(val) + '\n')
		fp.write(pad + '-----\n')

		for child in self.children:
			child.show(fp, lvl + 1, visited)


	@classmethod
	def show_gdf(cls, fp, cfg):
		fp.write('nodedef>name INTEGER, label VARCHAR\n')
		visited = set()
		cfg._show_gdf_nodes(fp, visited)

		fp.write('edgedef>node1 INTEGER, node2 INTEGER\n')
		visited = set()
		cfg._show_gdf_edges(fp, visited)


	def _show_gdf_nodes(self, fp, visited):
		if id(self) in visited: return
		visited.add(id(self))
		fp.write('{}, {}\n'.format(id(self), self.label.replace(',', '.')))
		for child in self.children:
			child._show_gdf_nodes(fp, visited)

	def _show_gdf_edges(self, fp, visited):
		if id(self) in visited: return
		visited.add(id(self))
		for child in self.children:
			fp.write('{}, {}\n'.format(id(self), id(child)))
		for child in self.children:
			child._show_gdf_edges(fp, visited)


class BuiltinBlock(BasicBlock):
	'''An opaque basic block.'''
