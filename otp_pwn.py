#!/usr/bin/env python2

'''
@author: derbenoo

OTP PWN


'''

import curses
import string
import sys


class OTPPwn:
    
    def __init__(self, fd, keylen, filesize):
        self.fd= fd
        self.keylen= keylen
        self.filesize= filesize
        self.blockwidth= 25
        self.infoBarHeight= 3
        self.blockpadding= 3
        self.blocklenX= self.blockwidth+self.blockpadding
        self.blocklenY= self.keylen+self.blockpadding+2
        self.printable= string.digits+string.uppercase+string.lowercase+string.punctuation+" "
        
        self.viewOffset= 0
        self.key= "\x00"*self.keylen
        self.keyHistory= [self.key]
        self.rawmode= False

        
    
    def makePrintable(self, text):
        return ''.join([x if x in self.printable else "." for x in text])
    
    def drawBlock(self, y, x, text, offset):
        for i, line in enumerate(self.makeBlock(text, offset)):
            self.pad.addstr(y+i, x, line)
        
    def makeBlock(self, text, offset= 0):
        # add table header
        res= []
        res.append("POS   | HEX | DEC | STR |")
        res.append("-------------------------")
        
        for i, ch in enumerate(text):
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
                
                self.drawBlock(ypos, xpos, text, offset)
                offset+= self.keylen
        
    
    def clearStatusBar(self):
        self.stdscr.move(self.ymax-2, 0)
        self.stdscr.clrtoeol()
        
    def clearInput(self):
        self.stdscr.move(self.ymax-1, 0)
        self.stdscr.clrtoeol()
    
    def updateKey(self, newKey):
        self.keyHistory.append(newKey)
        self.key= newKey
    
    def revertKeyChange(self):
        if len(self.keyHistory) > 1:
            self.keyHistory.pop()
            self.key= self.keyHistory[-1]
            self.printInfo("reverted to last key")
        else:
            self.printErr("cannot revert key changes, already at initial key")
    
    def processPlain(self, text):
        cmds= text.split(" ")
        if len(cmds) >= 3:
            if cmds[0] == "p" or cmds[0] == "plain":
                plain= ' '.join(cmds[2:])
            elif cmds[0] == "phex" or cmds[0] == "plainhex":
                try:
                    hexnums= ''.join(cmds[2:])
                    # check plaintext length
                    if len(hexnums) % 2:
                        self.printErr("length of plaintext must be even numbered (hex format)")
                        return

                    plain= ""
                    # convert plaintext input from hex to byte
                    for i in range(0, len(hexnums), 2):
                        plain+= chr(int(hexnums[i:i+2], 16))
                except:
                    self.printErr("could not convert plain hex to bytes")
                    return
                
            else:
                return 
            
            try:
                # get plaintext offset
                offset= int(cmds[1])
                
                if len(plain) > self.keylen:
                    self.printErr("plaintext longer than key!")
                    return
                
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

                
                self.updateKey(newKey)
                
                return
            except ValueError:
                self.printErr("could not convert parameters!")
                return
        else:
            self.printErr("syntax: p | phex [pos] [plaintext (in hex)]")    
        
    def drawStatusBar(self):
        self.clearStatusBar()
        #statusBar= "MODE: "+ ("original   " if self.rawmode else "key applied")
        statusBar="KEY: " + ' '.join([hex(ord(c))[2:].ljust(2, "0") for c in self.key])
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
        self.pad.refresh(0,0, 0,0, self.ymax,self.xmax)
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

        #initialize analyzer pad
        self.pad= curses.newpad(self.ymax - self.infoBarHeight, self.xmax)
        self.blocksPerLine= self.xmax / self.blocklenX
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
            if input == ord("r"):
                self.revertKeyChange()
            
            # scroll view up
            elif input == curses.KEY_UP or input == ord('k'):
                self.viewOffset-= self.keylen* self.blocksPerLine
                if self.viewOffset < 0:
                    self.viewOffset= 0
            
            # scroll view down
            elif input == curses.KEY_DOWN or input == ord('j'):
                if self.viewOffset+ self.keylen* self.blocksPerLine < self.filesize:
                    self.viewOffset+= self.keylen* self.blocksPerLine
                else:
                    self.printInfo("reached end of file.")

            self.refresh()

if __name__ == "__main__":
    # display help
    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print "Usage: otp_pwn.py [encrypted file] [key length]"
        print ""

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