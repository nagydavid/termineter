#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  termineter/modules/get_data.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import unicode_literals

from c1218.errors import C1218ReadTableError
from termineter.module import TermineterModuleOptical

import binascii
import os
import time

class Module(TermineterModuleOptical):
	def __init__(self, *args, **kwargs):
		TermineterModuleOptical.__init__(self, *args, **kwargs)
		self.author = ['Spencer McIntyre']
		self.description = 'Read Data part From A C12.19 Table'
		self.detailed_description = 'This module get MyData from the smart meter.'

	def run(self):
		conn = self.frmwk.serial_connection
# Read 8 bytes (octet=8) from Table BT23 (Current Register Data)
		tableid = 23
		offset = 0
		octet = 8

		try:
			data = conn.get_table_part(tableid, octet, offset)
		except C1218ReadTableError as error:
			self.frmwk.print_error('Caught C1218ReadTableError: ' + str(error))

		self.frmwk.print_status('Read ' + str(len(data)) + ' bytes')
		self.frmwk.print_hexdump(data)

# Write data from Table BT23 to file named 'BT23'
		out_file = open('/var/tmp/BT23', 'w', 1)
		out_file.write(binascii.b2a_hex(data).decode('utf-8'))
		out_file.close()

# Read 40 bytes (octet=40) from Table BT28 (Present Register Data)
		tableid = 28
		offset = 0
		octet = 40

		try:
			data = conn.get_table_part(tableid, octet, offset)
		except C1218ReadTableError as error:
			self.frmwk.print_error('Caught C1218ReadTableError: ' + str(error))

		self.frmwk.print_status('Read ' + str(len(data)) + ' bytes')
		self.frmwk.print_hexdump(data)

# Write data from Table BT28 to file named 'BT28'
		out_file = open('/var/tmp/BT28', 'w', 1)
		out_file.write(binascii.b2a_hex(data).decode('utf-8'))
		out_file.close()
