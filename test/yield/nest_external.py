from tokenize import _tokenize

POS = 0
SRC = ['\n', 'if True:\n', '\tprint("True")\n', '\n']
def _rl():
	global POS, SRC
	out = SRC[POS] if POS < len(SRC) else ''
	POS += 1
	return out


class PythonTokenizer:
	def tokenize(self, source:str) -> list:
		tokens = list(self.token_iter(_rl))
		return tokens

	def token_iter(self, readline):
		tokiter = _tokenize(readline, None)
		out = []
		for tok in tokiter:
			out.append(tok)
		for tok in out:
			yield tok


pt = PythonTokenizer()
toks = pt.tokenize('')
