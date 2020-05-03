import argparse
import sys
import re

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def eexit(*args, **kwargs):
	eprint("Error:",*args, **kwargs)
	exit(-1)

buf = []
def getc():
	global buf
	if len(buf)>0:
		return buf.pop()
	else:
		c = sys.stdin.read(1)
		if len(c)==0:
			return -1
		else:
			return ord(c)

def ungetc(c):
	global buf
	buf.append(c)

class Any: pass
	
class Num(Any):
	def __init__(self,n):
		self.v = int(n)
	def subst(self,fr,to):
		return self

class Id(Any):
	def __init__(self,s):
		self.v = s
	def subst(self,fr,to):
		for d,e in zip(fr,to):
			if d == self.v:
				return e
		return self

class FunBody:
	def __init__(self,argnum,apply,subst):
		self.argnum = argnum
		self.apply = apply
		self.subst = subst

class Fundef(Any):
	def __init__(self,name,args,body):
		self.name = name
		self.args = args
		self.body = body
		
		def apply(vs):
			return [d.subst(self.args,vs) for d in self.body]
		
		def subst(fr,to):
			tobody = [d.subst(fr,to) for d in self.body]
			return Fundef(self.args,tobody)
			
		self.definition = FunBody(len(self.args),apply,subst)

def builtin_functions():
	env = {}
	def register_builtin(name,argtypes,fun):
		def apply(args):
			assert (len(args) == len(argtypes))
			for v,t in zip(args,argtypes):
				if not isinstance(v,t):
					eexit("'%s' expects %s, got %s" % (name,"".join(map(str,argtypes)), "".join(map(str,map(type,args)))))
			return fun(args)
			
		body = FunBody(len(argtypes),apply,lambda _: ())
		body.subst = lambda _: body
		env[name] = body
	
	register_builtin('+',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v + xs[1].v)])
	register_builtin('-',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v - xs[1].v)])
	register_builtin('*',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v * xs[1].v)])
	register_builtin('/',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v // xs[1].v)])
	
	def out(v):
		sys.stdout.write(v)
		sys.stdout.flush()
		return []
	register_builtin('oc',[Num],lambda xs: out(chr(xs[0].v)))
	register_builtin('od',[Num],lambda xs: out(str(xs[0].v)))
	
	def inputchar(xs):
		return [xs[0],Num(getc())]
	
	def inputint(xs):
		i = 0
		while True:
			c = getc()
			if ord('0') <= c and c <= ord('9'):
				i = i * 10 + c - ord('0')
			else:
				ungetc(c)
				break
		return [xs[0],Num(i)]
	
	register_builtin('ic',[Any],inputchar)
	register_builtin('id',[Any],inputint)
	
	register_builtin('?',[Num,Any,Any],lambda xs: [xs[1] if xs[0].v != 0 else xs[2]])
	
	register_builtin('@',[Num],lambda xs: exit(xs[0].v))
	
	return env

def tokenize(s):
	res = []
	while s != '':
		m = re.match(r"([0-9A-Za-z]+|\+|-|\*|/|@|\?|\(|\)|\{|\}|\s)",s)
		if m is None:
			eexit("tokenize error:",s)
		res.append(m.group(1))
		s = s[m.end():]
	
	res = list(filter(lambda x: re.match(r'^\s$',x) is None,res))
	return res


def checkparse(s,p):
	if len(s)==0:
		eexit('parse error: expected %s got nothing' % p)
	if re.match(r'^' + p + r'$',s[0]):
		return s[0],s[1:]
	else:
		eexit('parse error: expected %s got %s' % (p,s[0]))

def head(s):
	if len(s)<=0:
		return None
	return s[0]

def parse_fundef(s):
	assert (len(s) >= 1)
	f = s[0]
	s = s[1:]
	_,s = checkparse(s,r'\(')
	
	args = []
	if head(s) == ')':
		pass
	else:
		v,s = checkparse(s,r"[0-9A-Za-z]+")
		args = [v]
		while head(s) != ')':
			_,s = checkparse(s,r",")
			v,s = checkparse(s,r"[0-9A-Za-z]+")
			if v in args:
				eexit('parse error: argument %s of function %s colide' % (v,f))
			args.append(v)
	_,s = checkparse(s,r'\)')
	
	_,s = checkparse(s,r'\{')
	body,s = parse(s)
	_,s = checkparse(s,r'\}')
	
	return (f,args,body),s
		
	
	

def parse(s):
	res = []
	while s != []:
		h = s[0]
		if re.match(r"^[0-9]+$",h):
			res.append(Num(int(h)))
			s = s[1:]
		elif re.match(r"^[0-9A-Za-z]+$",h):
			if len(s) >= 2 and s[1] == '(':
				(f,args,body),s = parse_fundef(s)
				res.append(Fundef(f,args,body))
			else:
				res.append(Id(h))
				s = s[1:]
		elif re.match(r"^(\+|-|\*|/|@|\?)$",h):
			res.append(Id(h))
			s = s[1:]
		elif h == '}':
			break
		else:
			eexit("parse failure unexpected token:",s)
	
	return res,s

def interpret(stack,debug):
	env = builtin_functions()
	while True:
		if len(stack) == 0:
			eexit("stack is empty")
		
		op = stack[0]
		stack = stack[1:]
		if isinstance(op,Num):
			eexit("Num can't be applied")
		elif isinstance(op,Id):
			if not op.v in env.keys():
				eexit("undefined function %s" % op.v)
			
			f = env[op.v]
			if f.argnum > len(stack):
				eexit("insufficient arguments for function %s. Expected %d, got %d" % (op.v,f.argnum,len(stack)))
			
			args = stack[:f.argnum]
			stack = f.apply(args) + stack[f.argnum:]
		elif isinstance(op,Fundef):
			env[op.name] = op.definition
		else:
			assert False
			
	

if __name__=='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('filename', help='the name of the source code file')
	parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='output debug string')

	args = parser.parse_args()
	code = open(args.filename,'r').read()
	program,rem = parse(tokenize(code))
	if len(rem) != 0:
		eexit('parse failure: token remains',rem) 
	interpret(program,args.debug)
	
