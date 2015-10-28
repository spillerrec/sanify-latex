#!/usr/bin/env python

# This file is part of TheBlackHole, which is free software and is licensed
# under the terms of the GNU GPL v3.0. (see http://www.gnu.org/licenses/ )

from colorama import init, Fore
import re
import sys
import subprocess
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
	
def getLine(stream):
	line = stream.readline()
	if len(line) > 79 : #TODO: verify this number
		return line.rstrip() + getLine(stream)
	return line

def input(stream):
	while True:
		line = getLine(stream)
		if not line:
			break
		yield line
		
class Parser:
	context = []
	has_outputed = False
	bracket_number = re.compile("^\[[0-9]*\]")
	lost_scope = re.compile("\(\./")
	
	def output(self, line):
		if line:
			indent = len(self.context)
			
			# Print the file context this output belongs to
			if not self.has_outputed and not indent==0:
				#TODO: print context levels which have been skipped as there were no output
				print( '' )
				print( Fore.CYAN + '   '*(indent-1) + self.context[-1] + Fore.RESET )
				self.has_outputed = True
			
			print( '   '*indent + line )
	
	# Do special formatting of known messages
	def handleLine(self, line):
		if line.startswith( "!" ):
			self.output( Fore.RED + line + Fore.RESET )
		elif line.startswith( "LaTeX Warning:" ):
			self.output( Fore.YELLOW + line + Fore.RESET )
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
		elif self.bracket_number.search(trimmed):
			#TODO: find out what this is
			self.handleScope( trimmed[self.bracket_number.search(trimmed).end():] )
		else:
			found_scope = self.lost_scope.search(trimmed)
			if found_scope:
			#	print( Fore.RED + "Warning, unexpected scope in: " + trimmed + Fore.RESET )
				self.handleLine( trimmed[:found_scope.start()] )
				self.handleScope( trimmed[found_scope.start():] )
			else:
				self.handleLine( line.strip() )
	
	def parseStrStream(self, stream):
		for line in input( stream ):
			self.handleScope( line );
	
	def parseBytesStream(self, stream):
		for line in input( stream ):
			self.handleScope( line.decode(sys.stdout.encoding) );


def main():
	if len(sys.argv) == 1:
		Parser().parseStrStream( sys.stdin )
	else:
		args = sys.argv
		args.remove(args[0])
		args.insert( 0, "pdflatex" )
		args.insert( 1, "-interaction=nonstopmode" )
		args.insert( 1, "-halt-on-error" )
		args.insert( 1, "-synctex=1" )
	#	args.insert( 1, "-file-line-error" )
		Parser().parseBytesStream( subprocess.Popen( args, stdout=subprocess.PIPE ).stdout )
		
	
if __name__ == "__main__":
	main()
