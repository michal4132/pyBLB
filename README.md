# pyBLB

pyBLB is a Python library for extracting Neverhood BLB files.

## Installation
```bash
git clone https://github.com/michal4132/pyBLB
```
Linux:
```bash
cd pklib
make
```

## Usage

```bash
usage: pyBLB.py [-h] [-i] [-p] [-o OUTPUT] [-c] [-d] [-v] blb_file

Unpack/Pack Neverhood BLB

positional arguments:
  blb_file

optional arguments:
  -h, --help            show this help message and exit
  -i, --insert          pack BLB file
  -p, --print           print data info and exit
  -o OUTPUT, --output OUTPUT
                        output directory
  -c, --create          create json file for file reconstruction
  -d, --decode          convert files to more "modern" format
  -v, --verbose         show debug info

```
Unpack:
```bash
python3 pyBLB.py -c i.blb
```
Pack:
```bash
python3 pyBLB.py -i i.blb
```

## Progress
- [x] BLB unpacking
- [x] Image decoding
- [ ] Image palette 
- [x] Video decoding
- [x] Audio decoding
- [ ] Animation decoding

- [x] BLB packing NOTE: Packing only possible on Linux
- [ ] Video encoding
- [ ] Audio encoding
- [ ] Image encoding
- [ ] Animation encoding

## BLBs
a.blb  - sounds and music

c.blb  - cut scenes and other video files

i.blb  - sprites, backgrounds

m.blb  - making of videos

hd.blb - radio spin video, UI elements

t.blb  - first person videos

s.blb  - level data, animation data (messages) ?????


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
