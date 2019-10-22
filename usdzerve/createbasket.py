#!/usr/bin/python

import os, shutil, sys, struct, time, binascii, json
from collections import namedtuple, defaultdict

def computeExtraFieldSize(fileoffset):
    extra_headersize = 2*2
    usd_data_alignment = 64

    paddingbuffersize = extra_headersize + usd_data_alignment       # Maximum size of buffer needed for padding bytes.

    required_padding = usd_data_alignment - (fileoffset % usd_data_alignment)
    if required_padding == usd_data_alignment:
        required_padding = 0
    elif required_padding < extra_headersize:
        required_padding += usd_data_alignment  # If the amount of padding needed is too small to contain the header, bump the size up while maintaining the required alignment.

    if required_padding == 0:
        return bytearray([])

    extrafield = [0] * required_padding
    extrafield[0] = 0x86
    extrafield[1] = 0x19
    extrafield[2] = required_padding - extra_headersize
    extrafield[3] = 0

    return bytearray(extrafield)

FileInfo = namedtuple('FileInfo', 'dostime dosdate CRC filesize filename extra headerstart')

def storeFile(arc_fp, name, filepath):
    localHeaderFmt = "<4s5H3L2H"
    localHeaderSize = struct.calcsize(localHeaderFmt)

    filename = os.path.basename(filepath)

    st = os.stat(filepath)
    filesize = st.st_size
    mtime = time.localtime(st.st_mtime)
    dt = mtime[0:6]
    dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
    dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)

    headerstart = arc_fp.tell()
    extra = computeExtraFieldSize(headerstart + localHeaderSize + len(name))

    with open(filepath, 'rb') as f:
        filedata = f.read()
        CRC = binascii.crc32(filedata) & 0xffffffff

        header = struct.pack(localHeaderFmt,
               "PK\003\004",      # local file header signature     4 bytes  (0x04034b50)
                10,               # version needed to extract       2 bytes
                0,                # general purpose bit flag        2 bytes 
                0,                # compression method              2 bytes
                dostime,          # last mod file time              2 bytes
                dosdate,          # last mod file date              2 bytes
                CRC,              # crc-32                          4 bytes
                filesize,         # compressed size                 4 bytes 
                filesize,         # uncompressed size               4 bytes
                len(name),        # file name length                2 bytes
                len(extra))       # extra field length              2 bytes

        arc_fp.write(header)
        arc_fp.write(name)
        arc_fp.write(extra)

        arc_fp.write(filedata)

        return FileInfo(dostime, dosdate, CRC, filesize, filename, extra, headerstart)

    return None


def storeCentralDirectoryHeader(arc_fp, fileInfo):
    centralDirectoryHeaderFmt = "<4s6H3L5H2L"
    centralDirectoryHeaderSize = struct.calcsize(centralDirectoryHeaderFmt)

    header = struct.pack(centralDirectoryHeaderFmt,
        "PK\001\002",                    # central file header signature   4 bytes  (0x02014b50)
        0,                               # version made by                 2 bytes
        10,                              # version needed to extract       2 bytes
        0,                               # general purpose bit flag        2 bytes
        0,                               # compression method              2 bytes
        fileInfo.dostime,                # last mod file time              2 bytes
        fileInfo.dosdate,                # last mod file date              2 bytes
        fileInfo.CRC,                    # crc-32                          4 bytes
        fileInfo.filesize,               # compressed size                 4 bytes
        fileInfo.filesize,               # uncompressed size               4 bytes
        len(fileInfo.filename),          # file name length                2 bytes
        len(fileInfo.extra),             # extra field length              2 bytes
        0,                               # file comment length             2 bytes
        0,                               # disk number start               2 bytes
        0,                               # internal file attributes        2 bytes
        0,                               # external file attributes        4 bytes
        fileInfo.headerstart)            # relative offset of local header 4 bytes

    arc_fp.write(header)
    arc_fp.write(fileInfo.filename)
    arc_fp.write(fileInfo.extra)
    
def storeEndOfCentralDirectoryRecord(arc_fp, fileInfos, centralDirectoryStart):
    endOfCentralDirectoryRecordFmt = "<4s4H2LH"
    endOfCentralDirectoryRecordSize = struct.calcsize(endOfCentralDirectoryRecordFmt)

    centralDirectorySize = arc_fp.tell() - centralDirectoryStart

    eoCentralDirectory = struct.pack(endOfCentralDirectoryRecordFmt,
                                    "PK\005\006",                    # end of central dir signature    4 bytes  (0x06054b50)
                                    0,                               # number of this disk             2 bytes
                                    0,                               # number of the disk with the start of the central directory      2 bytes
                                    len(fileInfos),                  # total number of entries in the central directory on this disk   2 bytes
                                    len(fileInfos),                  # total number of entries in the central directory                2 bytes
                                    centralDirectorySize,            # size of the central directory   4 bytes
                                    centralDirectoryStart,           # offset of start of central directory with respect to the starting disk number 4 bytes
                                    0)                               # .ZIP file comment length        2 bytes

    arc_fp.write(eoCentralDirectory)

def createPackageUsda(assetPath, usdaFilename, files):
    prefixTemplate = """#usda 1.0
(
    defaultPrim = "Object"
    upAxis = "Y"
    customLayerData = {{
        asset[] assetLibrary = {0}
    }}
)

def Xform "Object" (
    variants = {{
        string Assets = "{1}"
    }}
    prepend variantSets = "Assets"
)
{{
    variantSet "Assets" = {{"""

    perAssetTemplate = """
        "{0}" (
            prepend references = @{1}@
        ) {{

        }}"""

    postFixTemplate = """
    }}
}}
"""
    fileBasenames = str([os.path.basename(name) for (index, name) in enumerate(files)]).replace("'", "@")
    firstname = os.path.splitext(os.path.basename(files[0]))[0]
    usda = prefixTemplate.format(fileBasenames, firstname)
    for (index, filename) in enumerate(files):
        variantSetName = os.path.splitext(os.path.basename(filename))[0]
        usda += perAssetTemplate.format(variantSetName, os.path.basename(filename))
    usda += postFixTemplate.format()

    file = open(os.path.join(assetPath, usdaFilename) , "w")
    file.write(usda)
    file.close() 
    return 


if len(sys.argv) < 3:
    print 'usage:\n\tpython\tcreatebasket.py outputFile,asset1[,asset2[,...]] assetPath\n\t\tasset names and outputFile should not include the ".usdz" extension\n'
    sys.exit(0)

name_list = sys.argv[1].split(',')

assetPath = sys.argv[2]
target_usdz = name_list[0]+".usdz"
target_usda = name_list[0]+".usda"

#check if items appear multiple times and then create file duplicates, that are later removed
cloneCounters = defaultdict(int)
assetlist = []
for assetID in name_list[1:]:
    cloneIndex = cloneCounters[assetID]
    if cloneIndex == 0:
        assetlist.append(assetID+".usdz")
    else:
        assetName = assetID+"-"+str(cloneIndex)+".usdz"
        try:
            shutil.copyfile(os.path.join(assetPath,assetID+".usdz"), os.path.join(assetPath,assetName))
            assetlist.append(assetName)
        except:
            pass
    cloneCounters[assetID] += 1

# produce the USDA file
createPackageUsda(assetPath, target_usda, assetlist)

# create USDZ archive with ZIP
fileInfos = []
with open(os.path.join(assetPath,target_usdz), 'wb') as arc_fp:
    fileInfo = storeFile(arc_fp, target_usda, os.path.join(assetPath,target_usda))
    fileInfos.append(fileInfo)
    for fileName in assetlist:
        fileInfo = storeFile(arc_fp, fileName, os.path.join(assetPath,fileName))
        fileInfos.append(fileInfo)

    centralDirectoryStart = arc_fp.tell()

    for fileInfo in fileInfos:
        storeCentralDirectoryHeader(arc_fp, fileInfo)

    storeEndOfCentralDirectoryRecord(arc_fp, fileInfos, centralDirectoryStart)

# remove USDA file not needed any longer
os.remove(os.path.join(assetPath,target_usda))

# also remove temp duplicates
# \todo this does not scale well on high traffic websites
for key, count in cloneCounters.items():
    for idx in range(1,count):
        os.remove(os.path.join(assetPath,key+"-"+str(idx)+".usdz"))


# return USDZ URL to client
print 'Content-Type: application/json'
print ''
print json.dumps('models/'+target_usdz)

# test it with :
# localhost/usdzerve/createbasket.py?UUID-BASKET-1,chair,chair,desk,Ivar
