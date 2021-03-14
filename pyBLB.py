import platform
import sys
import os
import struct
import json
import wave
from PIL import Image
import pklib

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

    def __init__(self, BLBpath, debug=False, json_file=True):
        self.blb = open(BLBpath, "rb")
        self.debug = debug
        self.files = []
        self.extDataOffsets = []
        self.json_file = json_file #Not used for now

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
            return

        if(debug):
            print("ID1: {}\nID2: {}\nextDataSize: {}\nfileSize: {}\nfileCount: {}".format(id1, id2, self.extDataSize, self.fileSize, self.fileCount))


    def id2fileName(self, id):
        fileName = "file{}".format(id)
        if self.files[id].type == 2:
            fileName = "file{}_image.nhi".format(id)
        elif self.files[id].type == 3:
            fileName = "file{}_palette".format(id)
        elif self.files[id].type == 4:
            fileName = "file{}_anim".format(id)
        elif self.files[id].type == 6:
            fileName = "file{}.txt".format(id)
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

            if(self.debug):
                print("Num: {} FileHash: {} FileType: {} ComprType: {} extDataOffset: {} timestamp: {} offset: {} diskSize: {} size: {}".format(i, self.files[i].fileHash, self.files[i].type, self.files[i].comprType, extDataOffset, self.files[i].timeStamp, self.files[i].offset, self.files[i].diskSize, self.files[i].size))

    def load_extdata(self):
        #Load ext data
        #extData is used to decompress audio files and contains width+height for images
        if(self.extDataSize > 0):
            extData = self.blb.read(self.extDataSize)
            for i in range(self.fileCount):
                #BLBs can use 4 bytes or 1 byte
                if(self.extDataOffsets[i] > 0):
                   #a.blb - 1 byte
                    if(self.extDataSize == len(self.files)):
                        if(self.extDataOffsets[i] > self.extDataSize):
                            self.files[i].extData = 0xFF
                        else:                    
                            self.files[i].extData = extData[self.extDataOffsets[i] - 1]
                        if(self.json_file):
                            self.json_data['files'][i]['extData'] = self.files[i].extData
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
                if(self.debug):
                    print("Num: {} extData: {}".format(i, self.files[i].extData))

    def getFile(self, hash):
        for idx, val in enumerate(self.files):

            if(val.fileHash == hash):                
                return self.extract(idx), val.extData


    def create_json(self, json_path='data.json'):
        with open(json_path, 'w') as outfile:
            json.dump(self.json_data, outfile)

    def extract(self, fileNum):
        file = self.files[fileNum]
        fileData = None
        self.blb.seek(file.offset)

        #Uncompressed file
        if(file.comprType == 1):
            if(file.size == 0):
                fileData = self.blb.read(file.diskSize)
            else:
                fileData = self.blb.read(file.size)
        #Compressed file
        elif(file.comprType == 3):
            if(file.type == 8):
                compressed = self.blb.read(file.size)
            else:
                compressed = self.blb.read(file.diskSize)

            fileData = pklib.decompress(compressed)

        #Dirty hack for dummy files
        elif(file.comprType == 101):
            fileData,extDataUnused = self.getFile(file.diskSize)

        return fileData

    def __exit__(self):
        self.blb.close()

class ImageBLB:
    def __init__(self, input_data, is_file=True, debug=False):
        self.is_file = is_file
        if(is_file):
            file_path = input_data
            self.file = open(file_path, "rb")
        else:
            #TODO: RENAME FILE_PATH
            self.data = bytearray(input_data)
        self.debug = debug
        self.palette = []
        self.pixels = []
        self.w = None
        self.h = None
        self.reportedWidth = None
        self.rle = None
        self.flags = None
        self.position_x = 0
        self.position_y = 0

        self.BF_RLE            = 1
        self.BF_HAS_DIMENSIONS = 2
        self.BF_HAS_POSITION   = 4
        self.BF_HAS_PALETTE    = 8
        self.BF_HAS_IMAGE      = 16
        
    def unPack(self, length, dtype):
        if(self.is_file):
            return unpack(self.file, length, dtype)
        else:
            tmp = bytearray(b'')
            for i in range(length):
                tmp+=bytes([self.data[0]])
                del self.data[0]
            return struct.unpack(dtype, tmp)[0]
            

    def parseSprite(self):
        self.flags = self.unPack(2, "H")

        self.rle = self.flags & self.BF_RLE

        self.palette = []

        #Read file resolution
        if (self.flags & self.BF_HAS_DIMENSIONS):
            self.w = self.unPack(2, "H")
            self.h = self.unPack(2, "H")

        #Position on screen
        if (self.flags & self.BF_HAS_POSITION):
            self.position_x = self.unPack(2, "H")
            self.position_y = self.unPack(2, "H")

        #Read palette
        if (self.flags & self.BF_HAS_PALETTE):
            for i in range(256):
                r = self.unPack(1, "B")
                g = self.unPack(1, "B")
                b = self.unPack(1, "B")
                p = self.unPack(1, "B")
                self.palette.append((r, g, b))
        else:
            for i in range(256):
                self.palette.append((i, i, i))

        if(self.debug):
            print("type: {} rle: {} W: {} H: {} x: {} y: {}".format(self.flags, self.rle, self.w, self.h, self.position_x, self.position_y))

#        if(flags & self.BF_HAS_IMAGE):
#            print("pixels")

#       TODO REMOVE THIS
#        # Some images report wrong width
#        # so we need to check it
#        # if wrong we calculate correct width
#        if(self.is_file):
#            curr = self.file.tell()
#            self.file.seek(0, os.SEEK_END)
#            file_size = self.file.tell()
#            self.file.seek(curr)

#            pixels_size = file_size - curr

#            #reportedWidth is used to crop image
#            self.reportedWidth = self.w

#            while(((self.w + 1) * self.h) <= pixels_size):
#                self.w += 1


        return True

    def unpackSpriteNormal(self):
        self.pixels = []
        for i in range(self.w*self.h):
            #Convert palette index to RGB
            num = self.unPack(1, "B")
            decode = self.palette[num]
            self.pixels.append(decode)

        return True

    def unpackSpriteRle(self, w, h):
    
        rows = self.unPack(2, "H")
        chunks = self.unPack(2, "H")

        if(self.debug):
            print("rows: {} chunks: {}".format(rows, chunks))

        copy = 0
        skip = 0

        pixels_encoded = [0] * (w*h)

        dest = 0
        destPitch = w# same as image width

        while True:
            for r in range(rows):
                for c in range(chunks):
                    skip = self.unPack(2, "H")
                    copy = self.unPack(2, "H")
                    for i in range(copy):
                        value = self.unPack(1, "B")
                        pixels_encoded[dest + skip + i] = value
                    if(self.debug):
                        print("skip: {} copy: {} rows: {} chunks: {}".format(skip, copy, r, c))
                dest += destPitch

            rows = self.unPack(2, "H")
            chunks = self.unPack(2, "H")

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

    def get_flags(self):
        return self.flags

    def set_palette(self, palette):
        self.palette = palette

    def get_resolution(self):
        return (self.reportedWidth, self.w, self.h)

    def get_position(self):
        return (self.position_x, self.position_y)

    def __exit__(self):
        if(self.is_file):
            self.file.close()


class AnimFrameInfo:
    frameHash = None
    counter = None
    drawOffset_x = None
    drawOffset_y = None
    drawOffset_width = None
    drawOffset_height = None
    deltaX = None
    deltaY = None
    collisionBoundsOffset_x = None
    collisionBoundsOffset_y = None
    collisionBoundsOffset_width = None
    collisionBoundsOffset_height = None
    spriteDataOffs = None

class Animation:
    def __init__(self, input_data, extData, hash, debug=False):
        self.debug = debug
        self.file_pointer = 0
        self.spriteDataPos = None
        self.palette = []
        self.input_data = input_data
        self.hash = hash
        self.frames = []
        self.spriteDataOfs = None
        
        #Load width and height from extData

        w = bytearray()
        for i in range(2):
            w.append(extData[i])

        h = bytearray()
        for i in range(2):
            h.append(extData[i+2])

        self.w = struct.unpack("H", w)[0]
        self.h = struct.unpack("H", h)[0]


    def unPack(self, count, dtype):
        tmp = b''
        for i in range(count):
            tmp+=bytes([self.input_data[self.file_pointer]])
            self.file_pointer+=1
        return struct.unpack(dtype, tmp)[0]

        
    def parseAnim(self):
        animListCount = self.unPack(2, "H")
        animInfoStartOfs = self.unPack(2, "H")
        self.spriteDataOfs = self.unPack(4, "I")
        paletteDataOfs = self.unPack(4, "I")

        if(self.debug):
            print("animListCount: {} animInfoStartOfs: {} spriteDataOfs: {} paletteDataOfs: {}".format(animListCount, animInfoStartOfs, self.spriteDataOfs, paletteDataOfs))

        for animListIndex in range(animListCount):
            hash1 = self.unPack(4, "I")
            if(hash1 == self.hash):
                break

        self.spriteDataPos = self.spriteDataOfs

        frameCount = self.unPack(2, "H") 
        frameListStartOfs = self.unPack(2, "H")

        frameListPos = animInfoStartOfs

        if(self.debug):
            print("frame_count: {} frame_list_pos: {} frameListStartOfs: {}".format(frameCount, frameListPos, frameListStartOfs))

        if(paletteDataOfs > 0):
            if(self.debug):
                print("Palette present")
            paletteDataPos = paletteDataOfs
            self.file_pointer = paletteDataPos
            for i in range(256):
                r = self.unPack(1, "B")
                g = self.unPack(1, "B")
                b = self.unPack(1, "B")
                p = self.unPack(1, "B")
                self.palette.append((r, g, b))

        #Jump to position with frames data
        self.file_pointer = animInfoStartOfs

        for frameIndex in range(frameCount):
            frameInfo = AnimFrameInfo()
    
            frameInfo.frameHash = self.unPack(4, "I")
            frameInfo.counter = self.unPack(2, "H")

            frameInfo.drawOffset_x = self.unPack(2, "h")
            frameInfo.drawOffset_y = self.unPack(2, "h")
            frameInfo.drawOffset_width = self.unPack(2, "H")
            frameInfo.drawOffset_height = self.unPack(2, "H")

            frameInfo.deltaX = self.unPack(2, "H")
            frameInfo.deltaY = self.unPack(2, "H")

            frameInfo.collisionBoundsOffset_x = self.unPack(2, "H")
            frameInfo.collisionBoundsOffset_y = self.unPack(2, "H")
            frameInfo.collisionBoundsOffset_width = self.unPack(2, "H")
            frameInfo.collisionBoundsOffset_height = self.unPack(2, "H")

            #Unused data
            self.unPack(2, "H")

            frameInfo.spriteDataOffs = self.unPack(4, "I")

            self.frames.append(frameInfo)
    
            if(self.debug):
                print("id : {}, off: {}, hash: {}, counter: {}, w: {}, y: {}, pos_x: {}, pos_y: {}".format(frameIndex, frameInfo.spriteDataOffs, frameInfo.frameHash, frameInfo.counter, frameInfo.drawOffset_width, frameInfo.drawOffset_height, frameInfo.drawOffset_x, frameInfo.drawOffset_y))

    def getFrame(self, num):
    
        self.file_pointer = self.spriteDataOfs + self.frames[num].spriteDataOffs
        
        image = ImageBLB(self.input_data[self.file_pointer:], is_file=False)
    
        image.set_palette(self.palette)
        image.unpackSpriteRle(self.frames[num].drawOffset_width, self.frames[num].drawOffset_height)

        pixels = image.get_pixels()
        
        return self.frames[num], pixels
        
    def numOfFrames(self):
        return len(self.frames)
        
    def setPalette(self, palette):
        self.palette = palette
    
    def getPalette(self):
        return self.palette
    
class BLBInserter:
    def __init__(self, BLBpath, debug=False):
        self.blb = open(BLBpath, "wb")
        self.debug = debug
        self.files = []
        self.curr_offset = 0
        self.doneFileHashes = False
        self.filesInfoOffset = None
        self.file_size_offset = None
        self.extDataSize = None
        self.extDataOffsets = []
        self.fileCount = None
        self.json_file = True #Not used for now

        blb_json = open('data.json', "r")
        self.json_data = json.load(blb_json)

    def get_fileCount(self):
        return int(self.json_data['header'][4])

    def write_header(self):
        #Header
        id1 = struct.pack("I", int(self.json_data['header'][0])) #0x2004940 #UINT32LE
        id2 = struct.pack("H", int(self.json_data['header'][1])) #7 #UINT16LE
        #These valies should be written after processing files
        self.extDataSize = struct.pack("H", int(self.json_data['header'][2])) #UINT16LE
        fileSize = struct.pack("I", int(self.json_data['header'][3])) #UINT32LE
        self.fileCount = struct.pack("I", int(self.json_data['header'][4])) #UINT32LE

        self.blb.seek(0, 0)
    
        self.blb.write(id1)
        self.blb.write(id2)
        self.blb.write(self.extDataSize)
        self.file_size_offset = self.blb.tell()
        self.blb.write(fileSize)
        self.blb.write(self.fileCount)

        if(self.debug):
            print("ID1: {}\nID2: {}\nextDataSize: {}\nfileSize: {}\nfileCount: {}".format(id1, id2, self.extDataSize, fileSize, self.fileCount))

    def write_fileHashes(self):
        for file in self.json_data['files']:
            #Create files in memory for later
            entry = Entry()
            entry.fileHash = file['fileHash']
            entry.type = file['type']
            entry.comprType = file['comprType']
            #Dirty fix for audio
            if(file['type'] == 7 or file['type'] == 8):
                entry.extData = 255 # 0xFF means audio is not compressed
            else:                
                entry.extData = file['extData']
            entry.extDataOffset = file['extDataOffset']
            entry.timeStamp = file['timeStamp']
            entry.offset = file['offset']
            entry.size = file['size']
            entry.diskSize = file['diskSize']
            entry.realPath = file['realPath']
            self.files.append(entry)

            #Write file hash to BLB
            fileHash = struct.pack("I", entry.fileHash)
            self.blb.write(fileHash)
        self.filesInfoOffset = self.blb.tell()

    def compress_files(self):
        #Compress files
        os.makedirs("files_out/", exist_ok=True)
        for i in range(len(self.files)):
            if(self.files[i].comprType == 3):
                #Update uncompressed size
                self.files[i].size = os.path.getsize(self.files[i].realPath)

                out_path = "files_out/"+self.files[i].realPath.split("/")[1]

                #Open file and compress
                d_file = open(self.files[i].realPath, "rb")
                compressed = pklib.compress(d_file.read())
                c_file = open(out_path, "wb")
                c_file.write(compressed)
                c_file.close()

                #Update compressed size
                self.files[i].diskSize = os.path.getsize(out_path)

                #Change file location to compressed file
                self.files[i].realPath = out_path

                print("Compressed: {}".format(i), end="\r")
            else:
                self.files[i].diskSize = os.path.getsize(self.files[i].realPath)
                self.files[i].size = os.path.getsize(self.files[i].realPath)

    def writeFilesInfo(self):
        #Write file records

        if not self.filesInfoOffset:
            print("Error: Write File Hashes first")
            return False

        self.blb.seek(self.filesInfoOffset)

        for i in range(len(self.files)):
            type = struct.pack("b", self.files[i].type)
            self.blb.write(type)

            comprType = struct.pack("b", self.files[i].comprType)
            self.blb.write(comprType)

            extDataOffset = struct.pack("H", self.files[i].extDataOffset)
            self.blb.write(extDataOffset)

            timeStamp = struct.pack("I", self.files[i].timeStamp)
            self.blb.write(timeStamp)

            offset = struct.pack("I", self.files[i].offset)
            self.blb.write(offset)

            diskSize = struct.pack("I", self.files[i].diskSize)
            self.blb.write(diskSize)

            size = struct.pack("I", self.files[i].size)
            self.blb.write(size)


            if(self.debug):
                print("Num: {} Type: {} ComprType: {} extDataOffset: {} timestamp: {} offset: {} diskSize: {} size: {}".format(i, self.files[i].type, self.files[i].comprType, extDataOffset, self.files[i].timeStamp, self.files[i].offset, self.files[i].diskSize, self.files[i].size))

    def writeExtData(self):
        #Write ext data
        #extData is used to decompress audio files and maybe something else
        extDataSizeInt = struct.unpack("H", self.extDataSize)[0]

        extData = bytearray(extDataSizeInt)

        for i in range(len(self.files)):
            if(self.files[i].extDataOffset > 0):
                extDataPayload = struct.pack("I", self.files[i].extData)
                if(extDataSizeInt == len(self.files)):
                    extData[self.files[i].extDataOffset - 1] = extDataPayload[0]
                else:
                    for extByteNum in range(4):
                        extData[self.files[i].extDataOffset - 1 + extByteNum] = extDataPayload[extByteNum]
        self.blb.write(extData)

        self.curr_offset = self.blb.tell()

    def insert(self, fileNum):
        self.files[fileNum].offset = self.curr_offset
        file = self.files[fileNum]
        self.blb.seek(file.offset)

        try:
            source_file = open(file.realPath, "rb")
        except:
            print("No file: {}".format(fileNum))
            return

        #Get file size
        source_file.seek(0, os.SEEK_END)
        source_size = source_file.tell()
        source_file.seek(0,0)

        if(source_size <= file.diskSize * 2):
            data = source_file.read(file.diskSize)
            self.blb.write(data)
        else:
            print("Error: file size incorrect file num: {} expected: {} real: {}".format(fileNum, file.diskSize, source_size))
        self.curr_offset += (file.diskSize)

        source_file.close()
        return True

    def write_size(self):
        self.blb.seek(0, os.SEEK_END)
        blb_size = self.blb.tell()

        self.blb.seek(self.file_size_offset)
        fileSize = struct.pack("I", int(blb_size)) #UINT32LE
        self.blb.write(fileSize)


    def __exit__(self):
        self.blb.close()

def decompress_audio(data, shift):
    out = bytearray()
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
            out+=struct.pack("h", iCurValue<<shift)
    return out



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Unpack/Pack Neverhood BLB')
    parser.add_argument('blb_file')
    parser.add_argument('-i', '--insert', action="store_true",
        help="pack BLB file")
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
        os.makedirs(out_dir+"gif", exist_ok=True)

    files_processed = 0

    #Pack
    if(args.insert):
        inserter = BLBInserter(args.blb_file)
        inserter.write_header()
        inserter.write_fileHashes()
        inserter.compress_files()
        inserter.writeFilesInfo()
        inserter.writeExtData()


        fileCount = inserter.get_fileCount()

        print("0/{}                   ".format(fileCount), end="\r")
        for i in range(fileCount):
            inserter.insert(i)
            files_processed += 1
            print("{}/{}                   ".format(files_processed, fileCount), end="\r")
        inserter.writeFilesInfo()


        inserter.write_size()
    #Unpack    
    else:
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
                        image = ImageBLB(image_path, debug=False)
                        image.parseSprite()

                        reportedWidth, w, h = image.get_resolution()

                        if(image.isRle()):
                            image.unpackSpriteRle(w, h)
                        else:
                            image.unpackSpriteNormal()

                        pixels = image.get_pixels()

                        #Save as png
                        new_image = Image.new("RGB", (w, h))
                        new_image.putdata(pixels)
                        #TODO REMOVE
#                        new_image = new_image.crop((0,0, reportedWidth, h))
                        new_image.save(out_dir+'png/file'+str(i)+'.png')
                        
                # 4 - animations
                elif(extractor.files[i].type == 4):
                    #Save original file
                    f.write(data)
                    f.close()

                    if(args.decode):           
                        extData = extractor.files[i].extData
                        file_hash = extractor.files[i].fileHash

                        anim = Animation(data, extData, file_hash, debug=args.debug)
                            
                        try:
                            anim.parseAnim()
                    
                            #Get max width and height
                            x = []
                            y = []
                            for j in range(anim.numOfFrames()):
                                frame, pixels = anim.getFrame(j)
  
                                x.append(frame.drawOffset_width)
                                y.append(frame.drawOffset_height)

                            width = max(x)
                            height = max(y)
                    
                    
                            imgs = []
                            for j in range(anim.numOfFrames()):
                                frame, pixels = anim.getFrame(j)

                                bg = Image.new('RGB', (width, height))

                                img =  Image.new("RGB", (frame.drawOffset_width, frame.drawOffset_height))
                                img.putdata(pixels)
    
                                bg.paste(img, (0, 0))

                                imgs.append(bg)

                            imgs[0].save(out_dir+'gif/file'+str(i)+'.gif', save_all=True, append_images=imgs[1:], optimize=False, duration=40, loop=0)
                        except:
                            pass
                    
                #7 and 8 - audio
                elif(extractor.files[i].type == 7 or extractor.files[i].type == 8):
                    shift = extractor.files[i].extData

                    #File is compressed only if shift value is smaller than 0xFF
                    if(shift < 255):
                        data = decompress_audio(data, shift)
                        
                    f.write(data)

                    #Decode audio to WAV
                    if(args.decode):
                        wav_file = wave.open(out_dir+'wav/file'+str(i)+'.wav', 'w')
                        wav_file.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                        wav_file.writeframes(data)
                        wav_file.close()
                    f.close()

                #10 - Video
                elif(extractor.files[i].type == 10):
                    f.write(data)
                    f.close()
                    #Decode video to mp4 using ffmpeg
                    if(args.decode):
                        ffmpeg_cmd = "ffmpeg -i {0}{1} -vcodec rawvideo -pix_fmt yuv420p {0}mp4/{1}.avi".format(out_dir, extractor.id2fileName(i))
                        out = os.popen(ffmpeg_cmd).read()

                #others
                else:
                    f.write(data)
                    f.close()
            files_processed += 1
            print("{}/{}      ".format(files_processed, extractor.fileCount), end="\r")
    print()
