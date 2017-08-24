#!/usr/bin/env python2

'''
OTP PWN
@author: derbenoo
'''

import curses
import string
import sys
import binascii

class OTPPwn:
    
    def __init__(self, fd, keylen, filesize):
        self.fd= fd # file descriptor for encrypted file
        self.keylen= keylen # key length
        self.filesize= filesize # number of bytes in encrypted file
        self.blockwidth= 25 # width of one ciphertext block
        self.infoBarHeight= 4 # height of the info bar on the bottom of the screen
        self.blockpadding= 3 # padding in between ciphertext blocks
        self.blocklenX= self.blockwidth+self.blockpadding # overall width of a block
        self.blocklenY= self.keylen+self.blockpadding+2 # overall height of a block
        self.printable= string.digits+string.uppercase+string.lowercase+string.punctuation+" " # characters to be printed to screen
        self.viewOffset= 0 # offset into the file
        self.blockViewOffset= 0 # offset inside a block for blocks that are larger than the screen height, also affects the shown key
        self.key= "\x00"*self.keylen # key (initialize with zero bytes)
        self.keyHistory= [self.key] # list of keys for reverting key changes
        self.plainHistory= [] # history of plaintext for reverting key changes and crib dragging
        self.rawmode= False # whether or not the current key is applied to the ciphertext blocks

    def makePrintable(self, text):
        return ''.join([x if x in self.printable else "." for x in text])
    
    def drawBlock(self, y, x, text, offset, blockOffset):
        for i, line in enumerate(self.makeBlock(text, offset, blockOffset)):
            if i > 1 and i < self.keylen + 2:
                if ord(self.key[i-2+blockOffset]) != 0 and not self.rawmode:
                    self.pad.addstr(y+i, x, line, curses.A_BOLD)
                    continue
            
            self.pad.addstr(y+i, x, line)
        
    def makeBlock(self, text, offset= 0, blockOffset= 0):
        # add table header
        res= []
        res.append("POS   | HEX | DEC | STR |")
        res.append("-------------------------")
        
        for i, ch in enumerate(text):
            if i < blockOffset:
                continue
            res.append("%5d | %02x  | %3d | %2s  |" % ((i+offset), ord(ch), ord(ch), self.makePrintable(ch)))
        
        return res 
    
    def xorkey(self, text):
        res= ""
        for i, c in enumerate(text):
            res+= chr(ord(self.key[i]) ^ ord(c)) 
        
        return res
    
    def drawPad(self):
        offset= self.viewOffset
        self.fd.seek(offset)
        ylen, xlen= self.pad.getmaxyx()
        self.pad.clear()

        for ypos in range(0, ylen-self.blocklenY, self.blocklenY):
            for xpos in range(0, xlen-self.blocklenX, self.blocklenX):
                if offset > self.filesize:
                    return

                text= f.read(self.keylen)
                
                # apply XOR key if raw mode is off
                if not self.rawmode:
                    text= self.xorkey(text)
                
                self.drawBlock(ypos, xpos, text, offset, self.blockViewOffset)
                offset+= self.keylen
        
    
    def clearStatusBar(self):
        self.stdscr.move(self.ymax-2, 0)
        self.stdscr.clrtoeol()
        
    def clearInput(self):
        self.stdscr.move(self.ymax-1, 0)
        self.stdscr.clrtoeol()
    
    def updateKey(self, newKey, plain, offset):
        self.keyHistory.append(newKey)
        self.plainHistory.append((plain, offset))
        self.key= newKey
    
    def revertKeyChange(self, silent= False):
        if len(self.keyHistory) > 1:
            self.keyHistory.pop()
            self.plainHistory.pop()
            self.key= self.keyHistory[-1]
            if not silent:
                self.printInfo("reverted to last key")
        else:
            self.printErr("cannot revert key changes, already at initial key")
    
    def cribdrag(self, forward= True):
        if len(self.plainHistory) > 0:
            plain, offset= self.plainHistory[-1]
            self.revertKeyChange(silent= True)
            self.applyPlaintext(plain, offset+ (1 if forward else -1))

    def applyPlaintext(self, plain, offset):
        # calculate resulting key bytes
        key= ""
        self.fd.seek(offset)
        cipher= self.fd.read(len(plain))
        for i, c in enumerate(cipher):
            key+= chr(ord(c) ^ ord(plain[i]))
        
        # apply changes to stored key
        newKey= self.key
        for i, c in enumerate(key):
            keyIndex= (offset+i) % self.keylen
            newKey= newKey[:keyIndex]+c+newKey[keyIndex+1:]
        self.updateKey(newKey, plain, offset)

    def processPlain(self, text):
        cmds= text.split(" ")
        if len(cmds) >= 3:
            if cmds[0] == "p" or cmds[0] == "plain":
                plain= ' '.join(cmds[2:])
            elif cmds[0] == "phex" or cmds[0] == "plainhex":
                try:
                    hexnums= ''.join(cmds[2:])
                    plain= binascii.unhexlify(hexnums)
                except:
                    self.printErr("could not convert plain hex to bytes")
                    return
            else:
                return 
            
            try:
                # get plaintext offset
                offset= int(cmds[1])
            except ValueError:
                self.printErr("offset must be an integer!")
                return

            if len(plain) > self.keylen:
                self.printErr("plaintext longer than key!")
                return
            
            self.applyPlaintext(plain, offset)

        else:
            self.printErr("syntax: p | phex [pos] [plaintext (in hex)]")    
        
    def drawStatusBar(self):
        self.clearStatusBar()
        statusBar="KEY: " + ' '.join([hex(ord(c))[2:].ljust(2, "0") for c in self.key[self.blockViewOffset:self.blockViewOffset+self.charsPerBlock]])
        self.stdscr.addstr(self.ymax-2, 0, statusBar[:self.xmax])    
    
    def printErr(self, text):
        self.stdscr.addstr(self.ymax-1, 0, "[!] "+text)
    
    def printInfo(self, text):
        self.stdscr.addstr(self.ymax-1, 0, text)
    
    def refresh(self):
        # draw pad
        self.drawPad()
        self.drawStatusBar()
        self.stdscr.refresh()
        self.pad.refresh(0,0, 0,0, self.ymax-self.infoBarHeight,self.xmax)
        self.stdscr.move(self.ymax-1, 0)
    
    def dumpResultToFile(self, input):
        if not len(input.split(" ")) == 2:
            self.printErr("syntax: d(ump) [filename]")
            return
        
        filename= input.split(" ")[1]
        filename= str(filename)
        self.fd.seek(0)
        text= self.fd.read()
        res= ''.join([chr(ord(x) ^ ord(self.key[i % len(self.key)])) for i,x in enumerate(text)])
        
        with open(filename, "w") as f:
            f.write(res)
            
        self.printInfo("dumped decrypted bytes to '"+filename+"'!")
    
    def run(self, stdscr):
        self.stdscr= stdscr
        
        # get window width and height
        self.ymax, self.xmax= stdscr.getmaxyx()

        #initialize analyzer pad (show at least one row of blocks)
        self.pad= curses.newpad(self.ymax if self.ymax > self.blocklenY else self.blocklenY+1, self.xmax)
        self.blocksPerLine= self.xmax / self.blocklenX
        self.charsPerBlock= self.ymax - self.infoBarHeight - 2
        self.refresh()
        
        # get user input
        while 1:
            input= self.stdscr.getch()
            self.clearInput()
            
            # input command mode
            if input == ord(":"):
                self.clearInput()
                curses.echo()
                stdscr.addch(self.ymax-1, 0, ":")
                input= stdscr.getstr(self.ymax-1, 1)
                curses.noecho()
                self.clearInput()
                
                # quit
                if input == "q":
                    break
                
                # plain input
                if input[:1] == "p":
                    self.processPlain(input)
                    
                # dump result to file
                if input[:1] == "d" or input[:5] == "dump":
                    self.dumpResultToFile(input)
                
            # toggle raw mode
            if input == ord("m"):
                if self.rawmode:
                    self.rawmode= False
                    self.printInfo("MODE: applying key")
                else:
                    self.rawmode= True
                    self.printInfo("MODE: original")
            
            # revert key changes
            if input == ord("r") or input == ord("u"):
                self.revertKeyChange()

            # crib drag
            if input == ord("c") or input == ord("n"):
                self.cribdrag()
            if input == ord("C") or input == ord("N"):
                self.cribdrag(forward= False)
            
            # jump to start/end of file
            if input == ord("g"):
                self.viewOffset= 0
            if input == ord("G"):
                self.viewOffset= self.filesize-self.blocksPerLine * self.keylen

            # scroll view up
            if input == ord('k'):
                self.viewOffset-= self.keylen* self.blocksPerLine
                if self.viewOffset < 0:
                    self.viewOffset= 0

            # scroll block up
            if input == ord('K'):
                if self.blockViewOffset > 0:
                    self.blockViewOffset-= 1
            
            # scroll view down
            if input == ord('j'):
                if self.viewOffset+ self.keylen* self.blocksPerLine < self.filesize:
                    self.viewOffset+= self.keylen* self.blocksPerLine
                else:
                    self.printInfo("reached end of file.")

            # scroll block down
            if input == ord('J'):
                if self.blockViewOffset < self.keylen - self.charsPerBlock:
                    self.blockViewOffset += 1
                else:
                    self.printInfo("reached end of block.")

            self.refresh()

if __name__ == "__main__":
    # display help
    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print "Usage: otp_pwn.py [encrypted file] [key length]"
        sys.exit()

    if len(sys.argv) < 2:
        filename= raw_input("Encrypted file: ")
    else:
        filename= sys.argv[1]

    if len(sys.argv) < 3:
        keylen= int(raw_input("Length of the key: "))
    else:
        keylen= int(sys.argv[2])

    with open(filename, "r") as f:   
        # size of file
        f.seek(0, 2)
        filesize= f.tell() 
        otpPwn= OTPPwn(f, keylen, filesize)
        curses.wrapper(otpPwn.run)