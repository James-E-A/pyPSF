#!/usr/bin/env python3

"""Cobbled together from:

* https://git.kernel.org/pub/scm/linux/kernel/git/legion/kbd.git/tree/src/psf.h
* https://www.win.tue.nl/~aeb/linux/kbd/font-formats-1.html
"""

import struct
from collections import OrderedDict
from PIL import Image
#import unicodedata
import os.path
import string

PSF1_MAGIC		= b'\x36\x04'
PSF1_MODE512		= 0x01
PSF1_MODEHASTAB		= 0x02
PSF1_MODEHASSEQ		= 0x04
PSF1_MODEHASSEQ_msg	= 'I have no idea yet what the "HASSEQ" mode means.\nIf you know whether (and, if so, how) it is different from "HASTAB",\nplease email me at agentorange@8chan.co so I can fix it.'
PSF1_MAXMODE		= 0x05
PSF1_ENCODING		= 'utf-16le'
PSF1_SEPARATOR		= '\uFFFF'.encode(PSF1_ENCODING)
PSF1_STARTSEQ		= '\uFFFE'.encode(PSF1_ENCODING)

PSF2_MAGIC		= (0x864ab572).to_bytes(32//8,'little')
"""32-bit magic 0x864ab572"""
PSF2_HAS_UNICODE_TABLE	= 0x01
PSF2_MAXVERSION		= 0
PSF2_ENCODING		= 'utf-8'
PSF2_SEPARATOR		= b'\xFF'
PSF2_STARTSEQ		= b'\xFE'

_magic_ok		= lambda x,m: x[:len(m)]==m
PSF1_MAGIC_OK		= lambda x: _magic_ok(x,PSF1_MAGIC)
PSF2_MAGIC_OK		= lambda x: _magic_ok(x,PSF2_MAGIC)

PSF1_SPEC=('<',OrderedDict([
	('magic',  '2s'), # Magic bytes sequence (should be equal to PSF1_MAGIC)
	('mode',    'B'), # Metadata bitfield (see PSF1_MODE* constants)
	('charsize','B'), # Size-in-bytes (AKA height-in-pixels) of a glyph
]))

PSF2_SPEC=('<',OrderedDict([
	('magic',     '4s'), # Magic bytes sequence (should be equal to PSF2_MAGIC)
	('version',    'i'), # The 'X' in 'PSFv2.X' (only 2.0 supported)
	('headersize', 'i'), # Offset of the glyphtable (ought to be equal to Struct.size)
	('flags',      'i'), # Metadata bitfield (see PSF2_HAS* constants)
	('length',     'i'), # Number of characters
	('charsize',   'i'), # Size-in-bytes of a glyph (ought to be greater than h*w/8)
	('height',     'i'), # Height-in-pixels of a glyph
	('width',      'i'), # Width-in-pixels of a glyph
]))

def _spec2fmtstr(spec):
	return ''.join((
		 spec[0],
		 *(v for k,v in spec[1].items())
		))

def _parse_header(header, spec):
	st=struct.Struct(_spec2fmtstr(spec))
	d=dict(zip(
	 (k for k,v in spec[1].items()),
	 st.unpack_from(header)
	))
	if 'headersize' in d:
		s=d['headersize']
	else:
		s=st.size
	return s,d

with open(os.path.join(os.path.dirname(__file__),'CP00437.txt')) as f:
	CP437_Names=(*(
		line.split(maxsplit=2)[-1].strip() for line in
		 filter(
		  lambda l:(l[0] in string.hexdigits and l[1] in string.hexdigits),
		 f)
	),)

_ceil_div=lambda a,b=8:-(-a//b)

class Psf:
	def __init__(self,psf_file=None):
		if os.path.isdir(psf_file):
			raise NotImplementedError
		
		with open(psf_file, 'r+b') as f:
			if PSF2_MAGIC_OK(f.peek(len(PSF2_MAGIC))):
				s,hedr=_parse_header(
				 f.read(struct.calcsize(_spec2fmtstr(PSF2_SPEC))),
				 PSF2_SPEC
				)
				cod=PSF2_ENCODING
				chl=len('a'.encode(cod))
				sep=PSF2_SEPARATOR
				seq=PSF2_STARTSEQ
				#self.version=(2,hedr['version'])
				assert hedr['version'] <= PSF2_MAXVERSION
				
				has_unicode_table = bool(hedr['flags']&PSF2_HAS_UNICODE_TABLE)
				nglyphs           = hedr['length']
				glyphsize         = hedr['charsize']
				self.size         = (hedr['width'],hedr['height'])
			
			elif PSF1_MAGIC_OK(f.peek(len(PSF1_MAGIC))):
				s,hedr=_parse_header(
				 f.read(struct.calcsize(_spec2fmtstr(PSF1_SPEC))),
				 PSF1_SPEC
				)
				cod=PSF1_ENCODING
				chl=len('a'.encode(cod))
				sep=PSF1_SEPARATOR
				seq=PSF1_STARTSEQ
				#self.version=(1,)
				if hedr['mode']&PSF1_MODEHASSEQ:
					raise NotImplementedError(PSF1_MODEHASSEQ_msg)
				
				has_unicode_table = bool(hedr['mode']&PSF1_MODEHASTAB)
				nglyphs           = 512 if hedr['mode']&PSF1_MODE512 else 256
				glyphsize         = hedr['charsize']
				self.size         = (8,glyphsize)
			else:
				raise ValueError("No valid header found")
			f.seek(s)
			self.glyphs=[]
			for i in range(nglyphs):
				self.glyphs.append(f.read(glyphsize))
			if has_unicode_table:
				#TODO: make this streaming/iterable
				#TODO: sequences
				self.unicode_table=[
					c.rstrip(sep).decode(cod)
					for c in
					f.read().split(sep,nglyphs-1)
				]
	def display(self, w=16):
		#TODO: more formatting options
		im=Image.new(mode='1',size=(self.size[0]*w,_ceil_div(self.size[0]*len(self.glyphs),w)))
		for i in range(len(self.glyphs)):
			im.paste(
			 Image.frombytes(
			  mode='1',
			  size=self.size,
			  data=self.glyphs[i]
			 ),
			 (
			  self.size[0]*(i%w),       #left
			  self.size[1]*(i//w),  #upper
			  self.size[0]*((i%w)+1),   #right
			  self.size[1]*(i//w+1) #lower
			 )
			)
		return im.show()
