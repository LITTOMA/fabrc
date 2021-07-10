# fabrc
A script for parsing Fab Resource *(What is Fab?)* found in Pokemon Pokémon Art Academy

# Requirements
* python 3
* python-fire

# Usage
## fabfnt.py
You can generate a *.fabfnt file and the corresponding font image(s) with this script.
``` shell
fabfnt.py FONTNAME CHARSET_PATH CHARSET_ENCODING FACEPATH SIZE SAVEDIR BASELINE [IMAGEGLYPHS]...
```
FONTNAME: The internal name of the generated font file.
CHARSET_PATH: Path to the charset file which you want to included in the generated font.
CHARSET_ENCODING: Charset file encoding.
FACEPATH: Font file path (*.ttf, *.ttc, etc.).
SIZE: Font pixel size.
SAVEDIR: Where the output files being saved to.
BASELINE: Baseline position.
[IMAGEGLYPHS]...: Special glyphs, such as button icons. The file name should be the glyph's charcode in decimal.

## fabndl.py
### Pack a folder to a fab resource bundle
``` shell
fabndl.py pack PATH PATH_OUT
```
* PATH: Path to the folder
* PATH_OUT: Path to the output file.


### Repack a bundle
``` shell
fabndl.py repack PATH LOAD_DIR PATH_OUT
```
* PATH: Path to an existing bundle file.
* LOAD_DIR: Path to the folder you want to load the replacement files.
* PATH_OUT: Path to the output file.


### Unpack a bundle
``` shell
fabndl.py unpack PATH PATH_OUT <flags>
  optional flags:        --decompress
```
* PATH: Path to the bundle file.
* PATH_OUT: Path to the unpacked folder.
* --decompress: Decompress the lz4 compressed file data if specified.


## fabtex.py
Convert a ctpk file to a fabtex file. Supports L4/A4/ETC1A4 pixel format only.
``` shell
fabtex.py CTPK FABTEX
```
