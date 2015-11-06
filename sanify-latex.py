#!/usr/bin/env python

# This file is part of TheBlackHole, which is free software and is licensed
# under the terms of the GNU GPL v3.0. (see http://www.gnu.org/licenses/ )

from colorama import init, Fore
import re
import sys
from functools import partial
import subprocess
init()
	
def getLine(stream):
	line = stream.readline()
	if len(line.rstrip()) > 78 : #TODO: verify this number
		return line.rstrip() + getLine(stream)
	return line
		
def findFirst(str, matchers, skip=0):
	pos = -1
	matched = ""
	for matcher in matchers:
		match_pos = str.find( matcher, skip )
		if match_pos != -1:
			if match_pos < pos or pos < 0:
				pos = match_pos
				matched = matcher
	return (pos, matched)
		
class Scope:
	prefixes = []
	nested_count = 0
	
	def __init__(self, parser, start_char, end_char):
		self.parser = parser
		self.start_char = start_char
		self.  end_char =   end_char

	def getFile(self, str):
		# Include prefixes
		start = 0
		for prefix in self.prefixes:
			if str.startswith( prefix ):
				start = len(prefix)
		
		# Filename ends on '"' if it starts on '"'
		if str.startswith( '"' ):
			return str[:str.index( '"', 1+start )+1]
		
		# Otherwise end at the first whitespace, at the end of scope or end of file
		(end, _) = findFirst( str, [self.end_char, ' '])
		return str[:end]
	
	def breakLine(self, str, skip=0):
		(pos, key) = findFirst(str, [self.start_char, self.end_char], skip)
		
		if pos == -1:
			return -1
		
		self.nested_count += 1 if key==self.start_char else -1
		
		if self.nested_count < 0:
			return pos
		
		return self.breakLine(str, pos+1)
	
class FileScope(Scope):
	def __init__(self, parser):
		Scope.__init__(self, parser, '(', ')')

	def handleScope(self, line):
		self.name = self.getFile(line)
		self.parser.handleScope( line[len(self.name):] )
		
	def getName(self):
		return "File: " + self.name

	
class PageScope(Scope):
	bracket_number = re.compile("^[0-9]*")
	def __init__(self, parser):
		Scope.__init__(self, parser, '[', ']')
		
	def getName(self):
		return "Page: " + self.name

	def getNumber(self, line):
		pos = self.bracket_number.search(line)
		if pos:
			return line[:pos.end()]
		return ""
	
	def handleScope(self, line):
		self.name = self.getNumber(line)
		self.parser.handleScope( line[len(self.name):] )

	
class ResourceScope(Scope):
	def __init__(self, parser):
		Scope.__init__(self, parser, '<', '>')
		self.prefixes = ["use "]

	def handleScope(self, line):
		self.name = self.getFile(line)
		self.parser.handleScope( line[len(self.name):] )
		
	def getName(self):
		return "Resource: " + self.name
	

class Parser:
	context = []
	has_outputed = False
	lost_scope = re.compile("\(\./") #TODO: detect windows drive letters as well
	
	def output(self, line):
		if line:
			indent = len(self.context)
			
			# Print the file context this output belongs to
			if not self.has_outputed and not indent==0:
				#TODO: print context levels which have been skipped as there were no output
				print( '' )
				print( Fore.CYAN + '   '*(indent-1) + self.context[-1].getName() + Fore.RESET )
				self.has_outputed = True
			
			print( '   '*indent + line )
	
	def addScope(self, scope):
		self.context.append(scope)
		self.has_outputed = False
		return scope
	
	def checkForScope(self, line):
		if line.startswith( '(' ):
			self.addScope( FileScope(self) ).handleScope(line[1:])
		elif line.startswith( '[' ):
			self.addScope( PageScope(self) ).handleScope(line[1:])
		elif line.startswith( '<' ):
			self.addScope( ResourceScope(self) ).handleScope(line[1:])
		else:
			return False
		return True
			
	def endScope(self, line):
		if line.startswith( ')' ) or line.startswith( ']' ) or line.startswith( '>' ):
			if len(self.context) > 0:
				self.context.pop()
			else:
				print( Fore.RED + "Sanify-Warning, scopes were not parsed correctly" + Fore.RESET )
			
			self.has_outputed = False
			self.handleScope( line[1:] )
			return True
		else:
			return False
	
	# Do special formatting of known messages
	def handleLine(self, line):
		plain = line.lower()
		if line.startswith( "!" ) or "error" in plain or "unsuccessful" in plain or "fatal" in plain:
			self.output( Fore.RED + line + Fore.RESET )
		elif "warning" in plain or "not available" in plain:
			self.output( Fore.YELLOW + line + Fore.RESET )
		elif line.startswith( "Underful" ) or line.startswith( "Overfull" ):
			self.output( Fore.YELLOW + line + Fore.RESET )
		else:
			self.output( line )
	
	# Handle the "(filepath ...)" scoping
	def handleScope(self, line):
		trimmed = line.lstrip()
		if self.checkForScope( trimmed ):
			return
		
		if self.endScope( trimmed ):
			return
		
		if len(self.context) > 0:
			pos = self.context[-1].breakLine( line )
			if pos != -1:
				self.handleLine( line[:pos] )
				self.handleScope( line[pos:] )
				return
		
		#Handle ordinary input
		found_scope = self.lost_scope.search(trimmed)
		if found_scope:
		#	print( Fore.RED + "Warning, unexpected scope in: " + trimmed + Fore.RESET )
			self.handleLine( trimmed[:found_scope.start()] )
			self.handleScope( trimmed[found_scope.start():] )
		else:
			self.handleLine( line.strip() )
	
	def parseBytesStream(self, stream):
		for line in iter(partial(getLine,stream), b''):
			self.handleScope( line.decode(sys.stdout.encoding) );


def main():
	if len(sys.argv) == 1:
		Parser().parseBytesStream( sys.stdin.buffer )
	else:
		args = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-synctex=1"]
		args.extend( sys.argv[1:] )
		Parser().parseBytesStream( subprocess.Popen( args, stdout=subprocess.PIPE ).stdout )
		
	
if __name__ == "__main__":
	main()
