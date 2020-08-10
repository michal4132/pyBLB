import argparse
import subprocess
import sys
import os
import struct
import wave

#Download and build
#https://github.com/madler/zlib/tree/master/contrib/blast
BLAST_PATH = "./blast"

parser = argparse.ArgumentParser(description='Extract Neverhood BLB')
parser.add_argument('blb_file')
parser.add_argument('-o', '--output', default="files/",
    help="output directory")
parser.add_argument('-d', '--decode', action='store_true',
    help='convert files to more "modern" format')
parser.add_argument('-v', '--verbose', action="store_true",
    help='show debug info')

args = parser.parse_args()

### Args
### TODO: Make this more clear

if args.verbose:
    debug = True
else:
    debug = False

if args.decode:
    decode = True
else:
    decode = False

if(args.output.endswith("/")):
    out_dir = args.output
else:
    out_dir = args.output + "/"

os.makedirs(out_dir, exist_ok=True)
if(decode):
    os.makedirs(out_dir+"mp4", exist_ok=True)
    os.makedirs(out_dir+"wav", exist_ok=True)

class Entry:
    fileHash = None
    type = None
    comprType = None
    extData = None
    timeStamp = None
    offset = None
    diskSize = None
    size = None

blb = open(args.blb_file, "rb")

#Get file size
blb.seek(0, os.SEEK_END)
blb_size = blb.tell()
blb.seek(0,0)

#Header
id1 = blb.read(4) #UINT32LE
id2 = blb.read(2) #UINT16LE
extDataSize = blb.read(2) #UINT16LE
fileSize = blb.read(4) #UINT32LE
fileCount = blb.read(4) #UINT32LE

#Unpack bytes
id1 = struct.unpack("I", id1)[0]
id2 = struct.unpack("H", id2)[0]
extDataSize = struct.unpack("H", extDataSize)[0]
fileSize = struct.unpack("I", fileSize)[0]
fileCount = struct.unpack("I", fileCount)[0]


#Check if file is correct
if(id1 != 0x2004940 or id2 != 7 or fileSize != blb_size):
    print("Error: Corrupted BLB")

if(debug):
    print("ID1: {}\nID2: {}\nextDataSize: {}\nfileSize: {}\nfileCount: {}".format(id1, id2, extDataSize, fileSize, fileCount))

#Load file hashes
files = []

for i in range(fileCount):
    fileHash = blb.read(4) #UINT32LE
    fileHash = struct.unpack("I", fileHash)[0]
    entry = Entry()
    entry.fileHash = fileHash
    files.append(entry)
#    print(fileHash)


extDataOffsets = []

#Load file records

for i in range(fileCount):
    files[i].type = struct.unpack("b", blb.read(1))[0] #Byte
    files[i].comprType = struct.unpack("b", blb.read(1))[0] #Byte
    files[i].extData = None
    extDataOffsets.append(struct.unpack("H", blb.read(2))[0]) #UINT16LE
    files[i].timeStamp = struct.unpack("I", blb.read(4))[0] #UINT32LE
    files[i].offset = struct.unpack("I", blb.read(4))[0] #UINT32LE
    files[i].diskSize = struct.unpack("I", blb.read(4))[0] #UINT32LE
    files[i].size = struct.unpack("I", blb.read(4))[0] #UINT32LE

    if(debug):
        print("Num: {} Type: {} ComprType: {} extDataOffset: {} timestamp: {} offset: diskSize: {} size: {}".format(i, files[i].type, files[i].comprType, 0, files[i].timeStamp, files[i].offset, files[i].diskSize, files[i].size))

#Load ext data
#extData is used to decompress audio files and maybe something else
if(extDataSize > 0):
    extData = blb.read(extDataSize)
#    extData = struct.unpack('b', extData)
    for i in range(fileCount):
        if(extDataOffsets[i] > 0):
            files[i].extData = extData[extDataOffsets[i] - 1]
        else:
            files[i].extData = None
        if(debug):
            print("Num: {} extData: {}".format(i, files[i].extData))

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
        if((iCurValue<<shift) < 32768):
            out.append( struct.pack("h", iCurValue<<shift) )
    return out


def extract(fileNum):
    file = files[fileNum]
    fileData = None
    blb.seek(file.offset)

    #Uncompressed file
    if(file.comprType == 1):
        fileData = blb.read(file.diskSize)

    #Compressed file
    elif(file.comprType == 3):
        compressed = blb.read(file.size)

        #There's some issue with blast, some files can't be decompressed, so we kill process after 5 seconds
        try:
            p = subprocess.Popen(["timeout", "5" , BLAST_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(os.devnull, 'wb'))
            p.stdin.write(compressed)
            fileData = p.communicate()[0]
            p.stdin.close()
            p.stdout.close()
        except:
            fileData = None

    return fileData

if __name__ == '__main__':
    files_processed = 0
    print("0/{}      ".format(fileCount), end="\r")
    for i in range(fileCount):
        f = open(out_dir+"file"+str(i), "wb")
        data = extract(i)
        if(data is not None):
            #7 and 8 - audio
            if(files[i].type == 7 or files[i].type == 8):
                shift = files[i].extData
                if(shift != 255):
                    data = decompress_audio(data, shift)
                    for sample in data:
                        f.write(sample)
                else:
                    f.write(data)
                if(decode):
                    wav_file = wave.open(out_dir+'wav/file'+str(i)+'.wav', 'w')
                    wav_file.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                    if(shift != 255):
                        for sample in data:
                            wav_file.writeframes(sample)
#                    else:
#                        wav_file.writeframes()
                    wav_file.close()

            #10 - Video
            elif(files[i].type == 10):
                f.write(data)
                if(decode):
                    ffmpeg_cmd = "ffmpeg -i {0}file{1} -vcodec libx264 {0}mp4/file{1}.mp4".format(out_dir, str(i))
                    out = os.popen(ffmpeg_cmd).read()
            #others
            else:
                f.write(data)
        f.close()
        files_processed += 1
        print("{}/{}      ".format(files_processed, fileCount), end="\r")
    print()

blb.close()