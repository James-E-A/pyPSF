#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Cobbled together from:

* https://git.kernel.org/pub/scm/linux/kernel/git/legion/kbd.git/tree/src/psf.h
* https://www.win.tue.nl/~aeb/linux/kbd/font-formats-1.html
"""

import struct
from collections import OrderedDict
from PIL import Image
import unicodedata

PSF1_MAGIC		= b'\x36\x04'
PSF1_MODE512		= 0x01
PSF1_MODEHASTAB		= 0x02
PSF1_MODEHASSEQ		= 0x04
PSF1_MODEHASSEQ_MSG	= 'I have no idea yet what the "HASSEQ" mode means.\nIf you know whether (and, if so, how) it is different from "HASTAB",\nplease email me at agentorange@8chan.co so I can fix it.'
PSF1_MAXMODE		= 0x05
PSF1_SEPARATOR		= (0xFFFF).to_bytes(2,'little')
PSF1_STARTSEQ		= (0xFFFE).to_bytes(2,'little')

PSF2_MAGIC		= (0x864ab572).to_bytes(32/8,'little')
"""32-bit magic 0x864ab572"""
PSF2_HAS_UNICODE_TABLE	= 0x01
PSF2_MAXVERSION		= 0
PSF2_SEPARATOR		= (0xFF).to_bytes(1,'little')
PSF2_STARTSEQ		= (0xFE).to_bytes(1,'little')

_magic_ok		= lambda x,m: x[:len(m)]==m
PSF1_MAGIC_OK		= lambda x: _magic_ok(x,PSF1_MAGIC)
PSF2_MAGIC_OK		= lambda x: _magic_ok(x,PSF2_MAGIC)

PSF1_SPEC=('<',OrderedDict([
	('magic',  '2s'), # unsigned char magic[2];
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
"""The integers in the psf2 header struct are little endian 4-byte integers."""

CP437=''.join([
	#0x00=NUL
	# range(0x00,0x01)
	'\x00'
	
	#"Fun" symbols
	# range(0x01,0x10)
	"☺☻♥♦♣♠•◘○◙♂♀♪♬✺",
	# range(0x10,0x20)
	"►◄↕‼¶§▬↨↑↓→←∟↔▲▼",
	
	#Good Old ASCII
	# range(0x20,0x30)
	" !\x22#$%&\x27()*+,-./",
	# range(0x30,0x39)
	"0123456789",
	# range(0x3a,0x40)
	":;<=>?@",
	# range(0x40,0x5b)
	"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
	# range(0x5b,0x61)
	"[\\]^_`",
	# range(0x61,0x7b)
	"abcdefghijklmnopqrstuvwxyz",
	# range(0x7b,0x7f)
	"{|}~",
	
	#Upwards-pointing Lump
	# range(0x7f,0x80)
	"⌂",
	
	#Huge pile of diacritic letters
	# range(0x80,0x9b)
	"ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ",
	
	#Some symbols
	# range(0x9b,0x9f)
	"¢£¥₧ƒ",
	
	#Leftover diacritics lol
	# range(0xa0,0xa6)
	"áíóúñÑ",
	
	#More symbols
	# range(0xa6,0xb0)
	"ªº¿⌐¬½¼¡«»",
	
	#Box Drawing +accessories
	# range(0xb0,0xb3)
	"░▒▓",
	# range(0xb3,0xdb)
	"│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌","
	# range(0xdb,0xe0)
	"█▄▌▐▀",
	
	#A pile of Greek (+infinity)
	# range(0xe0,0xef)
	"αßΓπΣσµτΦΘΩδ∞φε",
	
	#Math Stuff
	# range(0xef,0xfe)
	"∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²",
	
	#A square (?)
	# range(0xfe,0xff)
	"■",
	
	#&nbsp;
	# range(0xff,256)
	"\xa0"
])

#_detect_v1v2_spec = lambda data: (
#	(PSF1_SPEC,PSF2_SPEC)[
#	 0 if PSF1_MAGIC_OK(data) else
#	 1 if PSF2_MAGIC_OK(data) else
#	 2 #raise ValueError
#	]
#)

#_spec = lambda data,spec: dict(zip(
#	spec,
#	struct.unpack_from(
#	  spec[0]+''.join(v for k,v in spec[1].items()),
#	  data
#	)
#))

#_parse_header = lambda data: _spec(data,_detect_v1v2_spec(data))

#_render_header = lambda header,spec=PSF2_SPEC: struct.pack(
#	spec[0]+''.join(v for k,v in spec[1].items()),
#	*(header[k] for k,v in spec[1].items())
#)

def _parse_PSF1(data):
	s=struct.Struct(PSF1_SPEC[0]+''.join(v for k,v in PSF1_SPEC[1].items()))
	h=dict(zip(
	  PSF1_SPEC,
	  s.unpack_from(data)
	))
	i=dict()
	i['_magic'] = h['magic']
	assert PSF2_MAGIC_OK(i['_magic'])
	i['_version'] = (1,)
	i['_headersize'] = s.size
	assert h['flags'] <= PSF1_MAXMODE
	i['_has_unicode_table'] = h['flags']&PSF1_MODEHASTAB
	if h['flags']&PSF1_MODEHASSEQ:
		raise NotImplementedError(PSF1_MODEHASSEQ_MSG)
	i['nglyphs'] = 256 << bool(h['flags']&PSF1_MODE512)
	i['glyphsize'] = h['charsize']
	i['size'] = (8, i['glyphsize'])
	return (
	 i,
	 data[
	  i['headersize']
	  :
	  i['headersize']+i['nglyphs']*i['glyphsize']
	 ],
	 data[
	  i['headersize']+i['nglyphs']*i['glyphsize']
	  :
	 ]
	)

def _parse_PSF2(data):
	s=struct.Struct(PSF2_SPEC[0]+''.join(v for k,v in PSF2_SPEC[1].items()))
	h=dict(zip(
	  PSF2_SPEC,
	  s.unpack_from(data)
	))
	i['_magic'] = h['magic']
	assert PSF2_MAGIC_OK(i['_magic'])
	i['_version'] = (2,h['version'])
	assert i['_version'] <= PSF2_MAXVERSION
	i['_headersize'] = h['headersize']
	i['_has_unicode_table'] = h['flags']&PSF2_HAS_UNICODE_TABLE
	i['nglyphs'] = h['length']
	i['glyphsize'] = h['charsize']
	i['size'] = (h['width'], h['height'])
#	assert i['glyphsize'] == i['size'][1] * ((i['size'][0] + 7) // 8)
	return (
	 i,
	 data[
	  i['_headersize']
	  :
	  i['_headersize']+i['nglyphs']*i['glyphsize']
	 ],
	 data[
	  i['_headersize']+i['nglyphs']*i['glyphsize']
	  :
	 ]
	)

def _render_PSF1(size, flat_glyphtable, flat_unicodetable=None):
	raise NotImplementedError

def _render_PSF2(size, flat_glyphtable, flat_unicodetable=None):
	raise NotImplementedError

class Psf:
	def __init__(self,data):
		if PSF1_MAGIC_OK(data):
			i,flat_glyphtable,flat_unicodetable=_parse_PSF1(data)
		
		elif PSF2_MAGIC_OK(data):
			i,flat_glyphtable,flat_unicodetable=_parse_PSF1(data)
		
		else:
			raise ValueError("No recognized header found!")
		
		self.glyphs=[
		  flat_glyphtable[index:index+i['glyphsize'] for index in (
		   range(0,len(flat_glyphtable),i['glyphsize'])
		  )
		]
		
		self._flat_glyphtable=flat_glyphtable

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

def extract_psf_to_dir(psf_path, dir=None):
	import os
	import unicodedata
	from PIL import Image
	if not dir:
		dir=os.path.splitext(psf_path)[0]
	os.mkdir(dir) #Yes, this does crash the script if already exists
	with open(psf_path, 'rb') as f:
		p=Psf(f.read())
	os.chdir(dir)
	for codepoint437,glyph in zip(range(p.nglyphs),p.glyphs):
		i=codepoint437*p.charsize
		
		if codepoint437<256:
			name='0x{:02x}_{}.{}'.format(
			  codepoint437,
			  unicodedata.name(CP437[codepoint437]).replace(' ','_'),
			  'png'
			)
		else:
			name='EXT_{:04d}.{}'.format(
			  codepoint437,
			  'png'
			)
		
		Image.frombytes('1', (p.width,p.height), p.glyphs[codepoint437]).save(name)

def compile_dir_to_psf(psf_dir, psf_path=None):
	import os,glob
	from PIL import Image
	
	matchfname=lambda s: s.startswith('0x') and s.endswith('png')
	
	if not psf_path:
		psf_path=psf_dir.rstrip('/\\')+'.psf'
		#IF path was autodetected
		assert not os.path.exists(psf_path),"Will not clobber unless path is explicitly set."
	
	assert sum(map(matchfname, os.listdir(psf_dir))) > 8
	with open(psf_path, 'wb') as f:
		os.chdir(psf_dir)
		f.write(
		 _render_header({
		  'magic':	PSF2_MAGIC,
		  'version':	0,
		  'headersize': headersize,
		  'flags':	0x00,
		  'length':	256,
		  'charsize':	charsize,
		  'height':	8,
		  'width':	6
		 })
		)
		#dirtychrs=((0b1<<nchars)-1)
		f.truncate()
		for fname in filter(matchfname, os.listdir()):
			i=int(fname[2:4],16)
			f.seek(headersize+charsize*i)
			f.write(
			 Image.open(fname).convert('1').tobytes()
			)
		f.seek(headersize+charsize*256)
		f.truncate()

if __name__=="__main__":
	import sys
	psf_dir=psf_path=None
	if len(sys.argv)>1 and sys.argv[1].endswith('.psf'):
		psf_path=sys.argv[1]
		if len(sys.argv)>2:
			psf_dir=sys.argv[2]
		extract_psf_to_dir(psf_path, *((psf_dir,) if psf_dir else ()) )
	
	elif len(sys.argv)>1 and sys.argv[1].endswith('/'):
		psf_dir=sys.argv[1]
		if len(sys.argv)>2:
			psf_path=sys.argv[2]
		compile_dir_to_psf(psf_dir, *((psf_path,) if psf_path else ()))
	
	else:
		psf_path=input("What is the .psf file")
		extract_psf_to_dir(psf_path, *((psf_dir,) if psf_dir else ()) )
#	interactive_main(sys.argv)
