import urllib
import os
import sys
import xml.etree.ElementTree as ET

import TESOZip
import Simplebencode

OUTDIR = 'UPDATE_OUT/'

HOST_LAUNCHER = 'launcher.bethesda.net'
HOST_LIVEPATCHER = 'live.patcher.elderscrollsonline.com'

def _reporthook(numblocks, blocksize, filesize, url=None):
    base = os.path.basename(url)
    try:
        percent = min((numblocks * blocksize * 100) / filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b" * 70)
    sys.stdout.write("%-66s%3d%%" % (base, percent))

def geturl(url, dst):
    print "[+] Get url '%s' to '%s'" % (url, dst)
    if sys.stdout.isatty():
        urllib.urlretrieve(url, dst, lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url))
        sys.stdout.write('\n')
    else:
        urllib.urlretrieve(url, dst)

class Release:
    def __init__(self, idd, sha1, name):
        self.id = idd
        self.sha1 = sha1
        self.name = name
        self.patchdatetime = ""
        self.metafileurl = ""
        self.esoname = ""
        self.outdir = OUTDIR + "/" + str(self.id) + "/"
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        self.status = ""

    #def GetMetaFile(self):
    #    try:
    #        geturl(self.metafileurl, self.outdir + self.metafile)
    #    except:
    #        return
    #    buf = open(self.outdir + self.metafile, "rb").read()
    #    if buf == "File not found.\"":
    #        print "[-] %s not found" % self.metafile
    #        return
    #    l_file = TESOZip.extract_files(self.outdir + self.metafile, self.outdir)
    #    if "metafile.solid" not in l_file:
    #        print "[-] no metafile.solid file extracted :("
    #        print l_file
    #        return
    #    data = open(self.outdir + "metafile.solid", "rb").read()
    #    torrent = Simplebencode.bedecode(data)
    #    self.zipfiles = ["/".join(file["path"]) for file in torrent["info"]["files"]]
    #    if len(self.zipfiles) > 2:
    #        print "[-] more than 2 zipfiles!"
    #        print self.zipfiles
    #        return
    #    for zipfile in self.zipfiles:
    #        geturl(torrent["reliable"] + zipfile, self.outdir + zipfile)
    #    self.mainzip = next(x for x in self.zipfiles if x.endswith('.zip'))
    #    self.archive = next(x for x in self.zipfiles if x.endswith('.z01'))
    #    l_file = TESOZip.list_files(self.outdir + self.mainzip)
    #    #print torrent["reliable"]
    #    #for file in torrent["info"]["files"]:
    #    #    if "/".join(file["path"]).endswith(".zip") == True:
    #    #        l_file = TESOZip.list_files( self.outdir + "/".join(file["path"]))
    #    for info in l_file:
    #        if info.filename == "client/eso.exe":
    #            print "[+] offset : 0x%08X" % info.header_offset
    #            TESOZip.extract_comp_file(self.outdir + self.archive, info.header_offset, info.compress_size, self.outdir)

    def CheckContentPkg(self):
        buf = open(self.outdir + self.metafile, "rb").read()
        if buf == "File not found.\"":
            return False
        return True

    def CheckMetaFile(self):
        if os.path.exists(self.outdir + self.metafile) == False:
            print "[-] solidpkg not present"
            try:
                geturl(self.metafileurl, self.outdir + self.metafile)
            except:
                return False
        else:
            print "[+] solidpkg already downloaded"
        if self.CheckContentPkg() == False:
            print "[-] %s contains \"File not found.\"" % self.metafile
            return False
        return True

    def GetTorrentInfo(self):
        data = open(self.outdir + "metafile.solid", "rb").read()
        torrent = Simplebencode.bedecode(data)
        self.torrenturl = torrent["reliable"]
        self.zipfiles = ["/".join(file["path"]) for file in torrent["info"]["files"]]
        if len(self.zipfiles) > 2:
            print "[-] more than 2 zipfiles!"
            print self.zipfiles
            return False
        self.mainzip = next(x for x in self.zipfiles if x.endswith('.zip'))
        self.archive = next(x for x in self.zipfiles if x.endswith('.z01'))
        return True

    def GetMetaFile(self):
        if self.CheckMetaFile() == True:
            tz = TESOZip.TESOZip(self.outdir + self.metafile, self.outdir)
            if tz.ExtractFile("metafile.solid") == False:
                print "[-] no metafile.solid file extracted"
                return False
            return True
        else:
            return False

    def DownloadTorrent(self):
        for zipfile in self.zipfiles:
            try:
                geturl(self.torrenturl + zipfile, self.outdir + zipfile)
            except:
                return False
        return True

    def CheckTorrent(self):
        for zipfile in self.zipfiles:
            if os.path.exists(self.outdir + zipfile) == False:
                try:
                    geturl(self.torrenturl + zipfile, self.outdir + zipfile)
                except:
                    return False
            # TODO ADD CHECK TESO ZIP ARCHIVE
        return True

    def Process(self):
        self.esoname = self.patchdatetime + "-" + self.name + "-" + "eso.exe"
        print "[+] Processing"
        print self
        if self.GetMetaFile() == False:
            print "[-] GetMetaFile() failed"
            return False
        if self.GetTorrentInfo() == False:
            print "[-] GetTorrentInfo() failed"
            return False
        if self.CheckTorrent() == False:
            print "[-] CheckTorrent() failed"
            return False
        tz = TESOZip.TESOZip(self.outdir + self.mainzip, self.outdir, True)
        if tz.ExtractFile("client/eso.exe") == False:
            print "[-] Can't extract eso.exe"
            return False
        print "eso.exe extracted!"
        self.status = ""
        return True
        #pass

    def __str__(self):
        b = "[+] id            : %s\n" % self.id
        b += "[+] sha1          : %s\n" % self.sha1
        b += "[+] name          : %s\n" % self.name
        b += "[+] patchdatetime : %s\n" % self.patchdatetime
        b += "[+] metafileurl   : %s\n" % self.metafileurl
        b += "[+] esoname       : %s" % self.esoname
        return b

def ExtractManifest():
    releases = {}
    tz = TESOZip.TESOZip(OUTDIR + "game_player.patchmanifest", OUTDIR)
    if tz.ExtractFile("manifest.xml") == False:
        print "[-] fail extracting xml"
        sys.exit(1)
    tree = ET.parse(OUTDIR + "manifest.xml")
    root = tree.getroot()
    for release in root.iter('Release'):
        rlz_id = release.find('Id').text
        rlz_sha1 = release.find('SHA1').text
        rlz_name = release.find('Name').text
        releases[rlz_id] = Release(rlz_id, rlz_sha1, rlz_name)
    for i in xrange(0, len(releases)):
        for release in root.iter('ReleaseUpdatePath'):
            rlz_from = release.find('From').text
            rlz_to = release.find('To').text
            #if int(rlz_from) == (i - 1) and int(rlz_to) == i:
            if int(rlz_from) == -1 and int(rlz_to) == i:
                for extradataitem in release.iter('ExtraDataItem'):
                    if extradataitem.find('Key').text == 'ZoPatchDateTime':
                        releases[str(i)].patchdatetime = extradataitem.find('Value').text.split(" ")[0].replace("-", "_")
                    if extradataitem.find('Key').text == 'MetafileUrl':
                        releases[str(i)].metafileurl = extradataitem.find('Value').text
                        releases[str(i)].metafile = releases[str(i)].metafileurl.split("/")[-1]
    return releases

def GetManifest():
    if not os.path.exists(OUTDIR):
        os.mkdir(OUTDIR)
    geturl("http://launcher.bethesda.net/ESO/game_player.patchmanifest", OUTDIR + "game_player.patchmanifest")


#urllib.urlretrieve("http://launcher.bethesda.net/ESO/game_player.patchmanifest", OUTDIR + "game_player.patchmanifest")

GetManifest()
releases = ExtractManifest()
#for k in releases:
#    print releases[k]
#    print "-" * 20
#for k in releases:
#    releases[k].GetMetaFile()
#releases["3"].GetMetaFile()
releases["10"].Process()

#releases["95"].GetMetaFile()

#for i in xrange(6, 10):
#   releases[str(i)].GetMetaFile()

sys.exit(42)





#print releases
print len(releases)





sys.exit(42)
