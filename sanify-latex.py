# This file is part of TheBlackHole, which is free software and is licensed
# under the terms of the GNU GPL v3.0. (see http://www.gnu.org/licenses/ )

from sys import stdin
from colorama import init, Fore
init()

def getUntil(str, terminator):
	return str[:str.index(terminator)]

def getFile( str ):
	if str.startswith( '"' ):
		return '"' + getUntil( str[1:], '"' ) + '"'
	
	end = str.find( ')' )
	if end == -1:
		end = str.find( ' ' )
	
	return str[:end]
	
def getLine():
	line = stdin.readline()
	if len(line) > 79 : #TODO: verify this number
		return line.rstrip() + getLine()
	return line

def input():
	while True:
		line = getLine()
		if not line:
			break
		yield line
		
class Parser:
	context = []
	has_outputed = False
	
	def output(self, line):
		if line:
			indent = len(self.context)
			
			# Print the file context this output belongs to
			if not self.has_outputed and not indent==0:
				#TODO: print context levels which have been skipped as there were no output
				print( '' )
				print( Fore.CYAN + '\t'*(indent-1) + self.context[-1] + Fore.RESET )
				self.has_outputed = True
			
			print( '\t'*indent + line )
	
	# Do special formatting of known messages
	def handleLine(self, line):
		if line.startswith( "LaTeX Warning:" ):
			self.output( Fore.GREEN + line + Fore.RESET )
		elif line.startswith( "Underful" ) or line.startswith( "Overfull" ):
			self.output( Fore.GREEN + line + Fore.RESET )
		else:
			self.output( line )
	
	# Handle the "(filepath ...)" scoping
	def handleScope(self, line):
		trimmed = line.lstrip()
		if trimmed.startswith( '(' ):
			name = getFile( trimmed[1:] )
			self.context.append( name )
			self.has_outputed = False
			self.handleScope( trimmed[len(name)+1:] )
		elif trimmed.startswith( ')' ):
			self.context.pop()
			self.has_outputed = False
			self.handleScope( trimmed[1:] )
		else:
			self.handleLine( line.strip() )
	
	def parse(self):
		for line in input():
			self.handleScope( line );


def main():
	Parser().parse()
	
if __name__ == "__main__":
	main()