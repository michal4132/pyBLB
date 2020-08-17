import platform
import sys
import os
import struct
import json
import wave
from PIL import Image
if(platform.system() == "Linux"):
    import pklib
else:
    import pwexplode

class Entry:
    fileHash = None
    type = None
    comprType = None
    extData = None
    timeStamp = None
    offset = None
    diskSize = None #size of file in BLB
    size = None #real size of file

def unpack(file, count, dtype):
    return struct.unpack(dtype, file.read(count))[0]

class BLBExtract:
    #TODO Remove this
    def unpack(self, count, dtype):
        return struct.unpack(dtype, self.blb.read(count))[0]

    def __init__(self, BLBpath, debug=False):
        self.blb = open(BLBpath, "rb")
        self.debug = debug
        self.files = []
        self.extDataOffsets = []
        self.json_file = True #Not used for now

        self.json_data = {}
        self.json_data['files'] = []

        #Get file size
        self.blb.seek(0, os.SEEK_END)
        self.blb_size = self.blb.tell()
        self.blb.seek(0,0)

        #Header
        id1 = self.unpack(4, "I") #UINT32LE
        id2 = self.unpack(2, "H") #UINT16LE
        self.extDataSize = self.unpack(2, "H") #UINT16LE
        self.fileSize = self.unpack(4, "I") #UINT32LE
        self.fileCount = self.unpack(4, "I") #UINT32LE

        self.json_data['header'] = [id1, id2, self.extDataSize, self.fileSize, self.fileCount]

        #Check if file is correct
        if(id1 != 0x2004940 or id2 != 7 or self.fileSize != self.blb_size):
            print("Error: Corrupted BLB")
            return False

        if(args.verbose):
            print("ID1: {}\nID2: {}\nextDataSize: {}\nfileSize: {}\nfileCount: {}".format(id1, id2, self.extDataSize, self.fileSize, self.fileCount))


    def id2fileName(self, id):
        fileName = "file{}".format(id)
        if self.files[id].type == 2:
            fileName = "file{}_image.nhi".format(id)
        elif self.files[id].type == 3:
            fileNmae = "files{}_palette".format(id)
        elif self.files[id].type == 7 or self.files[id].type == 8:
            fileName = "file{}_audio".format(id)
        elif self.files[id].type == 10:
            fileName = "file{}_video".format(id)
        return fileName

    def load_files(self):

        #Load file hashes from BLB
        for i in range(self.fileCount):
            fileHash = self.unpack(4, "I") #UINT32LE
            entry = Entry()
            entry.fileHash = fileHash
            self.files.append(entry)
            if(self.json_file):
                self.json_data['files'].append({})
                self.json_data['files'][i]['fileHash'] = fileHash

        #Load file records
        for i in range(self.fileCount):
            self.files[i].type = self.unpack(1, "b") #Byte
            self.files[i].comprType = self.unpack(1, "b") #Byte
            self.files[i].extData = None

            extDataOffset = self.unpack(2, "H") #UINT16LE
            self.extDataOffsets.append(extDataOffset)

            self.files[i].timeStamp = self.unpack(4, "I") #UINT32LE
            self.files[i].offset = self.unpack(4, "I") #UINT32LE
            self.files[i].diskSize = self.unpack(4, "I") #UINT32LE
            self.files[i].size = self.unpack(4, "I") #UINT32LE

            if(self.json_file):
                self.json_data['files'][i]['type'] = self.files[i].type
                self.json_data['files'][i]['comprType'] = self.files[i].comprType
                self.json_data['files'][i]['extDataOffset'] = extDataOffset
                self.json_data['files'][i]['extData'] = ""
                self.json_data['files'][i]['timeStamp'] = self.files[i].timeStamp
                self.json_data['files'][i]['offset'] = self.files[i].offset
                self.json_data['files'][i]['diskSize'] = self.files[i].diskSize
                self.json_data['files'][i]['size'] = self.files[i].size
                self.json_data['files'][i]['realPath'] = out_dir+self.id2fileName(i)

            if(args.verbose or args.print):
                print("Num: {} FileHash: {} FileType: {} ComprType: {} extDataOffset: {} timestamp: {} offset: {} diskSize: {} size: {}".format(i, self.files[i].fileHash, self.files[i].type, self.files[i].comprType, extDataOffset, self.files[i].timeStamp, self.files[i].offset, self.files[i].diskSize, self.files[i].size))

    def load_extdata(self):
        #Load ext data
        #extData is used to decompress audio files and maybe something else
        if(self.extDataSize > 0):
            extData = self.blb.read(self.extDataSize)
            for i in range(self.fileCount):
                #BLBs can use 4 bytes or 1 byte
                if(self.extDataOffsets[i] > 0):
                   #a.blb - 1 byte
                    if(self.extDataSize == len(self.files)):
                        self.files[i].extData = extData[self.extDataOffsets[i] - 1]
                    else:
                        #Other BLBs use 4 bytes
                        #Read 4 bytes from extData
                        self.files[i].extData = bytearray(4)
                        self.files[i].extData[0] = extData[self.extDataOffsets[i] - 1]
                        self.files[i].extData[1] = extData[self.extDataOffsets[i]    ]
                        self.files[i].extData[2] = extData[self.extDataOffsets[i] + 1]
                        self.files[i].extData[3] = extData[self.extDataOffsets[i] + 2]
                        if(self.json_file):
                            self.json_data['files'][i]['extData'] = struct.unpack("I", self.files[i].extData)[0]
                else:
                    self.files[i].extData = b"\x00\x00\x00\x00"
                if(args.verbose):
                    print("Num: {} extData: {}".format(i, struct.unpack("I", self.files[i].extData)[0]))


    def create_json(self, json_path='data.json'):
        with open(json_path, 'w') as outfile:
            json.dump(self.json_data, outfile)

    def extract(self, fileNum):
        file = self.files[fileNum]
        fileData = None
        self.blb.seek(file.offset)

        #Uncompressed file
        if(file.comprType == 1):
            fileData = self.blb.read(file.diskSize)

        #Compressed file
        elif(file.comprType == 3):
            compressed = self.blb.read(file.diskSize)

            if(platform.system() == "Linux"):
                fileData = pklib.decompress(compressed)
            else:
                fileData = pwexplode.explode(compressed)

        return fileData

    def __exit__(self):
        self.blb.close()

class ImageBLB:
    def __init__(self, file_path, debug=False):
        self.file = open(file_path, "rb")
        self.debug = debug
        self.palette = []
        self.pixels = []
        self.w = None
        self.h = None
        self.reportedWidth = None
        self.rle = None
        self.position_x = 0
        self.position_y = 0

        self.BF_RLE            = 1
        self.BF_HAS_DIMENSIONS = 2
        self.BF_HAS_POSITION   = 4
        self.BF_HAS_PALETTE    = 8
        self.BF_HAS_IMAGE      = 16

    def parseSprite(self):
        flags = unpack(self.file, 2, "H")

        self.rle = flags & self.BF_RLE

        self.palette = []

        #Read file resolution
        if (flags & self.BF_HAS_DIMENSIONS):
            self.w = unpack(self.file, 2, "H")
            self.h = unpack(self.file, 2, "H")

        #Position on screen
        if (flags & self.BF_HAS_POSITION):
            self.position_x = unpack(self.file, 2, "H")
            self.position_y = unpack(self.file, 2, "H")

        #Read palette
        if (flags & self.BF_HAS_PALETTE):
            for i in range(256):
                r = unpack(self.file, 1, "B")
                g = unpack(self.file, 1, "B")
                b = unpack(self.file, 1, "B")
                p = unpack(self.file, 1, "B")
                self.palette.append((r, g, b))
        else:
            for i in range(256):
                self.palette.append((i, i, i))

        if(self.debug):
            print("type: {} rle: {} W: {} H: {} x: {} y: {}".format(flags, self.rle, self.w, self.h, self.position_x, self.position_y))

#        if(flags & self.BF_HAS_IMAGE):
#            print("pixels")

        # Some images report wrong width
        # so we need to check it
        # if wrong we calculate correct width
        curr = self.file.tell()
        self.file.seek(0, os.SEEK_END)
        file_size = self.file.tell()
        self.file.seek(curr)

        pixels_size = file_size - curr

        #reportedWidth is used to crop image
        self.reportedWidth = self.w

        while(((self.w + 1) * self.h) <= pixels_size):
            self.w += 1


        return True

    def unpackSpriteNormal(self):
        self.pixels = []
        for i in range(self.w*self.h):
            #Convert palette index to RGB
            num = unpack(self.file, 1, "B")
            decode = self.palette[num]
            self.pixels.append(decode)

        return True

    def unpackSpriteRle(self):
        rows = unpack(self.file, 2, "H")
        chunks = unpack(self.file, 2, "H")

        if(self.debug):
            print("rows: {} chunks: {}".format(rows, chunks))

        copy = 0
        skip = 0

        pixels_encoded = [0] * (self.w*self.h)

        dest = 0
        destPitch = self.w# same as image width

        while True:
            for r in range(rows):
                for c in range(chunks):
                    skip = unpack(self.file, 2, "H")
                    copy = unpack(self.file, 2, "H")
                    for i in range(copy):
                        value = unpack(self.file, 1, "B")
                        pixels_encoded[dest + skip + i] = value
#                    print("skip: {} copy: {} rows: {} chunks: {}".format(skip, copy, r, c))
                dest += destPitch

            rows = unpack(self.file, 2, "H")
            chunks = unpack(self.file, 2, "H")

            if(rows == 0):
                break

        self.pixels = []
        for i in range(len(pixels_encoded)):
            #Convert palette index to RGB
            decode = self.palette[pixels_encoded[i]]
            self.pixels.append(decode)

        return True

    def isRle(self):
        return self.rle

    def get_pixels(self):
        return self.pixels

    def get_palette(self):
        return self.palette

    def set_palette(self, palette):
        self.palette = palette

    def get_resolution(self):
        return (self.reportedWidth, self.w, self.h)

    def __exit__(self):
        self.file.close()

def decompress_audio(data, shift):
    out = []
    iCurValue = 0

    for i in data:
        one = i
        #Emulate integer overflow
        if(one > 127):
            one -= 256
        elif(one < -128):
            one += 256

        iCurValue += one
        if((iCurValue<<shift) < 32768 and (iCurValue<<shift) >= -32768):
            out.append( struct.pack("h", iCurValue<<shift) )
    return out



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Extract Neverhood BLB')
    parser.add_argument('blb_file')
    parser.add_argument('-p', '--print', action="store_true",
        help="print data info and exit")
    parser.add_argument('-o', '--output', default="files/",
        help="output directory")
    parser.add_argument('-c', '--create', action='store_true',
        help='create json file for file reconstruction')
    parser.add_argument('-d', '--decode', action='store_true',
        help='convert files to more "modern" format')
    parser.add_argument('-v', '--verbose', action="store_true",
        help='show debug info')

    args = parser.parse_args()

    if(args.output.endswith("/")):
        out_dir = args.output
    else:
        out_dir = args.output + "/"


    #Create directories for unpacked files
    os.makedirs(out_dir, exist_ok=True)
    if(args.decode):
        os.makedirs(out_dir+"mp4", exist_ok=True)
        os.makedirs(out_dir+"wav", exist_ok=True)
        os.makedirs(out_dir+"png", exist_ok=True)

    #Create extractor object
    extractor = BLBExtract(args.blb_file)

    #Load files from BLB
    extractor.load_files()

    #Load ext data from BLB
    extractor.load_extdata()

    if(args.print):
        blb.close()
        sys.exit(0)

    #Create JSON with BLB info
    #This JSON is used to repack files
    if(args.create):
        extractor.create_json()

    files_processed = 0
    print("0/{}      ".format(extractor.fileCount), end="\r")
    for i in range(extractor.fileCount):
        f = open(out_dir+extractor.id2fileName(i), "wb")

        #Extract file with number i
        data = extractor.extract(i)
        if(data is not None):

            # 2 - images
            if(extractor.files[i].type == 2):
                #Save original file
                f.write(data)
                f.close()
                #Decode image to png
                if(args.decode):

                    image_path = out_dir+extractor.id2fileName(i)
                    image = ImageBLB(image_path)
                    image.parseSprite()

                    if(image.isRle()):
                        image.unpackSpriteRle()
                    else:
                        image.unpackSpriteNormal()

                    pixels = image.get_pixels()

                    reportedWidth, w, h = image.get_resolution()

                    #Save as png
                    new_image = Image.new("RGB", (w, h))
                    new_image.putdata(pixels)
                    new_image = new_image.crop((0,0, reportedWidth, h))
                    new_image.save(out_dir+'png/file'+str(i)+'.png')

            #7 and 8 - audio
            elif(extractor.files[i].type == 7 or extractor.files[i].type == 8):
                shift = extractor.files[i].extData

                #File is compressed only if shift value is smaller than 0xFF
                if(shift < 255):
                    data = decompress_audio(data, shift)
                    for sample in data:
                        f.write(sample)
                else:
                    f.write(data)

                #Decode audio to WAV
                if(args.decode):
                    wav_file = wave.open(out_dir+'wav/file'+str(i)+'.wav', 'w')
                    wav_file.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                    if(shift < 255):
                        for sample in data:
                            wav_file.writeframes(sample)
                    else:
                        wav_file.writeframes(data)
                    wav_file.close()
                f.close()

            #10 - Video
            elif(extractor.files[i].type == 10):
                f.write(data)
                f.close()
                #Decode video to mp4 using ffmpeg
                if(args.decode):
                    ffmpeg_cmd = "ffmpeg -i {0}{1} -vcodec libx264 {0}mp4/{1}.mp4".format(out_dir, extractor.id2fileName(i))
                    out = os.popen(ffmpeg_cmd).read()

            #others
            else:
                f.write(data)
                f.close()
        files_processed += 1
        print("{}/{}      ".format(files_processed, extractor.fileCount), end="\r")
    print()
