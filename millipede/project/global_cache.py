'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Unicode, String, DateTime, Boolean
import os.path


SQLBase = declarative_base()


class AST(SQLBase):
	__tablename__ = 'ast'
	id = Column(Integer, primary_key=True)
	path = Column(Unicode)
	hash = Column(String(40))
	data = Column(String)


	def __init__(self, path, hash, data):
		super().__init__()
		self.path = path
		self.hash = hash
		self.data = data


class Links(SQLBase):
	__tablename__ = 'ast_imports'
	id = Column(Integer, primary_key=True)
	path = Column(Unicode)
	data = Column(String) # pickled (imports, importfroms, renames)

	def __init__(self, path, data):
		self.path = path
		self.data = data


class GlobalCache:
	def __init__(self, cache_dir):
		self.cache_dir = cache_dir

		self.engine = create_engine('sqlite:///' + os.path.join(os.path.realpath(cache_dir), '__common__') + '.db')
		SQLBase.metadata.create_all(self.engine)
		self.session = sessionmaker(bind=self.engine)()


	def query_ast_data(self, path, hash):
		row = self.session.query(AST).filter_by(path=path, hash=hash).first()
		# NOTE: if our hash updates, then we lose access to the data -- we clear out the existing row
		#		_and_ the matching rows from all dependent structures
		if not row:
			self.session.query(AST).filter_by(path=path).delete()
			self.session.query(Links).filter_by(path=path).delete()
			return None
		return row.data


	def update_ast_data(self, path, hash, data):
		self.session.query(AST).filter_by(path=path).delete()
		row = AST(path, hash, data)
		self.session.add(row)
		self.session.commit()


	def query_file_links(self, path):
		row = self.session.query(Links).filter_by(path=path).first()
		if not row:
			return None
		return row.data


	def update_file_links(self, path, data):
		self.session.add(Links(path, data))
		self.session.commit()


