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
usage: pyBLB.py [-h] [-p] [-o OUTPUT] [-c] [-d] [-v] blb_file

Extract Neverhood BLB

positional arguments:
  blb_file

optional arguments:
  -h, --help            show this help message and exit
  -p, --print           print data info and exit
  -o OUTPUT, --output OUTPUT
                        output directory
  -c, --create          create json file for file reconstruction
  -d, --decode          convert files to more "modern" format
  -v, --verbose         show debug info
```
## Progress:
- [x] BLB unpacking
- [x] Image decoding
- [ ] Image palette 
- [x] Video decoding
- [x] Audio decoding
- [ ] Animation decoding

- [x] BLB packing
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
