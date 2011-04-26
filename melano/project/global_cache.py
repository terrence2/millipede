'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, Unicode, String, DateTime, Boolean
import os.path


SQLBase = declarative_base()


class AST(SQLBase):
	__tablename__ = 'ast'
	id = Column(Integer, primary_key=True)
	path = Column(Unicode)
	hash = Column(String(40))
	data = Column(String)
	data_has_index = Column(Boolean)


	def __init__(self, path, hash, data):
		self.path = path
		self.hash = hash
		self.data = data



class GlobalCache:
	def __init__(self, cache_dir):
		self.cache_dir = cache_dir

		self.engine = create_engine('sqlite:///' + os.path.join(os.path.realpath(cache_dir), '__common__') + '.db')
		SQLBase.metadata.create_all(self.engine)
		self.session = sessionmaker(bind=self.engine)()


	def query_ast_data(self, path, hash):
		row = self.session.query(AST).filter_by(path=path, hash=hash).first()
		if row:
			return row.data


	def update_ast_data(self, path, hash, data):
		self.session.query(AST).filter_by(path=path).delete()
		row = AST(path, hash, data)
		self.session.add(row)
		self.session.commit()


	def query_file_links(self, path):
		return None, None

	def update_file_links(self, path, imports, importfroms):
		pass
