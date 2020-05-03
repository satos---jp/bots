import interpreter
import sys

def check(prog,ins,outs):
	mins = ins
	ins = list(ins)
	nout = b""
	def puts(s):
		nonlocal nout
		nout += s
	def getc():
		nonlocal ins
		if len(ins) > 0:
			res = ins[0]
			ins = ins[1:]
			return res
		else:
			return -1
	def ungetc(c):
		nonlocal ins
		ins = [c] + ins
	
	interpreter.puts = puts
	interpreter.getc = getc
	interpreter.ungetc = ungetc

	program,rem = interpreter.parse(interpreter.tokenize(prog))
	if len(rem) != 0:
		eexit('parse failure: token remains',rem) 
	interpreter.interpret(program)
	
	if nout != outs:
		sys.stderr.buffer.write(
			b'test failed\nprogram: %s\ninput: %s\noutput: %s\nexpect: %s\n' % (bytes(map(ord,prog)),mins,nout,outs))
		exit(-1)

# exit
check('@ 0',b'',b'')

# io
check('oc 49 @ 0',b'',b'1')
check('od 49 @ 0',b'',b'49')
check('ic od @ 0',b'314',b'51')
check('id od @ 0',b'314',b'314')
check('oc 72 oc 101 oc 108 oc 108 oc 111 oc 44 oc 32 oc 119 oc 111 oc 114 oc 108 oc 100 oc 33 @ 0',b'',b'Hello, world!')

# arith
check('+ 1 2 od @ 0',b'',b'3')
check('- 9 3 od @ 0',b'',b'6')
check('* 3 5 od @ 0',b'',b'15')
check('/ 29 3 od @ 0',b'',b'9')

# cond
check('? 0 oc od 49 @ 0',b'',b'49')
check('? 1 oc od 49 @ 0',b'',b'1')
check('? 2 oc od 49 @ 0',b'',b'1')

# func
check('f(){od 1}f @ 0',b'',b'1')
check('0F3f(){od 1}0F3f @ 0',b'',b'1')
check('f(x){od x}f 3 @ 0',b'',b'3')
check('f(a,b,c,d,e){+ a b - c / d * e od}f 9 8 7 3 4 @ 0',b'',b'12')
check('g(x,y,r){ * x y + 2 r } f(x){g x x}f 3 od @ 0',b'',b'11')
check('g(x){ + 1 x ? + @ 0 x oc } f(){ ic g f } f',b'meow\n',b'meow\n')
check('o(x,y){y 1} g(x){ - x 1 f * x } f(x){ ? x g o x } id f od @ 0',b'10',b'3628800')
check('''
ack(x,y,r){ ? x f1 f2 x y r } 
f2(x,y,r){ + 1 y r } f1(x,y,r){ ? y g1 g2 x y r } 
g2(x,y,r){ - x 1 ack 1 r } ack2(y,x,r){ ack x y r } g1(x,y,r){ - y 1 ack2 x h x r } h(y,x,r){ - x 1 ack y r }
ack 3 2 od @ 0
''',b'',b'29')

# dinamic binding
check('f(x){ g(y){ + x y } } f 3 g 2 od @ 0',b'',b'5')
check('f(x){ g(x){ + x 4 } } f 3 g 2 od @ 0',b'',b'7')


sys.stderr.write('all test passed\n')
