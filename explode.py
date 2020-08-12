#!/usr/bin/env python
# coding: utf-8
#
# Explode library for PKWARE compression library
# based on Ladislav Zezula's StormLib explode.c @ 2003
# ported to Python by O. Kutal @ 2020
#

CMP_BINARY = 0  # Binary compression
CMP_ASCII = 1   # Ascii compression

CMP_NO_ERROR = 0
CMP_INVALID_DICTSIZE = 1
CMP_INVALID_MODE = 2
CMP_BAD_DATA = 3
CMP_ABORT = 4

CMP_IMPLODE_DICT_SIZE1 = 1024  # Dictionary size of 1024
CMP_IMPLODE_DICT_SIZE2 = 2048  # Dictionary size of 2048
CMP_IMPLODE_DICT_SIZE3 = 4096  # Dictionary size of 4096

PKDCL_OK = 0
PKDCL_STREAM_END = 1  # All data from the input stream is read
PKDCL_NEED_DICT = 2  # Need more data (dictionary)
PKDCL_CONTINUE = 10  # Internal flag, not returned to user
PKDCL_GET_INPUT = 11  # Internal flag, not returned to user

dist_bits = [
    0x02, 0x04, 0x04, 0x05, 0x05, 0x05, 0x05, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x06,
    0x06, 0x06, 0x06, 0x06, 0x06, 0x06, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07,
    0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07,
    0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08
]

dist_code = [
    0x03, 0x0D, 0x05, 0x19, 0x09, 0x11, 0x01, 0x3E, 0x1E, 0x2E, 0x0E, 0x36, 0x16, 0x26, 0x06, 0x3A,
    0x1A, 0x2A, 0x0A, 0x32, 0x12, 0x22, 0x42, 0x02, 0x7C, 0x3C, 0x5C, 0x1C, 0x6C, 0x2C, 0x4C, 0x0C,
    0x74, 0x34, 0x54, 0x14, 0x64, 0x24, 0x44, 0x04, 0x78, 0x38, 0x58, 0x18, 0x68, 0x28, 0x48, 0x08,
    0xF0, 0x70, 0xB0, 0x30, 0xD0, 0x50, 0x90, 0x10, 0xE0, 0x60, 0xA0, 0x20, 0xC0, 0x40, 0x80, 0x00
]

ex_len_bits = [
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08
]

len_base = [
    0x0000, 0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007,
    0x0008, 0x000A, 0x000E, 0x0016, 0x0026, 0x0046, 0x0086, 0x0106
]

len_bits = [
    0x03, 0x02, 0x03, 0x03, 0x04, 0x04, 0x04, 0x05, 0x05, 0x05, 0x05, 0x06, 0x06, 0x06, 0x07, 0x07
]

len_code = [
    0x05, 0x03, 0x01, 0x06, 0x0A, 0x02, 0x0C, 0x14, 0x04, 0x18, 0x08, 0x30, 0x10, 0x20, 0x40, 0x00
]

ch_bits_asc = [
    0x0B, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x08, 0x07, 0x0C, 0x0C, 0x07, 0x0C, 0x0C,
    0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0D, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C,
    0x04, 0x0A, 0x08, 0x0C, 0x0A, 0x0C, 0x0A, 0x08, 0x07, 0x07, 0x08, 0x09, 0x07, 0x06, 0x07, 0x08,
    0x07, 0x06, 0x07, 0x07, 0x07, 0x07, 0x08, 0x07, 0x07, 0x08, 0x08, 0x0C, 0x0B, 0x07, 0x09, 0x0B,
    0x0C, 0x06, 0x07, 0x06, 0x06, 0x05, 0x07, 0x08, 0x08, 0x06, 0x0B, 0x09, 0x06, 0x07, 0x06, 0x06,
    0x07, 0x0B, 0x06, 0x06, 0x06, 0x07, 0x09, 0x08, 0x09, 0x09, 0x0B, 0x08, 0x0B, 0x09, 0x0C, 0x08,
    0x0C, 0x05, 0x06, 0x06, 0x06, 0x05, 0x06, 0x06, 0x06, 0x05, 0x0B, 0x07, 0x05, 0x06, 0x05, 0x05,
    0x06, 0x0A, 0x05, 0x05, 0x05, 0x05, 0x08, 0x07, 0x08, 0x08, 0x0A, 0x0B, 0x0B, 0x0C, 0x0C, 0x0C,
    0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D,
    0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D,
    0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D,
    0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C,
    0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C,
    0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C, 0x0C,
    0x0D, 0x0C, 0x0D, 0x0D, 0x0D, 0x0C, 0x0D, 0x0D, 0x0D, 0x0C, 0x0D, 0x0D, 0x0D, 0x0D, 0x0C, 0x0D,
    0x0D, 0x0D, 0x0C, 0x0C, 0x0C, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D, 0x0D
]

ch_code_asc = [
    0x0490, 0x0FE0, 0x07E0, 0x0BE0, 0x03E0, 0x0DE0, 0x05E0, 0x09E0,
    0x01E0, 0x00B8, 0x0062, 0x0EE0, 0x06E0, 0x0022, 0x0AE0, 0x02E0,
    0x0CE0, 0x04E0, 0x08E0, 0x00E0, 0x0F60, 0x0760, 0x0B60, 0x0360,
    0x0D60, 0x0560, 0x1240, 0x0960, 0x0160, 0x0E60, 0x0660, 0x0A60,
    0x000F, 0x0250, 0x0038, 0x0260, 0x0050, 0x0C60, 0x0390, 0x00D8,
    0x0042, 0x0002, 0x0058, 0x01B0, 0x007C, 0x0029, 0x003C, 0x0098,
    0x005C, 0x0009, 0x001C, 0x006C, 0x002C, 0x004C, 0x0018, 0x000C,
    0x0074, 0x00E8, 0x0068, 0x0460, 0x0090, 0x0034, 0x00B0, 0x0710,
    0x0860, 0x0031, 0x0054, 0x0011, 0x0021, 0x0017, 0x0014, 0x00A8,
    0x0028, 0x0001, 0x0310, 0x0130, 0x003E, 0x0064, 0x001E, 0x002E,
    0x0024, 0x0510, 0x000E, 0x0036, 0x0016, 0x0044, 0x0030, 0x00C8,
    0x01D0, 0x00D0, 0x0110, 0x0048, 0x0610, 0x0150, 0x0060, 0x0088,
    0x0FA0, 0x0007, 0x0026, 0x0006, 0x003A, 0x001B, 0x001A, 0x002A,
    0x000A, 0x000B, 0x0210, 0x0004, 0x0013, 0x0032, 0x0003, 0x001D,
    0x0012, 0x0190, 0x000D, 0x0015, 0x0005, 0x0019, 0x0008, 0x0078,
    0x00F0, 0x0070, 0x0290, 0x0410, 0x0010, 0x07A0, 0x0BA0, 0x03A0,
    0x0240, 0x1C40, 0x0C40, 0x1440, 0x0440, 0x1840, 0x0840, 0x1040,
    0x0040, 0x1F80, 0x0F80, 0x1780, 0x0780, 0x1B80, 0x0B80, 0x1380,
    0x0380, 0x1D80, 0x0D80, 0x1580, 0x0580, 0x1980, 0x0980, 0x1180,
    0x0180, 0x1E80, 0x0E80, 0x1680, 0x0680, 0x1A80, 0x0A80, 0x1280,
    0x0280, 0x1C80, 0x0C80, 0x1480, 0x0480, 0x1880, 0x0880, 0x1080,
    0x0080, 0x1F00, 0x0F00, 0x1700, 0x0700, 0x1B00, 0x0B00, 0x1300,
    0x0DA0, 0x05A0, 0x09A0, 0x01A0, 0x0EA0, 0x06A0, 0x0AA0, 0x02A0,
    0x0CA0, 0x04A0, 0x08A0, 0x00A0, 0x0F20, 0x0720, 0x0B20, 0x0320,
    0x0D20, 0x0520, 0x0920, 0x0120, 0x0E20, 0x0620, 0x0A20, 0x0220,
    0x0C20, 0x0420, 0x0820, 0x0020, 0x0FC0, 0x07C0, 0x0BC0, 0x03C0,
    0x0DC0, 0x05C0, 0x09C0, 0x01C0, 0x0EC0, 0x06C0, 0x0AC0, 0x02C0,
    0x0CC0, 0x04C0, 0x08C0, 0x00C0, 0x0F40, 0x0740, 0x0B40, 0x0340,
    0x0300, 0x0D40, 0x1D00, 0x0D00, 0x1500, 0x0540, 0x0500, 0x1900,
    0x0900, 0x0940, 0x1100, 0x0100, 0x1E00, 0x0E00, 0x0140, 0x1600,
    0x0600, 0x1A00, 0x0E40, 0x0640, 0x0A40, 0x0A00, 0x1200, 0x0200,
    0x1C00, 0x0C00, 0x1400, 0x0400, 0x1800, 0x0800, 0x1000, 0x0000
]


def _gen_decode_tabs(positions, start_indexes, length_bits):
    assert (len(length_bits) == len(start_indexes))
    for i in range(len(length_bits)):
        length = 1 << length_bits[i]  # Get the length in bytes
        index = start_indexes[i]
        while index < 0x100:
            positions[index] = i & 0xFF
            index += length


class PkDecompressor:

    def __init__(self, input_buffer):
        self.offs0000 = 0  # 0000
        self.ctype = 0  # 0004: Compression type (CMP_BINARY or CMP_ASCII)
        self.output_pos = 0  # 0008: Position in output buffer
        self.dsize_bits = 0  # 000C: Dict size (4, 5, 6 for 0x400, 0x800, 0x1000)
        self.dsize_mask = 0  # 0010: Dict size bitmask (0x0F, 0x1F, 0x3F for 0x400, 0x800, 0x1000)
        self.bit_buff = 0  # 0014: 16-bit buffer for processing input data
        self.extra_bits = 0  # 0018: Number of extra (above 8) bits in bit buffer
        self.in_pos = 0  # 001C: Position in in_buff
        self.in_bytes = 0  # 0020: Number of bytes in input buffer
        self.out_buff = bytearray(0x2204)  # 0030: Output circle buffer.
        #        0x0000 - 0x0FFF: Previous uncompressed data, kept for repetitions
        #        0x1000 - 0x1FFF: Currently decompressed data
        #        0x2000 - 0x2203: Reserve space for the longest possible repetition
        self.in_buff = input_buffer  # bytearray(0x800)  # 2234: Buffer for data to be decompressed
        self.in_bytes = len(input_buffer)
        if self.in_bytes <= 4:
            raise Exception("CMP_BAD_DATA")

        self.dist_pos_codes = bytearray(0x100)  # 2A34: Table of distance position codes
        self.length_codes = bytearray(0x100)  # 2B34: Table of length codes
        self.offs2C34 = bytearray(0x100)  # 2C34: Buffer for
        self.offs2D34 = bytearray(0x100)  # 2D34: Buffer for
        self.offs2E34 = bytearray(0x80)  # 2EB4: Buffer for
        self.offs2EB4 = bytearray(0x100)  # 2EB4: Buffer for
        self.ch_bits_asc = bytearray(0x100)  # 2FB4: Buffer for
        self.dist_bits = bytearray(0x40)  # 30B4: Numbers of bytes to skip copied block length
        self.len_bits = bytearray(0x10)  # 30F4: Numbers of bits for skip copied block length
        self.ex_len_bits = bytearray(0x10)  # 3104: Number of valid bits for copied block
        self.len_base = [0] * 0x10  # 3114: Buffer for
        self.decompressed = bytearray()

        #  Initialize work struct and load compressed data
        #  Note: The caller must zero the "work_buff" before passing it to explode
        self.in_pos = len(self.in_buff)
        self.ctype = self.in_buff[0]  # Get the compression type (CMP_BINARY or CMP_ASCII)
        self.dsize_bits = self.in_buff[1]  # Get the dictionary size
        self.bit_buff = self.in_buff[2]  # Initialize 16-bit bit buffer
        self.extra_bits = 0  # Extra (over 8) bits
        self.in_pos = 3  # Position in input buffer

        #  Test for the valid dictionary size
        if 4 > self.dsize_bits or self.dsize_bits > 6:
            raise Exception("CMP_INVALID_DICTSIZE")

        self.dsize_mask = 0xFFFF >> (0x10 - self.dsize_bits)  # Shifted by 'sar' instruction

        if self.ctype != CMP_BINARY:
            if self.ctype != CMP_ASCII:
                raise Exception("CMP_INVALID_MODE")

            self.ch_bits_asc[:len(self.ch_bits_asc)] = ch_bits_asc
            self._gen_asc_tabs()

        self.len_bits[:len(self.len_bits)] = len_bits
        _gen_decode_tabs(self.length_codes, len_code, self.len_bits, )
        self.ex_len_bits[:len(self.ex_len_bits)] = ex_len_bits
        self.len_base[:len(self.len_base)] = len_base
        self.dist_bits[:len(self.dist_bits)] = dist_bits
        _gen_decode_tabs(self.dist_pos_codes, dist_code, self.dist_bits)

    def expand(self):
        self.output_pos = 0x1000  # Initialize output buffer position

        #  Decode the next literal from the input data.
        #  The returned literal can either be an uncompressed byte (next_literal < 0x100)
        #  or an encoded length of the repeating byte sequence that
        #  is to be copied to the current buffer position
        result = next_literal = self._decode_lit()

        while result < 0x305:
            #  If the literal is greater than 0x100, it holds length
            #  of repeating byte sequence
            #  literal of 0x100 means repeating sequence of 0x2 bytes
            #  literal of 0x101 means repeating sequence of 0x3 bytes
            #  ...
            #  literal of 0x305 means repeating sequence of 0x207 bytes
            if next_literal >= 0x100:
                #  Get the length of the repeating sequence.
                #  Note that the repeating block may overlap the current output position,
                #  for example if there was a sequence of equal bytes
                rep_length = next_literal - 0xFE

                #  Get backward distance to the repetition
                minus_dist = self._decode_dist(rep_length)
                if minus_dist == 0:
                    result = 0x306
                    break

                #  Target and source pointer
                target_offset = self.output_pos
                source_offset = self.output_pos - minus_dist

                #  Copy the repeating sequence
                self.out_buff[target_offset:target_offset + rep_length] = \
                    self.out_buff[source_offset:source_offset + rep_length]

                #  Update buffer output position
                self.output_pos += rep_length

            else:
                self.output_pos += 1
                self.out_buff[self.output_pos - 1] = next_literal & 0xFF

            #  Flush the output buffer, if number of extracted bytes has reached the end
            if self.output_pos >= 0x2000:
                #  Copy decompressed data into user buffer
                copy_bytes = 0x1000
                self.decompressed += self.out_buff[0x1000:0x1000 + copy_bytes]

                #  Now copy the decompressed data to the first half of the buffer.
                #  This is needed because the decompression might reuse them as repetitions.
                #  Note that if the output buffer overflowed previously, the extra decompressed bytes
                #  are stored in "out_buff_overflow", and they will now be
                #  within decompressed part of the output buffer.
                target_offset = 0
                source_offset = 0x1000
                copy_length = self.output_pos - 0x1000

                self.out_buff[target_offset:target_offset + copy_length] = \
                    self.out_buff[source_offset:source_offset + copy_length]

                self.output_pos -= 0x1000

            result = next_literal = self._decode_lit()

        #  Flush any remaining decompressed bytes
        copy_bytes = self.output_pos - 0x1000
        self.decompressed += self.out_buff[0x1000:0x1000 + copy_bytes]

        if result != 0x306:
            return self.decompressed
        raise Exception("CMP_ABORT")

    def _gen_asc_tabs(self):
        pch_code_asc_idx = 0xFF
        count = 0x00FF

        while pch_code_asc_idx >= 0:
            pch_bits_asc_idx = count
            bits_asc = self.ch_bits_asc[pch_bits_asc_idx]

            if bits_asc <= 8:
                add = (1 << bits_asc)
                acc = ch_code_asc[pch_code_asc_idx]

                while True:
                    self.offs2C34[acc] = count & 0xFF
                    acc += add
                    if acc >= 0x100:
                        break

            else:
                acc = (ch_code_asc[pch_code_asc_idx] & 0xFF)
                if acc != 0:
                    self.offs2C34[acc] = 0xFF

                    if ch_code_asc[pch_code_asc_idx] & 0x3F:
                        bits_asc -= 4
                        self.ch_bits_asc[pch_bits_asc_idx] = bits_asc

                        add = (1 << bits_asc)
                        acc = ch_code_asc[pch_code_asc_idx] >> 4

                        while True:
                            self.offs2D34[acc] = count & 0xFF
                            acc += add
                            if acc >= 0x100:
                                break
                    else:
                        bits_asc -= 6
                        self.ch_bits_asc[pch_bits_asc_idx] = bits_asc

                        add = (1 << bits_asc)
                        acc = ch_code_asc[pch_code_asc_idx]

                        while True:
                            self.offs2E34[acc] = count & 0xFF
                            acc += add
                            if acc >= 0x80:
                                break

                else:
                    bits_asc -= 8
                    self.ch_bits_asc[pch_bits_asc_idx] = bits_asc

                    add = (1 << bits_asc)
                    acc = ch_code_asc[pch_code_asc_idx] >> 8

                    while True:
                        self.offs2EB4[acc] = count & 0xFF
                        acc += add
                        if acc >= 0x100:
                            break

            pch_code_asc_idx -= 1
            count -= 1

    # -----------------------------------------------------------------------------
    #  Removes given number of bits in the bit buffer. New bits are reloaded from
    #  the input buffer, if needed.
    #  Returns: PKDCL_OK:         Operation was successful
    #           PKDCL_STREAM_END: There are no more bits in the input buffer
    def _waste_bits(self, n_bits):
        #  If number of bits required is less than number of (bits in the buffer) ?
        if n_bits <= self.extra_bits:
            self.extra_bits -= n_bits
            self.bit_buff >>= n_bits
            return PKDCL_OK

        #  Load input buffer if necessary
        self.bit_buff >>= self.extra_bits
        if self.in_pos == self.in_bytes:
            return PKDCL_STREAM_END

        #  Update bit buffer
        self.in_pos += 1
        self.bit_buff |= (self.in_buff[self.in_pos - 1] << 8)
        self.bit_buff >>= (n_bits - self.extra_bits)
        self.extra_bits = (self.extra_bits - n_bits) + 8
        return PKDCL_OK

    # -----------------------------------------------------------------------------
    #  Decodes next literal from the input (compressed) data.
    #  Returns : 0x000: One byte 0x00
    #            0x001: One byte 0x01
    #            ...
    #            0x0FF: One byte 0xFF
    #            0x100: Repetition, length of 0x02 bytes
    #            0x101: Repetition, length of 0x03 bytes
    #            ...
    #            0x304: Repetition, length of 0x206 bytes
    #            0x305: End of stream
    #            0x306: Error
    def _decode_lit(self):
        #  Test the current bit in byte buffer. If is not set, simply return the next 8 bits.
        if self.bit_buff & 1 != 0:
            #  Remove one bit from the input data
            if self._waste_bits(1):
                return 0x306

            #  The next 8 bits hold the index to the length code table
            length_code = self.length_codes[self.bit_buff & 0xFF]

            #  Remove the apropriate number of bits
            if self._waste_bits(self.len_bits[length_code]):
                return 0x306

            #  Are there some extra bits for the obtained length code ?
            extra_length_bits = self.ex_len_bits[length_code]
            if extra_length_bits != 0:
                extra_length = self.bit_buff & ((1 << extra_length_bits) - 1)

                if self._waste_bits(extra_length_bits):
                    if (length_code + extra_length) != 0x10E:
                        return 0x306
                length_code = self.len_base[length_code] + extra_length

            #  In order to distinguish uncompressed byte from repetition length,
            #  we have to add 0x100 to the length.
            return length_code + 0x100

        #  Remove one bit from the input data
        if self._waste_bits(1):
            return 0x306

        #  If the binary compression type, read 8 bits and return them as one byte.
        if self.ctype == CMP_BINARY:
            uncompressed_byte = self.bit_buff & 0xFF

            if self._waste_bits(8):
                return 0x306
            return uncompressed_byte

        #  When ASCII compression ...
        if self.bit_buff & 0xFF:
            value = self.offs2C34[self.bit_buff & 0xFF]

            if value == 0xFF:
                if self.bit_buff & 0x3F != 0:
                    if self._waste_bits(4):
                        return 0x306

                    value = self.offs2D34[self.bit_buff & 0xFF]
                else:
                    if self._waste_bits(6):
                        return 0x306

                    value = self.offs2E34[self.bit_buff & 0x7F]
        else:
            if self._waste_bits(8):
                return 0x306

            value = self.offs2EB4[self.bit_buff & 0xFF]

        return 0x306 if self._waste_bits(self.ch_bits_asc[value]) else value

    # -----------------------------------------------------------------------------
    #  Decodes the distance of the repetition, backwards relative to the
    #  current output buffer position
    def _decode_dist(self, rep_length):
        #  Next 2-8 bits in the input buffer is the distance position code
        dist_pos_code = self.dist_pos_codes[self.bit_buff & 0xFF]
        dist_pos_bits = self.dist_bits[dist_pos_code]
        if self._waste_bits(dist_pos_bits):
            return 0

        if rep_length == 2:
            #  If the repetition is only 2 bytes length,
            #  then take 2 bits from the stream in order to get the distance
            distance = (dist_pos_code << 2) | (self.bit_buff & 0x03)
            if self._waste_bits(2):
                return 0
        else:
            #  If the repetition is more than 2 bytes length,
            #  then take "dsize_bits" bits in order to get the distance
            distance = (dist_pos_code << self.dsize_bits) | (self.bit_buff & self.dsize_mask)
            if self._waste_bits(self.dsize_bits):
                return 0
        return distance + 1


# -----------------------------------------------------------------------------
#  Main exploding function.
def explode(input_buffer):
    return PkDecompressor(input_buffer).expand()
