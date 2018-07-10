"""https://git.kernel.org/pub/scm/linux/kernel/git/legion/kbd.git/tree/src/psf.h"""

import struct
from collections import OrderedDict

PSF1_MAGIC		= b'\x36\x04'
PSF1_MODE512		= 0x01
PSF1_MODEHASTAB		= 0x02
PSF1_MODEHASSEQ		= 0x04
PSF1_MAXMODE		= 0x05
PSF1_SEPARATOR		= 0xFFFF
PSF1_STARTSEQ		= 0xFFFE

PSF2_MAGIC		= b'\x72\xb5\x4a\x86'
"""32-bit magic 0x864ab572: int.to_bytes(0x864ab572,32/8,'little')"""
PSF2_HAS_UNICODE_TABLE	= 0x01
PSF2_MAXVERSION		= 0
PSF2_SEPARATOR		= 0xFF
PSF2_STARTSEQ		= 0xFE

magic_ok		= lambda x,m: x[:len(m)]==m
PSF1_MAGIC_OK		= lambda x: magic_ok(x,PSF1_MAGIC)
PSF2_MAGIC_OK		= lambda x: magic_ok(x,PSF2_MAGIC)

PSF1_SPEC=('<',OrderedDict([
	('magic',  '2s'), # unsigned char magic[2];e
	('mode',    'B'), # unsigned char mode;
	('charsize','B'), # unsigned char charsize;
]))

PSF2_SPEC=('<',OrderedDict([
	('magic',     '4s'), # unsigned char magic[4];
	('version',    'i'), # unsigned int version;
	('headersize', 'i'), # unsigned int headersize;
	('flags',      'i'), # unsigned int flags;
	('length',     'i'), # unsigned int length;
	('charsize',   'i'), # unsigned int charsize;
	('height',     'i'), # unsigned int height,
	('width',      'i'), #              width;
]))

_parse_header = lambda data,spec=PSF2_SPEC: OrderedDict(zip(
	spec[1],
	struct.unpack_from(
	  spec[0]+''.join(v for k,v in spec[1].items()),
	  data
	)
))

_render_header = lambda header,spec=PSF2_SPEC: struct.pack(
	spec[0]+''.join(v for k,v in spec[1].items()),
	*(header[k] for k,v in spec[1].items())
)

class Psf:
	def __init__(self,data):
		if PSF1_MAGIC_OK(data):
			raise NotImplementedError
			self.parsed_header=parse_header(data,spec=PSF1_SPEC)
			self.header=data[:4] # struct.Struct('<2sBB').size
			self.body=data[
			 len(self.header)
			:
			 (256,512)[bool(self.parsed_header['mode']&PSF1_MODE512)]
			]
			
			self.width=8
			self.height=self.parsed_header['charsize']
			
			if self.parsed_header['mode']&PSF1_MODEHASTAB:
				self.unicode_table=data[len(self.header)+len(self.body):]
		
		elif PSF2_MAGIC_OK(data):
			self.parsed_header=parse_header(data,spec=PSF2_SPEC)
			self.header=data[:self.parsed_header['headersize']]
			self.body=data[
			 len(self.header)
			:
			 len(self.header)+self.parsed_header['length']*self.parsed_header['charsize']
			]
			
			self.width=self.parsed_header['width']
			self.height=self.parsed_header['height']
			
			if self.parsed_header['flags']&PSF2_HAS_UNICODE_TABLE:
				self.unicode_table=data[len(self.header)+len(self.body):]
		else:
			raise ValueError("Unrecognized header")
		
		# Only stuff common to PSF1 and PSF2
		self.magic=self.parsed_header['magic']
		self.charsize=self.parsed_header['charsize']
		
		assert self.charsize == self.height * ((self.width+7)//8) # /* charsize = height * ((width + 7) / 8) */

"""The integers here are little endian 4-byte integers."""

"""Format of the Unicode information:

For each font position <uc>*<seq>*<term>
where <uc> is a 2-byte little endian Unicode value,
<seq> = <ss><uc><uc>*, <ss> = psf1 ? 0xFFFE : 0xFE,
<term> = psf1 ? 0xFFFF : 0xFF.
and * denotes zero or more occurrences of the preceding item.

Semantics:
The leading <uc>* part gives Unicode symbols that are all
represented by this font position. The following sequences
are sequences of Unicode symbols - probably a symbol
together with combining accents - also represented by
this font position.
"""

display=lambda bs:print('\n'.join('{:08b}'.format(b).replace('0', '.').replace('1', '0') for b in bs))
def interactive_main(argv=['psf.py']):
	while True:
		print("What do you want do do? (h for help)")
		u_i=input("> ").split(' ',1)
		if u_i[0].startswith('h'):
			print("""The commands are:
h:	show this help
o:	open a file
S:	save the current file
s N:	select a glyph
c:	change a glyph
q:	exit
""")
			continue
		elif u_i[0].startswith('o'):
			if len(u_i)<2:
				fname=input("filename:")
			else:
				fname=u_i[1]
			with open(fname, 'rb+') as f:
				p=Psf(f.read())
			headers=p.parsed_header
			glyphs=[*struct.iter_unpack(r'8B', p.body)]
			continue
		elif u_i[0].startswith('S'):
			with open(fname,'wb') as f:
				f.write(render_header(headers))
				for glyph in glyphs:
					f.write(struct.pack('8B', *glyph))
			continue
		elif u_i[0].startswith('s'):
			sglyph=ord(u_i[1])
			display(glyphs[sglyph])
			continue
		elif u_i[0].startswith('c'):
			B=[]
			for i in range(p.height):
				B.append(int(input().replace('0','1').replace('.','0'),2))
			glyphs[sglyph]=bytes(B)
			continue
		elif u_i[0].startswith('q'):
			break

if __name__=="__main__":
	import sys
	interactive_main(sys.argv)
