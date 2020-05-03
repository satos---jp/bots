import argparse
import sys
import re

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def eexit(*args, **kwargs):
	eprint("Error:",*args, **kwargs)
	exit(-1)

class Any: pass

class Num(Any):
	def __init__(self,n):
		self.v = int(n)
	def subst(self,fr,to):
		return self
	def __str__(self):
		return str(self.v)

class Id(Any):
	def __init__(self,s):
		self.v = s
	def subst(self,fr,to):
		for d,e in zip(fr,to):
			if d == self.v:
				return e
		return self
	def __str__(self):
		return self.v

class FunBody:
	def __init__(self,argnum,apply,reprstr=None):
		self.argnum = argnum
		self.apply = apply
		self.reprstr = reprstr
		self.is_builtin = reprstr is None
	def __str__(self):
		return self.reprstr

class Fundef(Any):
	def __init__(self,name,args,body):
		self.name = name
		self.args = args
		self.body = body
		self.reprstr = "(%s){ %s }" % (",".join(self.args)," ".join(map(str,self.body)))
		
		def apply(vs):
			return [d.subst(self.args,vs) for d in self.body]
		
		self.definition = FunBody(len(self.args),apply,self.reprstr)

	def subst(self,fr,to):
		tobody = [d.subst(fr,to) for d in self.body]
		return Fundef(self.name,self.args,tobody)
	
	def __str__(self):
		return "%s%s" % (self.name,self.reprstr)

class Exit(Exception):
	def __init__(self,v):
		self.v = v

def types2str(vs):
	return ";".join(map(lambda x: x.__name__,vs))

def builtin_functions():
	env = {}
	def register_builtin(name,argtypes,fun):
		def apply(args):
			assert (len(args) == len(argtypes))
			for v,t in zip(args,argtypes):
				if not isinstance(v,t):
					eexit("'%s' expects [%s], got [%s] of type [%s]" % 
						(name,types2str(argtypes),";".join(map(str,args)), types2str(map(type,args))))
			return fun(args)
			
		env[name] = FunBody(len(argtypes), apply)
	
	register_builtin('+',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v + xs[1].v)])
	register_builtin('-',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v - xs[1].v)])
	register_builtin('*',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v * xs[1].v)])
	register_builtin('/',[Num,Num,Any],lambda xs: [xs[2], Num(xs[0].v // xs[1].v)])
	
	def out(v):
		puts(v)
		return []
	register_builtin('oc',[Num],lambda xs: out(b"%c" % xs[0].v))
	register_builtin('od',[Num],lambda xs: out(b"%d" % xs[0].v))
	
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
	
	def raiseexit(xs):
		raise Exit(xs[0].v)
	
	register_builtin('@',[Num],raiseexit)
	
	return env

def tokenize(s):
	res = []
	while s != '':
		m = re.match(r"([0-9A-Za-z]+|\+|-|\*|/|@|\?|\(|,|\)|\{|\}|\s|#s|#e)",s)
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
		elif re.match(r"^(\+|-|\*|/|@|\?|#s|#e)$",h):
			res.append(Id(h))
			s = s[1:]
		elif h == '}':
			break
		else:
			eexit("parse failure unexpected token:",s)
	
	return res,s

class Defaultargs:
	def __init__(self):
		self.debug = self.debugstack = self.debugenv = False
	
def interpret(stack,debugargs=Defaultargs()):
	env = builtin_functions()
	
	def show_stack():
		eprint("stack:"," ".join(map(str,stack)))
	
	def show_env():
		eprint("env:")
		for k,v in env.items():
			if not v.is_builtin:
				eprint("\t%s ::= %s" % (k,str(v)))		
	
	try:
		while True:
			if debugargs.debug or debugargs.debugstack:
				show_stack()
			
			if debugargs.debug or debugargs.debugenv:
				show_env()

			if len(stack) == 0:
				eexit("stack is empty")
			
			op = stack[0]
			stack = stack[1:]
			if isinstance(op,Num):
				eexit("Num can't be applied")
			elif isinstance(op,Id):
				if not op.v in env.keys():
					if op.v == "#s":
						show_stack()
					elif op.v == "#e":
						show_env()
					else:
						eexit("undefined function %s" % op.v)
				else:
					f = env[op.v]
					if f.argnum > len(stack):
						eexit("insufficient arguments for function %s. Expected %d, got %d" % (op.v,f.argnum,len(stack)))
					
					args = stack[:f.argnum]
					stack = f.apply(args) + stack[f.argnum:]
			elif isinstance(op,Fundef):
				env[op.name] = op.definition
			else:
				assert False
	
	except Exit as e:
		return e.v
	
	assert False


if __name__=='__main__':
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

	def puts(s):
		sys.stdout.buffer.write(s)
		sys.stdout.flush()
	
	parser = argparse.ArgumentParser()
	parser.add_argument('filename', help='the name of the source code file')
	parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='show both stack and env')
	parser.add_argument('-ds', '--debug-stack', dest='debugstack', action='store_true', help='show stack')
	parser.add_argument('-de', '--debug-env', dest='debugenv', action='store_true', help='show env')

	args = parser.parse_args()
	code = open(args.filename,'r').read()
	program,rem = parse(tokenize(code))
	if len(rem) != 0:
		eexit('parse failure: token remains',rem) 
	exit(interpret(program,args))
	
