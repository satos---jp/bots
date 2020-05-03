import const

class F:
	def __init__(self):
		self.F = lambda x: x+1
		
	def q(self,y):
		self.F = lambda x: x+y

d = F()

print(d.F(1))

d.q(2)

print(d.F(1))
