#!/usr/bin/env python2

import curses
import string
import sys


class OTPPwn:
    
    def __init__(self, fd, keylen):
        self.fd= fd
        self.keylen= keylen
        self.blockwidth= 24
        self.infoBarHeight= 3
        self.blockpadding= 3
        self.blocklenX= self.blockwidth+self.blockpadding
        self.blocklenY= self.keylen+self.blockpadding+2
        self.printable= string.digits+string.uppercase+string.lowercase+string.punctuation
        
        self.viewOffset= 0
        self.key= "\x10"*self.keylen
        self.rawmode= True
    
    def drawBlock(self, y, x, text, offset):
        for i, line in enumerate(self.makeBlock(text, offset)):
            self.pad.addstr(y+i, x, line)
        
    def makeBlock(self, text, offset= 0):
        # add table header
        res= []
        res.append("POS  | HEX | DEC | STR |")
        res.append("------------------------")
        
        for i, ch in enumerate(text):
            res.append("%4d | %02x  | %3d | %2s  |" % ((i+offset), ord(ch), ord(ch), ch if ch in self.printable else "."))
        
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
        
        for ypos in range(0, ylen-self.blocklenY, self.blocklenY):
            for xpos in range(0, xlen-self.blocklenX, self.blocklenX):
                text= f.read(self.keylen)
                
                # apply XOR key if RAW mode is off
                if not self.rawmode:
                    text= self.xorkey(text)
                
                self.drawBlock(ypos, xpos, text, offset)
                offset+= self.keylen
        
    
    def clearInput(self):
        curses.setsyx(self.ymax, 0)
        self.stdscr.clrtoeol()
    
    def refresh(self):
        # draw pad
        self.drawPad()
        self.stdscr.refresh()
        self.pad.refresh(0,0, 0,0, self.ymax,self.xmax)
    
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
            
            # input command mode
            if input == ord(":"):
                curses.echo()
                stdscr.addch(self.ymax-1, 0, ":")
                input= stdscr.getstr(self.ymax-1, 1, 15)
                curses.noecho()
                self.clearInput()
                
                # quit
                if input == "q":
                    break
                
                # plain input
                
            # toggle raw mode
            if input == ord("r"):
                if self.rawmode:
                    self.rawmode= False
                else:
                    self.rawmode= True
            
            # scroll view up
            elif input == curses.KEY_UP or input == ord('k'):
                self.viewOffset-= self.keylen* self.blocksPerLine
                if self.viewOffset < 0:
                    self.viewOffset= 0
            
            # scroll view down
            elif input == curses.KEY_DOWN or input == ord('j'):
                self.viewOffset+= self.keylen* self.blocksPerLine
            
            self.refresh()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Please provide the encrypted file as a command line argument."
        sys.exit()
        
    filename= sys.argv[1]
    with open(filename, "r") as f:    
        otpPwn= OTPPwn(f, 16)
        curses.wrapper(otpPwn.run)
    