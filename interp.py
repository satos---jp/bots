#coding: utf-8

import sys


buf = []
def getc():
	global buf
	if len(buf)>0:
		c = buf[0]
		buf = buf[1:]
		return c
	else:
		c = sys.stdin.read(1)
		if len(c)==0:
			return -1
		else:
			return ord(c)

def ungetc(c):
	global buf
	buf.append(c)

def head(s):
	if ' ' in s:
		d = s.index(' ')
		v = s[:d]
		s = s[d:]
		while len(s)>0 and s[0]==' ':
			s = s[1:]
		return v,s
	else:
		return s,''

def binop(na,op):
	def f(s):
		a,s = head(s)
		b,s = head(s)
		v,s = head(s)
		a = int(a)
		b = int(b)
		return '%s %d %s' % (v[1:],op(a,b),s)
	return (na,f)

def inc(s):
	c = getc()
	v,s = head(s)
	return '%s %d %s' % (v[1:],c,s)

def ind(s):
	ds = ''
	while True:
		c = getc()
		if ord('0') <= c and c <= ord('9'):
			ds += chr(c)
		else:
			ungetc(c)
			break
	
	v,s = head(s)
	return '%s %d %s' % (v[1:],int(ds),s)

def outc(s):
	v,s = head(s)
	sys.stdout.write('%c' % chr(int(v)))
	return s[1:]

def outd(s):
	v,s = head(s)
	sys.stdout.write('%d' % int(v))
	return s[1:]

def nop(s):
	return s[1:]

def if_op(s):
	v,s = head(s)
	c,s = head(s)
	d = s.index(c)
	s_if,s_else = s[:d],s[d+len(c)+1:]
	if int(v)==0:
		return s_else[1:]
	else:
		return s_if[1:]

def exit_op(s):
	exit(0)

"""
def set_at(v):
	a = v[0]
	d = int(v[1])
	v = v[2:]
	return v[:d] + [a] + v[d:]
"""

bots = [inc,ind,outc,outd]

bots = dict(map(lambda x: (x.__name__,x),bots))
bots.update(dict([
	binop("add",lambda a,b: a+b),
	binop("sub",lambda a,b: a-b),
	binop("mul",lambda a,b: a*b),
	binop("div",lambda a,b: a//b),
	("if",if_op),
	("exit",exit_op),
]))

def dprint(s):
	global debug
	if debug:
		sys.stderr.write(str(s)+'\n')

def get_args(s):
	assert s[0]=='('
	s = s[1:]
	d = s.index(')')
	args,body = s[:d],s[d+2:]
	args = list(filter(lambda x: x!='',args.split(',')))
	return args,body

# @user name ` ($a,$b) .@hoge $a $b ` “I‚È‚Ì
def user(s):
	name,s = head(s)
	c,s = head(s)
	d = s.index(c)
	body,s = s[:d],s[d+len(c)+2:]
	args,body = get_args(body)
	
	def f(ts):
		vs = []
		for _ in range(len(args)-1):
			v,ts = head(ts)
			vs.append(v)
		vs.append(ts)
		dprint(zip(args,vs))
		
		res = body
		for fr,v in zip(args,vs):
			res = res.replace(fr,v)
		# print('return',res)
		return res
	
	bots.update({name: f})
	
	return s

bots.update({'user':user})

def interp(s):
	while len(s)>0:
		dprint(s)
		to,s = head(s)
		assert to[0]=="@"
		to = to[1:]
		if to in bots.keys():
			s = bots[to](s)
		else:
			raise Exception("user @%s is not found" % to)

debug = True
#debug = False

import os
if __name__ == '__main__':
	#s = '@in .@sub 1 .@if .@fact .@f'
	# fact
	s = (
		'@user apply ` ($a,$c,$r) @trim $c $a $r ` ' + 
		'.@user trim ` ($r) @if 1 # $r # ` ' + 
		'.@user fact ` ($a,$c) @sub $a 1 .@if # .@sub $a 1 .@fact .@mul $a $c # .@apply 1 $c ` ' + 
		'.@ind .@fact .@outd .@exit'
	)
	
	# ‚±‚È‚¢‚¾‚Ì
	s = (
		 '@user not ` ($x,$c,$r) @if $x # $c 0 $r # $c 1 $r ` ' + 
		'.@user xor ` ($a,$b,$c,$r) @if $a # .@not $b $c $r # $c $b $r ` ' + 
		  '.@user f ` ($a,$c,$r) @add $a 48 .@outc $c $a $r ` ' + 
		  '.@user g ` ($a,$c,$r) @sub $a 10 .@if # $c $a $r # .@exit ` ' + 
		'.@user main ` ($a,$c,$r) @inc .@g .@sub 48 .@xor $a .@f .@main $c $r ` ' + 
		'.@main 0'
	)
	s = open(os.sys.argv[1]).read()
	"""
	
	hs = "Hello, world!"
	s = "".join(map(lambda x: '.@outc %d ' % ord(x), hs))
	s = s[1:] + '.@exit'
	#print(s)
	s = (
		'@user f ` ($a,$c,$r) @add $a 1 .@if # $c $a $r # .@exit ` ' + 
		'.@user main ` () @inc .@f .@outc .@main ` ' + 
		'.@main'
	)
	print(s)
	"""
	# s = "@div 5 3"
	interp(s)




