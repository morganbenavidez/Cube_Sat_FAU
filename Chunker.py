# Jan Malte Roehrig
# malte.roehrig@gmx.de
# Julian Brown
# brownj4@mit.edu
# Summer 2016
# 2016-11-28 gm, jhn, jah working it
# 2016-12-07 pkt_generator working, updates working, move to production
# 2016-12-08 next rev, also try at AFIT
# 2016-12-12 next rev, added logging info to see more info on bad pkts (dropped bits or
what)
# 2016-12-14 added code to look at buffer when no sync_words in 3x10^4 bits
# 2016-12-15 clean up and test
# 2016-12-16 store failed packets for analysis
# 2016-12-19 store bad packets as pickled bitarrays or analysis
# 2016-12-20 store good packets, too
# 2017-01-02 write raw pkts to file for bitstring code
# 2017-01-06 updated to save single file, cleaned up log code
# 2017-01-10 look for fragments 2 and 3 after fragment 1 from sys-stat
# 2017-01-11 adapt program to just look for three packets after a preamble
# 2017-01-12 able to get n packets
# 2017-01-13 now put back everything needed to unstuff, crc, and kiss and log
# 2017-01-14 update to keep track of pkt #, need to add done with FF FF FF after blocks
# 2017-01-19 add ACK spoof capability by storing an ACK
# 2017-02-02 take spoof out, didn't work
# 2017-02-08 add pass info catcher to improve file naming of logged and printed data
# 2017-02-10 take pass catcher out, too hard to do UDP receive
# 2017-02-19 add in pass_info_filename_reader code to do file naming
# 2017-03-05 added the pass_ID to PASS_INFO_FOR_PARSE_AX25.txt
# UPDATE Version in init when you update the code!!!
"""
Embedded Python Blocks:
Each this file is saved, GRC will instantiate the first class it finds to get
ports and parameters of your block. The arguments to __init__ will be the
parameters. All of them are required to have default values!
"""
"""
Python notes:
120
indentation level = 2 spaces, not tabs
"""
from gnuradio import gr
from bitarray import bitarray
import calendar
import datetime
import itertools
import numpy as np
import pickle
import select
import socket
import threading
import time
from sys import stdout
class blk(gr.sync_block):
############################
# def - initialze the object
############################

 def __init__(self, ip='192.168.101.64', port=10001): # only default arguments here
 gr.sync_block.__init__(
 self,
 name='Parse AX.25',
 in_sig=[np.uint8],
 out_sig=None
 )
 #
 # set up the socket and threading
 #
 self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create UDP
socket
 self.send_lock = threading.Lock() # create lock to ensure UDP packets are sent
one at a time
 self.server_address = (ip, port)

 #
 # these variables are associated with this instance of the class/object
 #
121
 self.buff = bitarray(endian='big') # create bitarray data buffer to store received packets
 self.filename_raw = ''
 self.filename_KISS = ''
 #self.flag = bitarray('10111110111011111100101011111110', endian='big')
# now BEEFCAFE*2 (the flag is a 7E in hex (AX.25))
 #self.flag = bitarray('1011111011101111', endian='big') # now BEEFCAFE*2
(the flag is a 7E in hex (AX.25))
 self.flag = bitarray('01100110'*4, endian='big') # 2018-10-01 66 - the flag is
a 7E in hex (AX.25)
 self.last_length = 0
 #self.log_filename = "/home/satrnuser/PropCube/Log_files/Log_AX25_RX.txt"
# default file name for log_packet
 self.log_filename = "/home/ssagadmin/Desktop/lovdahl/Log_AX25_RX.txt"
# default file name for log_packet
 self.max_num_pkts_after_sync = 1 # 2018-10-01 total number of pkts to
look for before waiting for preamble
 self.number_of_overflows = 0 # how many times work hit
the 30k mark without a preamble flag ... flag
 self.number_of_packets = 0 # if sys-stat, want to
try to get all 3 fragments
 #self.sync_word = bitarray('01'*20, endian='big') + self.flag
 self.sync_word = bitarray('01111110'*5, endian='big') + self.flag
 #self.sync_word = self.flag
 #
 # identify who is running this program
 #
 ip_address = socket.gethostbyname(socket.gethostname())
 if(0): print "ip_address = ", ip_address
 if ( ip_address == "192.168.101.1" ): self.location = "NPS"
 elif( ip_address == "192.168.101.2" ): self.location = "PTSUR"
 elif( ip_address == "192.168.102.1" ): self.location = "AFIT"
 #elif( ip_address == "127.0.1.1" ): self.location = "SDL"
 elif( ip_address == "192.168.103.1" ): self.location = "SDL"
 elif( ip_address == "192.168.101.248" ): self.location = "HSFL"
 elif( ip_address == "192.168.104.1" ): self.location = "HSFL"
 elif( ip_address == "192.168.105.1" ): self.location = "UNM"
 elif( ip_address == "192.168.106.1" ): self.location = "USNA"
 else: self.location = "UNK"
 Version = "2018-10-04 working1"
 print "\nLocation = ", self.location, " ip_address = ", ip_address, " port = ", port
 print "Version: ", Version, " Parse AX.25 Pkt Decode and Logging Program\n"
###################################
122
# def - send a KISS packet over UDP
###################################

 def send_one_message(self, kiss_packet): # a KISS packet is just a string
 self.send_lock.acquire()
# a semaphore, this acquire will block if lock already being used
 try:
 self.sock.sendto(kiss_packet, self.server_address)
 except:
 print "exception sendto() failed"
 finally:
 self.send_lock.release() #
releases the lock, now next acquire can proceed
####################
# def - calc the crc
####################
 def calc_crc(self, packet):
 crc_poly = bitarray('0001000000100001', endian='big') # 0x1021
 shift_reg = bitarray('1'*16, endian='big') # two bytes of ones
 for bit in packet[:-16]:
 shift_reg.append(False) # 16 1's then only zeros in shift_reg
 if shift_reg.pop(0) != bit: # remove 1st element and check it against the
current packet bit
 shift_reg = shift_reg^crc_poly # if not the same, then update the calc'd CRC
(shift_reg)
 sr = shift_reg.tobytes()
 if(0): print "work: calculated crc = 0x ", ''.join('%02X'%ord(x) for x in sr)
 if(0): print "work: calculated crc =", shift_reg # shift_reg is the calculated
CRC
 if(0): print "work: recovered crc =", packet[-16:]
 return shift_reg
###################################################
# make the KISS Frame packet - KISS pkt is a string
# then send it and log it
###################################################
 def kiss_the_packet(self, packet):
 kiss_packet = ""
123
 for byte in list(bytearray(packet[:])): # CRC is being stripped out of the KISS packet
 kiss_packet += chr(byte)
# append the next byte

#####################################################
# create thread to send KISS packet over UDP socket #
#####################################################
 send_thread = threading.Thread(target=self.send_one_message, args=(kiss_packet,))
 send_thread.daemon = True
 send_thread.start()
 self.log_kiss_packet(kiss_packet) # displays and
logs kiss_packet
###################################################
# Produce a meaningful file name to store data in
###################################################
 def file_name_maker(self):
 # try reading the pass info and if successful,
 # check against the current date and time and
 # if not more than TBD minutes ago, make the name from the pass info
 # if more than TBD minutes old, the file data is stale and
 # so should use some default name
 #
 # string 1 = "xxxxx_201x-mm-dd_HH-MM-SS_UTC" # pass_ID, date, time
 # string 2 = "NPS_10MERRYW_180_359_090" # gs,
sat name, Az-start, Az-end, Max elevation
 # string 3 = "duration"
# pass duration in seconds
 try:
 file_path = "/home/ssagadmin/Desktop/lovdahl/"
 pass_info_filename = file_path + "PASS_INFO_FOR_PARSE_AX25.txt"
 #pass_info_filename = "PASS_INFO_FOR_PARSE_AX25.txt"
 pass_info_fp = open( pass_info_filename, "r" )
 string1 = pass_info_fp.readline()
 string2 = pass_info_fp.readline()
 string3 = pass_info_fp.readline()
 pass_info_fp.close()
 #print "string1 = ", string1
 #print "string2 = ", string2
 #print "string3 = ", string3
124
 [pass_ID, datestring, timestring, UTCstring, nullstring] = string1.split("_")
 duration = float(string3)
 #print "pass_ID = ", pass_ID
 #print "datestring = ", datestring
 #print "timestring = ", timestring
 #print "duration = ", duration
 pass_datetime_string = datestring + " " + timestring
 #print "pass_datetime_string = ", pass_datetime_string
 current_datetime_in_seconds = time.time() # all sites should be on UTC,
this result in seconds
 #print "current_datetime_in_seconds = ", current_datetime_in_seconds
 pass_datetime_in_seconds = calendar.timegm(time.strptime(pass_datetime_string,
"%Y-%m-%d %H-%M-%S"))
 #print "pass_datetime_in_seconds = ", pass_datetime_in_seconds
 beg_of_pass = pass_datetime_in_seconds
 end_of_pass = pass_datetime_in_seconds + duration
 #
 # check to see if a pass is going on right now, with +/- 5 seconds for relative clock
drift from UTC
 # if a pass is going on, make the same name to append data to
 # otherwise, make a simplified name
 #

 if( (current_datetime_in_seconds > beg_of_pass-5) & (current_datetime_in_seconds
< end_of_pass+5) ): # pass going
 self.filename_raw = file_path + string1[:-1] + 'raw_' + string2[:-1] + '.txt'
 self.filename_KISS = file_path + string1[:-1] + 'KISS_' + string2[:-1] + '.txt'
 else: # either clock is off (if pre-pass) or pass has ended and no new pass
info has come in
 datestr = time.strftime("%Y-%m-%d", time.gmtime(current_datetime_in_seconds))
 self.filename_raw = file_path + datestr + '_' + self.location + '_raw.txt'
 self.filename_KISS = file_path + datestr + '_' + self.location + '_KISS.txt'
 # test if can open and write to the filename
 #tstr = time.strftime("%Y-%m-%d %H:%M:%S",
time.gmtime(current_datetime_in_seconds)) + " UTC"
 #print "file_name_maker: writing a test file"
 #test_file_name = file_path+self.filename_raw
 #test_fp = open(test_file_name, "a")
 #test_fp.write("Opened file and wrote something at " + tstr + "\n")
 #test_fp.close()
125
 except IOError:
 print "Pass_info file '" + pass_info_filename + "' failed to open"
 datestr = time.strftime("%Y-%m-%d", time.gmtime(current_datetime_in_seconds))
 self.filename_raw = file_path + datestr + '_' + self.location + '_raw.txt'
 self.filename_KISS = file_path + datestr + '_' + self.location + '_KISS.txt'
# except:
# print "unknown error"
 #print "filename_raw = ", self.filename_raw
 #print "filename_KISS = ", self.filename_KISS
#################################################################
# def - log KISS packet to file and print to screen
# log_status:
# 1 - crc_good: packet_to_log is kiss_packet and is bytes
#################################################################
 def log_kiss_packet(self, kiss_packet_to_log):
 if(0): print "log_pkt: kiss_packet_to_log = ", list(kiss_packet_to_log)
 now = time.time()
 milliseconds = '.%03d' % int((now - int(now)) * 1000)
 tstr = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(now)) + milliseconds + "
UTC"
 file_date = time.strftime( "20%y-%m-%d", time.gmtime(now) )
# self.file_name_maker()
# 2018-10-01 updates
 self.log_filename = "/home/ssagadmin/Desktop/lovdahl/Logs/"
 self.log_filename += file_date
 self.log_filename += "_Log_RX_pkts.txt"
 if(1):
 #print "file_date = ", file_date
 print "log_filename = ", self.log_filename # 2018-10-01
 f = open(self.log_filename, "a") # ADD try: except: for the open process?

 data_prt = ""
126
 l = len(kiss_packet_to_log) # length of string is # of bytes
 len_to_log = l
 data_prt = kiss_packet_to_log[:] # this DOES copy packet_to_log to data_prt, don't
need the [:], on Ubuntu!
 data_wrt = kiss_packet_to_log[:]
 if(0): print "log: len of data_prt, kiss_packet_to_log = ", len(data_prt),
len(kiss_packet_to_log)
 if(0): print "log: l, l_to_print = ", l, l_to_print
 if(0): print "log: len data_prt, l_to_print = ", len(data_prt), l_to_print
 ################################################################
 # write the time, status, len, and data to the file
 # ALSO add try: except: for the write process
 ################################################################
 write_str = "%s %s pkt # = %d of %d KISS packet len = %d bytes"%(self.location,
tstr, self.number_of_packets, self.max_num_pkts_after_sync, len_to_log)
 pkt_len = len(data_wrt)
 f.write(write_str + '\n')
 f.write(str(pkt_len) + '\n')
 write_pkt = ''.join('{:02X}'.format(ord(x)) for x in data_wrt) # 2017-01-02
extra space gone, use for both
 f.write(write_pkt + '\n')
# logging pkts twice if
logging raw_pkts, unneccesary
 if(0): print "KISS packet logged!"
 f.close()
#################################################################
# def - log raw_packets to file and print to screen
# log_status:
# 0 - crc_failed, but packet_to_log is bitarray (not kiss_packet, because crc failed)
# 2 - crc_failed, packet not byte length, lost a bit somewhere: packet_to_log is a bitarray
# 3 - short packet: packet_to_log is a bitarray
#################################################################
 def log_packet(self, packet_to_log, log_status, fname=None):
 len_packet_to_log = len(packet_to_log) # length in bits
 #raw_packet = packet_to_log[:] # this copies the packet_to_log to a bitarray
or list
127
 if(0): print "log_pkt: type raw_packet = ", type(raw_packet)
 if(0): print "log_pkt: packet_to_log = ", packet_to_log
 now = time.time()
 milliseconds = '.%03d' % int((now - int(now)) * 1000)
 tstr = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(now)) + milliseconds + "
UTC"
 file_date = time.strftime( "20%y-%m-%d", time.gmtime(now) )
# 2018-10-03 to have same file name
 self.log_filename = "/home/ssagadmin/Desktop/lovdahl/Logs/"
 self.log_filename += file_date
 self.log_filename += "_Log_RX_pkts.txt"
 if(0):
 self.log_filename = "/home/ssagadmin/Desktop/lovdahl/"
 self.log_filename += file_date
 self.log_filename += "_Log_AX25_RX_"
 self.log_filename += self.location
 self.log_filename += "_raw_pkts.txt"
 #else: self.log_filename = fname
 if(0):
 print "file_date = ", file_date
 print "log_filename = ", filename_raw
 #2018-10-03: change filename_raw to self.log_filename
 f = open(self.log_filename, "a") # ADD try: except: for the open process?

 data_prt = ""
 # need to pad the packet_to_log to an even 8 bits
 len_to_pad = ( 8 - (len_packet_to_log % 8) ) % 8
 if(0): print "log: len_to_pad = ", len_to_pad
 for i in range(len_to_pad):
 packet_to_log.append(0)
 if(0): print "packet_to_log = ", packet_to_log
 data = ''
 if(0): print "log: bytearray(packet_to_log) = ", list(bytearray(packet_to_log))
 for byte in list(bytearray(packet_to_log)): # need to turn the bitarray into bytes
for printing
 data += chr(byte)
128
 data_prt = data[:]
 data_wrt = data[:]
 ################################################################
 # write the time, status, len, and data to the file
 # ALSO add try: except: for the write process
 ################################################################
 #write_str = "%s status = %s len = %d"%(tstr, log_status, len_packet_to_log)
 write_str = "%s %s pkt # = %d of %d status = %s len = %d bits"%(self.location, tstr,
self.number_of_packets, self.max_num_pkts_after_sync, log_status, len_packet_to_log)
 if( log_status == 0): write_str += " CRC Fail: "
 elif(log_status == 1): write_str += " Good pkt: "
 elif(log_status == 2): write_str += " Pkt bit drop: "
 elif(log_status == 3): write_str += " Pkt too short: "
 else: write_str += " Unexpected: "
 data_wrt_len = len(data_wrt)
 f.write(write_str + '\n')
 f.write(str(len_packet_to_log) + '\n')
 write_pkt = ''.join('{:02X}'.format(ord(x)) for x in data_wrt) # 2017-01-02
extra space gone, use for both
 f.write(write_pkt + '\n')
 if(0): print "raw packet logged!"
 f.close()
 ################################################################
 # print the time, status, len, and data to the screen
 ################################################################
 #if( log_status == 0): print_str = "%s %s l =%4d"%(tstr, log_status, l)
 #else:
 #print_str = "%s status = %s len = %d"%(tstr, log_status, len_packet_to_log)
 #print_str = "%s pkt # = %s status = %s len = %d"%(tstr, str(self.number_of_packets),
log_status, len_packet_to_log)
 print_str = "%s %s pkt # = %d of %d status = %s len = %d bits"%(self.location, tstr,
self.number_of_packets, self.max_num_pkts_after_sync, log_status, len_packet_to_log)
 if( log_status == 0): print_str += " CRC Fail: "
129
 elif(log_status == 1): print_str += " Good pkt: "
 elif(log_status == 2): print_str += " Pkt bit drop: "
 elif(log_status == 3): print_str += " Pkt too short: "
 else: print_str += " Unexpected: "
 print_len = 15
 print_str += ''.join(' {:02X}'.format(ord(x)) for x in data_prt[0:print_len])
 if( len(data_prt) > print_len): print_str += " ..."
 print print_str
 return
########################################################################
########
# the real work here
# - input_items is a list of lists
# in this particular case input_items[0] is a numpy.ndarray (n-dimensional)
# and the ndarray items are numpy.uint8
# - GNU Radio input_items[0][0] is big-endian bit
# - turn the numpy.ndarray into a bitarray to work on - frombytes() appends!
# - first do the byte alignment, based on sync word and final flag
# - then calc and check crc, if good, get rid of crc, reverse the bytes
# - then create the kiss_packet
#
# the preample bytes are big endian
# the data bytes are little endian
# the crc is big endian and comes inverted (is this bizarre or expected?)
# the flag is symmetric
#
# NOTE: data is little endian, but crc is big endian and inverted!
# these are combined into a big endian buff,
# so crc is written byte reversed by the data
logger!!! FIX!
#
########################################################################
########
 def work(self, input_items, output_items):
 PAYLOAD_SIZE = 256*8
 AFTER_PAYLOAD_SIZE = 4*8
 EXPECTED_BIT_COUNT = PAYLOAD_SIZE + AFTER_PAYLOAD_SIZE

 if(0): print "work: the top"
 #
130
 # start working on the bits
 #
 status = 0
# default status is simple CRC fail
 self.buff.frombytes(np.array(input_items, dtype=np.uint8).tobytes()) # magic -
makes a bitarray from an ndarray
 # frombytes() APPENDS the input_items
to buff
 #print "delta length = ", (len(self.buff) - self.last_length)
# shows how often work gets called!
 #self.last_length = len(self.buff)
# every byte
just about
 sync_word_pos = self.buff.search(self.sync_word, 1) # find the index of the
1st sync word
 if sync_word_pos:
 self.number_of_packets = 0
#restart packet counter
 if(0):
 #print "work: input_items type is ", type(input_items) # input_items is a 'list'
 #print "work: len input_items is ", len(input_items) # len always = 1
 #print "work: input_items = ", input_items
 #print "work: input_items[0][0] type is ", type(input_items[0][0]) #
input_items[0][0] is a 'numpy.ndarray'
 #print "work: len input_items[0][0] is ", len(input_items[0][0])
 #print "work: input_items[0][0] = ", input_items[0][0]
 print
 if bool(sync_word_pos) | bool(self.number_of_packets): # starting over either
for sync_word OR any pkts already
 self.number_of_overflows = 0
# reset the number_of_overflows counter
 if sync_word_pos: start_pos = sync_word_pos[0] + len(self.sync_word) #
sync_word is 48 bits long
 else: start_pos = 0
 if(0): print "work: start_pos = ", start_pos
 flag_pos = self.buff[start_pos:].search(self.flag,1) # find the index of the next 7E
flag
 if(0): print "work: flag_pos = ", flag_pos
131
 fragment_num = 0
# looking at
first packet after sync word
 if flag_pos:
# if no flag yet, return to wait for more bits
 end_pos = start_pos + flag_pos[0]
 if(0): print "work: end_pos, buff_len = ", end_pos, len(self.buff) #2018-10-02 0 to
1s
 self.number_of_packets += 1
 if(0): print "work: raw packet len = ", end_pos - start_pos + 1 # 2018-10-02
 if(0): print "work: number_of_packets = ", self.number_of_packets
 if(0): print "work: payload and crc = ", self.buff[start_pos:end_pos]
# print the payload and crc
 #########################################
 # extract packet (a bitarray) from buff #
 #########################################
 packet = self.buff[start_pos:end_pos] #
packet is after sync+7E to the next 7E and is a bitarray.
 raw_packet = packet[:]
# save for logging all raw packets
 if(0): print "work: raw_packet = ", raw_packet

 # unstuff and check if bits make up bytes (if bits%8!=0 something wrong)
 num_unstuffs = 0
 for stuffing_pos in packet.search(bitarray('111110', endian='big'))[::-1]:
# packet is big-endian, right?
 packet.pop(stuffing_pos+5)
# gets rid of
that zero
 num_unstuffs += 1
 if(1):
 print "work: after unstuff packet len = ", len(packet) # 2018-10-02 to print the
sequence number
 seq = packet[16*8:16*8+16]
 #print "work: len(seq) = ", len(seq)
 seq[:] = bitarray(seq, endian = 'little')
 #print "work: len(seq) = ", len(seq)
 #print "work: len(bytearray(seq)) = ", len(list(bytearray(seq)))
 s = ""
 for d in list(bytearray(seq)):
 s += "%02X "%d
132
 print "work: seq2 = ", s

 if(len(packet) % 8 != 0):
 #2018-10-04: turn off print # check len(packet) modulo 8 = 0!?
 if(0): print "work: packet not pure bytes after unstuff. Must fail CRC check."
 status = 2
# status = 2 for packet byte problem
 #self.log_packet(bitarray(raw_packet, endian='big'), status)
 # check if packet too short (len < 24)
 elif(len(packet) < 24):
# catch too short packets = CASE 3
 if(0): print "work: packet len < 24! = ", len(packet)
 status = 3
 # then crc check, but only if possibly good (status not 2 or 3)
# 2018-10-01
 if(status < 2):
 if(0): print "IN status < 2"
 shift_reg = bitarray(endian='big') # two bytes of ones
 shift_reg = self.calc_crc(packet)
 if(0): print "work: shift_reg = ", shift_reg
 if all(shift_reg^packet[-16:]): # compare the calc'd CRC with the received ~CRC,
they must be ~.
 status = 1
 packet[:] = bitarray(packet, endian='little') # Makes an le version of the
bitarray packet
 # this somehow reverses the bits in every
"byte"
 self.kiss_the_packet(packet) # KISSs the packet, sends it out, and logs it
 #2018-10-05: changed len(packet) check

 if(len(packet) == EXPECTED_BIT_COUNT):
 if(1): print "work: IN status = 4"
 status = 4
 packet = packet[:2048]
 packet[:] = bitarray(packet, endian='little') # 2018-10-03 Do this to good packets.
Makes an le version of the bitarray packet.
133
 self.kiss_the_packet(packet) # 2018-10-03 now logs good pkts! does not
KISSs the packet, but sends it out, and logs it
 # 2018-10-04: add more logging for debug
 elif(len(packet) > 2048):
 if(1): print "work: > 2048"
 packet = packet[:2048]
 packet[:] = bitarray(packet, endian='little') # 2018-10-03 Do this to good packets.
Makes an le version of the bitarray packet.
 self.kiss_the_packet(packet) # 2018-10-03 now logs good pkts! does not
KISSs the packet, but sends it out, and logs it
 # then log the raw packet
# 2018-10-01 self.log_packet(bitarray(raw_packet, endian='big'), status)
 # always look for max_num_pkts_after_sync, but then start over
 end_of_pkts_marker = bitarray('1'*24, endian='big') # 3 x 'FF'
seems to follow every set of blocks
 if(0): print "work: end_of_pkts_marker = ", end_of_pkts_marker
 if(0): print "work: packet[:48] = ", packet[:48]
 end_of_pkts_marker_pos = packet.search(end_of_pkts_marker)
 if(0): print "work: end_of_pkts_marker_pos = ", end_of_pkts_marker_pos
 if( end_of_pkts_marker_pos ):
# done with that set of blocks
 self.number_of_packets = 0
# resets and starts looking for sync word
 elif( self.number_of_packets >= self.max_num_pkts_after_sync ):
 self.number_of_packets = 0
 self.buff = self.buff[end_pos+8:]
# clear buffer up to end of sync word
flag ... flag
 return len(input_items[0])
# what is it really returning? the number 1

##############################################
 # clear buffer if sync word hasn't been seen
 # for the the last 10kb of data
 # CONSIDER only clearing buff up to an
 # occurrence of sync_word (obviously no
 # following 7E yet)
##############################################
134
 elif len(self.buff) > 1*10**4:
 now = time.time()
 tstr = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(now)) + " "
 file_date = time.strftime( "20%y-%m-%d", time.gmtime(now) )
 self.number_of_overflows += 1
 self.fragment_num = 0
 if(0):
# to collect "noise" from the buff overflow
 self.log_filename = "/home/ssagadmin/Desktop/lovdahl/"
 self.log_filename += file_date
 self.log_filename += "_Noise_data"
 f = open(self.log_filename, "a") # ADD try: except: for the open process?
 temp_buff = bitarray(endian = "big")
 temp_buff = self.buff[:-len(self.sync_word)]
 temp_buff.bytereverse()
 data = ''
 for byte in list(bytearray(temp_buff)):
 data += chr(byte)

 data_log = data[:] # PERHAPS
should log the bitarray instead of the bytearray???
 write_str = ""
 write_str += ''.join(' {:02X}'.format(ord(x)) for x in data_log)
 f.write("buff: " + write_str + "\n")
 f.close()
 print self.number_of_overflows, " ", tstr, " work: no sync_words, buff len =",
len(self.buff), "\r"
 self.buff = self.buff[-len(self.sync_word):]
 return len(input_items[0])
# what is it really returning?
135
APPENDIX H. CHUNKING.PY
from __future__ import print_function
import collections
import glob
import math
import os
import pickle
import random
import select
import serial
import shutil
import socket
import struct
import subprocess
import sys
import time
import crc32_cadet
import packet
import payload_UART
USE_SEEK_HAB = False
USE_SEEK_GROUND = True
RND_TX_HAB = 0
RND_TX_GROUND = 0
PAUSE_HAB_TX = 1.05
PAUSE_COUNT = 4
CAMERA_TAKE_INTERVAL = 5 # seconds
CAMERA_TODOWNLOAD_INTERVAL = 60 # seconds
USE_MHX = True
USE_PAYLOAD_SERIAL = True
SDR_UDP_GROUND_RX_PORT = 10005
SDR_UDP_HAB_RX_PORT = SDR_UDP_GROUND_RX_PORT
SDR_UDP_HAB_TX_PORT = 10000
SDR_UDP_GROUND_IP = '172.20.73.49'
#SDR_UDP_HAB_IP = '172.20.73.22'
136
SDR_UDP_HAB_IP = '127.0.0.1'
GROUND_FEEDBACK_TIME = 2
AFTER_PAYLOAD = 4*'\xAA'
PREAMBLE = '\x55'
#HEADER = '\xBE\xEF\xCA\xFE'
#HEADER = '\xBE\xEF'
HEADER = 4*'\x66'
FILENAME_SIZE = 12
FILESIZE_SIZE = 4
SEQ_SIZE = 2
MAX_SEQ_SIZE = 2
CRC_SIZE = 4
PAYLOAD_OFFSET = len(PREAMBLE) + len(HEADER)
DATA_OFFSET = PAYLOAD_OFFSET + FILENAME_SIZE + 8
MAX_PAYLOAD_SIZE = 256
MAX_DATA_SIZE = MAX_PAYLOAD_SIZE - FILENAME_SIZE - FILESIZE_SIZE
- SEQ_SIZE - MAX_SEQ_SIZE - CRC_SIZE
MAX_DOWNLOAD_COUNT = 4
GROUND_TO_HAB_CMD_LEN = 2
CHUNK_BIT_MASK_BYTES_LEN = 2 # number of bytes
CHUNK_BIT_MASK_BITS_LEN = CHUNK_BIT_MASK_BYTES_LEN*8
CHUCK_ASCII_VALUES = 15 # set to None if using bitmasking
# max seq = 65535
# therefore, maximum bit mask size = 65535/CHUNK_BIT_MASK_BYTES_LEN: so
for 80 bytes (800 bits) ==> 82 bit mask planes
# 1 MByte file: 4096 chunks; 80 bytes for bit mask (800 bits) ==> 5 bit mask frames
# MHX up structure is:
# offset size items
# ====== ==== =====
# 0 5 Command
# for Command == file complete
# 5 12 filename
# for Command == file progress
# 5 12 filename
# 17 2 bitmask chunk sequence offfset
# 19 80 bitmask for frame N
MHX_COMMAND_FILE_COMPLETE = "PLDN "
137
MHX_COMMAND_FILE_PROGRESS = "PLST "
MHX_COMMAND_START = "PLSTART"
MHX_COMMAND_CLEAR = "PLCLEAR"
MHX_COMMAND_TIME = "PLTIME"
FNAME_START_OFFSET = 5
BIT_MASK_SEQ_OFFSET = 17
BIT_MASK_START_OFFSET = 19
class CHUNKER(object):
def __init__(self, mode=None):
self.CRC32 = crc32_cadet.CRC32()
if mode == 'Ground' and USE_MHX:
self.eol = '\x0D'
self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600,
bytesize=8, parity='N', stopbits=1, timeout=0, xonxoff=0, rtscts=0)
self.ser.flushInput()
self.ser.flushOutput()
def prep_file_for_chunking(self, fname):
self.fname = fname
self.fname_padded = get_fname_padded(fname)
fp = open(os.path.join('todownload', fname), 'rb')
data = fp.read()
self.data = data
fp.close()
self.file_size = len(data)
(self.num_chunks, self.remainder) = divmod(self.file_size,
MAX_DATA_SIZE)
if self.remainder > 0:
self.num_chunks += 1
self.chunk_i = 0
self.received = set()
def prep_file_for_dechunking(self, fname):
pass
def start_over(self):
self.chunk_i = 0
def remove_download_data(self):
self.data = None
138
def mark_received(self, i):
self.received.add(i)
def make_next_chunk(self, count):
if self.chunk_i == self.num_chunks:
return ''
elif self.chunk_i == self.num_chunks -1:
if self.remainder > 0:
if self.chunk_i in self.received:
return ''
else:
payload = self.fname_padded + struct.pack('>IHH',
self.file_size, self.chunk_i, self.num_chunks)
if USE_SEEK_HAB:
fp = open(os.path.join('todownload',
self.fname), 'rb')
fp.seek(self.chunk_i*MAX_DATA_SIZE,
0) # goto absolute position, relative to start of file
payload += fp.read(self.remainder)
fp.close()
else:
payload += self.data[-self.remainder:]
payload += (MAX_DATA_SIZEself.remainder)*'\x00'
crc32 = self.CRC32.calc_str(payload)
print('%d, <%s>, fsize=%d, Nchunks=%d,
remainder=%d, i=%d'%(count, self.fname_padded, self.file_size, self.num_chunks,
self.remainder, self.chunk_i))
self.chunk_i += 1
return payload + crc32
else:
while True:
if self.chunk_i not in self.received:
break
else:
self.chunk_i += 1
if self.chunk_i == self.num_chunks:
return ''
payload = self.fname_padded + struct.pack('>IHH', self.file_size,
self.chunk_i, self.num_chunks)
if USE_SEEK_HAB:
fp = open(os.path.join('todownload', self.fname), 'rb')
139
fp.seek(self.chunk_i*MAX_DATA_SIZE, 0)
# goto absolute position, relative to start of file
payload += fp.read(MAX_DATA_SIZE)
fp.close()
else:
payload +=
self.data[self.chunk_i*MAX_DATA_SIZE:self.chunk_i*MAX_DATA_SIZE+MAX_D
ATA_SIZE]
crc32 = self.CRC32.calc_str(payload)
print('%d, <%s>, fsize=%d, Nchunks=%d, remainder=%d,
i=%d'%(count, self.fname_padded, self.file_size, self.num_chunks, self.remainder,
self.chunk_i))
self.chunk_i += 1
return payload + crc32
def MHX_write(self, data):
# mhx_data = MHX_escape(data, self.eol) + self.eol
mhx_data = data + self.eol
# print('MHX_write(', end='')
# for d in mhx_data:
# print('%02X '%ord(d), end='')
# print(')')
# print('MHX_write(): %s'%data)
self.ser.write(mhx_data)
def send_bitmask(self, fname, file_info, sock):
# send up information about chunks that have been received (NOT
missing)
bitmask_seq_count = file_info['bitmask_seq_count']
if CHUCK_ASCII_VALUES == None:
(bit_mask_seq_start, remainder) = divmod(bitmask_seq_count,
CHUNK_BIT_MASK_BITS_LEN)
bit_mask_seq_start =
bit_mask_seq_start*CHUNK_BIT_MASK_BITS_LEN
seq_end = bit_mask_seq_start +
CHUNK_BIT_MASK_BITS_LEN
else:
(bit_mask_seq_start, remainder) = divmod(bitmask_seq_count,
CHUCK_ASCII_VALUES)
bit_mask_seq_start =
bit_mask_seq_start*CHUCK_ASCII_VALUES
seq_end = bit_mask_seq_start + CHUCK_ASCII_VALUES
140
if seq_end >= file_info['max_seq']:
seq_end = file_info['max_seq'] - 1
if CHUCK_ASCII_VALUES == None:
bitmask = CHUNK_BIT_MASK_BYTES_LEN*[0]
# assumes ALL missing
else:
bitmask = ''
for seq in range(bit_mask_seq_start, seq_end+1):
if seq not in file_info['missing_seq']:
# we have this chunk, so indicate it
if CHUCK_ASCII_VALUES == None:
mi = int((seq-bit_mask_seq_start)/8)
mb = (seq-bit_mask_seq_start)%8
try:
bitmask[mi] |= (1<<mb)
except IndexError:
print('Index error mi=%d'%mi)
else:
bitmask += '%d,'%seq
if CHUCK_ASCII_VALUES != None:
if bitmask != '':
bitmask = bitmask[:-1] # get rid of trailing comma
file_info['bitmask_seq_count'] += CHUNK_BIT_MASK_BITS_LEN
if file_info['bitmask_seq_count'] > file_info['max_seq']:
file_info['bitmask_seq_count'] = 0
if CHUCK_ASCII_VALUES == None:
payload = MHX_COMMAND_FILE_PROGRESS +
get_fname_padded(fname) + struct.pack('<H', bit_mask_seq_start)
for m in bitmask:
payload += chr(m)
else:
if bitmask == '':
payload = MHX_COMMAND_FILE_PROGRESS +
get_fname_padded(fname)
else:
payload = MHX_COMMAND_FILE_PROGRESS +
get_fname_padded(fname) + bitmask
if USE_MHX:
self.MHX_write(payload)
else:
crc32 = self.CRC32.calc_str(payload)
sock.sendto(payload+crc32, (SDR_UDP_HAB_IP,
SDR_UDP_HAB_RX_PORT))
141
def send_file_complete(self, fname, sock):
payload = MHX_COMMAND_FILE_COMPLETE +
get_fname_padded(fname)
crc32 = self.CRC32.calc_str(payload)
if USE_MHX:
self.MHX_write(payload)
else:
sock.sendto(payload+crc32, (SDR_UDP_HAB_IP,
SDR_UDP_HAB_RX_PORT))
def dechunk(self, rx_ip, rx_port):
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((rx_ip, rx_port))
sock.setblocking(0)
files = collections.OrderedDict()
file_feedback_list = []
file_feedback_count = 0 # which file that last was used to give
feedback to HAB
last_feedback_time = time.time()
last_dbase_time = time.time()
while True:
if time.time() - last_feedback_time >
GROUND_FEEDBACK_TIME:
if USE_MHX:
# check if TLM incoming on MHX
N = self.ser.inWaiting()
if N > 0:
data = self.ser.read(N)
fp = open('mhx_rx.txt', 'a')
fp.write(data+'\n')
fp.close()
# send some feedback about chunks received
last_feedback_time = time.time()
if len(file_feedback_list) > 0:
fname = file_feedback_list[file_feedback_count]
file_feedback_count += 1
if file_feedback_count >= len(file_feedback_list):
file_feedback_count = 0
if not files[fname]['ack_done']:
142
if len(files[fname]['missing_seq']) > 0:
self.send_bitmask(fname,
files[fname], sock)
else:
self.send_file_complete(fname,
sock)
(rd, wr, err) = select.select([sock], [], [], 0)
if sock not in rd:
continue
chunk = sock.recv(4096)
if chunk[:5] == MHX_COMMAND_FILE_COMPLETE:
fname =
chunk[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].stri
p()
if fname in files:
files[fname]['ack_done'] = True
continue
a = struct.unpack('<I', self.CRC32.calc_str(chunk[:-4]))[0]
b = struct.unpack('<I', chunk[-4:])[0]
if a != b:
print("*** CRC32 ERROR (%08X != %08X) ***" %(a,
b))
continue
fname = chunk[:FILENAME_SIZE].strip()
(fsize, seq, mseq) = struct.unpack('>IHH',
chunk[FILENAME_SIZE:FILENAME_SIZE+8])
data = chunk[FILENAME_SIZE+8:-4]
if fname not in files:
n = 0
print('fname=<%s>, fsize=%u, seq=%u, mseq=%u,
complete=%d%%'%(fname, fsize, seq, mseq, n))
else:
n = float((len(files[fname]['data']))/float(mseq))*100
if len(files[fname]['missing_seq']) == 0:
print('fname=<%s>, fsize=%u, seq=%u, mseq=%u,
complete=100%%'%(fname, fsize, seq, mseq))
else:
print('fname=<%s>, fsize=%u, seq=%u, mseq=%u,
complete=%d%%'%(fname, fsize, seq, mseq, n))
if not os.path.exists(os.path.join('downloads', fname)):
143
# if os.path.exists(fname) then file is already completely
downloaded
# otherwise, ".download" is added to the temporary file as
it is being created and filled up
if not os.path.exists(os.path.join('downloads',
fname+'.download')):
print('first chunk from %s, setting up'%fname)
files[fname] = {'missing_seq':set(range(0, mseq)),
'max_seq':mseq, 'bitmask_seq_count':0, 'data':{}, 'ack_done':False}
# create full file (zeros)
fp = open(os.path.join('downloads',
fname+'.download'), 'wb')
if USE_SEEK_GROUND:
fp.seek(fsize-1)
fp.write('\0') # writing a byte to the
end of the file forces os to create full file
fp.close()
file_feedback_list.append(fname)
if seq in files[fname]['missing_seq']:
# fill in the chunk we just received (as long as it has
not already been)
if seq == mseq-1: # the last one
# possibly need to chop off end of the data
to correct file size
(N, remainder) = divmod(fsize,
MAX_DATA_SIZE)
if remainder > 0:
data = data[:remainder]
if USE_SEEK_GROUND:
files[fname]['data'][seq] = data[:]
fp = open(os.path.join('downloads',
fname+'.download'), 'r+')
fp.seek(seq*MAX_DATA_SIZE, 0)
# goto absolute position, relative to start of file
fp.write(data)
fp.close()
else:
files[fname]['data'][seq] = data[:]
files[fname]['missing_seq'].remove(seq)
if len(files[fname]['missing_seq']) == 0:
print('all chunks from %s received,
finished.'%fname)
if USE_SEEK_GROUND:
144
os.rename(os.path.join('downloads',
fname+'.download'), os.path.join('downloads', fname))
else:
fp = open(os.path.join('downloads', fname),
'wb')
for seq in sorted(files[fname]['data']):
fp.write(files[fname]['data'][seq])
fp.close()
os.remove(os.path.join('downloads',
fname+'.download'))
files[fname]['data'] = {}
def take_picture(camera, resize=None, quality=85):
print('take_picture(): resize=', resize, ', quality=%d'%quality)
t = time.time()
tstr = time.strftime('%Y-%m-%d_%H-%M-%S-%Z.jpg')
fpath = os.path.join('images', tstr)
found = False
if os.path.exists(fpath):
# file exists, try some variants
found = True # assume found until otherwise (which might not happen)
for i in range(0, 20):
fpath = os.path.join('images', time.strftime('%Y-%m-%d_%H-
%M-%S-%Z') + '-%d.jpg'%i)
if not os.path.exists(fpath):
found = False
break
if found:
return ''
if True: #try:
camera.capture(fpath, resize=resize, quality=quality)
else: #except:
return ''
return fpath
def MHX_escape(data, FEND='\x0D'):
FESC = "\xDB"
TFEND = "\xDC"
TFESC = "\xDD"
packet = ""
for d in data:
if d == FEND:
packet = packet + FESC + TFEND
145
elif d == FESC:
packet = packet + FESC + TFESC
else:
packet += d
return packet
def MHX_unescape(data_escaped, FEND='\x0D'):
FESC = "\xDB"
TFEND = "\xDC"
TFESC = "\xDD"
data = ""
i = 0
while i < len(data_escaped)-1:
if data_escaped[i] == FESC and data_escaped[i+1] == TFEND:
data += FEND
i += 2
elif data_escaped[i] == FESC and data_escaped[i+1] == TFESC:
data += FESC
i += 2
else:
data += data_escaped[i]
i += 1
return data
def get_fname_padded(fname):
if len(fname) < FILENAME_SIZE:
return fname + (FILENAME_SIZE-len(fname))*' '
else:
return fname[:FILENAME_SIZE]
def multi_file_send(rx_ip, rx_port):
files = collections.OrderedDict()
for file in glob.glob('todownload/*'):
fname = file.split('/')[1]
files[fname] = {'chunker':CHUNKER(mode='HAB'), 'started':False,
'downloaded':False, 'download_count':0}
file_feedback_list = []
for fname in files:
file_feedback_list.append(fname)
file_feedback_count = 0
if USE_PAYLOAD_SERIAL:
146
ser = payload_UART.UART("/dev/ttyAMA0", 9600, '\x0D')
try:
import picamera
camera = picamera.PiCamera()
payload_start = False
photo_count = 0
except:
camera = None
payload_start = False
photo_count = 0
# Jah
#payload_start = True
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((rx_ip, rx_port))
HAB_TX_count = 0
fname_processing = ''
last_camera_time = time.time() - CAMERA_TAKE_INTERVAL
last_todownload_time = time.time() - CAMERA_TODOWNLOAD_INTERVAL
while True:
now = time.time()
if camera != None and payload_start:
if now - last_camera_time > CAMERA_TAKE_INTERVAL:
last_camera_time = now
photo_fpath = take_picture(camera)
elif now - last_todownload_time >
CAMERA_TODOWNLOAD_INTERVAL:
photo_fpath = take_picture(camera, resize=(640, 480),
quality=15)
if photo_fpath != '':
fname = '%08d.jpg'%photo_count
shutil.copyfile(photo_fpath,
os.path.join('todownload', fname))
last_todownload_time = now
photo_count += 1
time.sleep(1)
if USE_PAYLOAD_SERIAL:
data = ser.get_line() # this is NOT blocking!
else:
(rd, wr, err) = select.select([sock], [], [], 0)
147
if sock in rd:
try:
data = sock.recv(4096)
except socket.error:
data = None
if data != None:
if data[0:5] == MHX_COMMAND_FILE_COMPLETE:
if
data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].strip(
) not in files:
print('%s is not in download list
(completion)'%fname)
else:
fname =
data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].strip(
)
if fname in files:
files[fname]['downloaded'] = True
files[fname]['chunker'].remove_download_data()
payload = MHX_COMMAND_FILE_COMPLETE
+ data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE]
payload += (MAX_PAYLOAD_SIZElen(payload))*'\x00' # zero pad it to full length
crc32 =
files[fname]['chunker'].CRC32.calc_str(payload)
payload = HEADER + payload + crc32 +
AFTER_PAYLOAD + HEADER
sock.sendto(payload, (SDR_UDP_HAB_IP,
SDR_UDP_HAB_TX_PORT))
HAB_TX_count += 1
if HAB_TX_count >= PAUSE_COUNT:
if PAUSE_HAB_TX > 0:
HAB_TX_count = 0
time.sleep(PAUSE_HAB_TX)
elif data[0:5] == MHX_COMMAND_FILE_PROGRESS:
if
data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].strip(
) not in files:
print('%s is not in download
list'%data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].
strip())
else:
148
fname =
data[FNAME_START_OFFSET:FNAME_START_OFFSET+FILENAME_SIZE].strip(
)
if CHUCK_ASCII_VALUES == None:
seq_start = struct.unpack('<H',
data[BIT_MASK_SEQ_OFFSET:BIT_MASK_SEQ_OFFSET+2])[0]
format =
"<%sB"%CHUNK_BIT_MASK_BYTES_LEN
received = struct.unpack(format,
data[BIT_MASK_START_OFFSET:BIT_MASK_START_OFFSET+CHUNK_BIT_M
ASK_BYTES_LEN])
print('Ground RX chunks: ', end = '')
for i in range(0,
CHUNK_BIT_MASK_BITS_LEN):
mi = int(i/8)
mb = i%8
if received[mi]&(1<<mb):
if seq_start+i not in
files[fname]['chunker'].received:
files[fname]['chunker'].mark_received(seq_start+i)
print('%d
'%(seq_start+i), end='')
print()
else:
try:
s =
data[FNAME_START_OFFSET+FILENAME_SIZE:].split(',')
if len(s) >= 1:
print('Ground RX chuncks: ',
end = '')
for i in s:
if i == '':
continue
i = int(i)
if i not in
files[fname]['chunker'].received:
files[fname]['chunker'].mark_received(i)
print('%d
'%(i), end='')
print()
except:
print('Error in comand progress list,
skipping')
149
if fname != fname_processing:
# need to allow fname to have precedence
files[fname]['download_count'] = 0
i = 0
found = False
for name in file_feedback_list:
if fname == name:
found = True
break
else:
i += 1
if found:
file_feedback_count = i
elif MHX_COMMAND_START in
data[0:len(MHX_COMMAND_START)]:
print("PLSTART received")
payload_start = True
ser.write('Payload <PLSTART> processed, starting image
taking.', send_eol=True)
elif MHX_COMMAND_CLEAR in
data[0:len(MHX_COMMAND_CLEAR)]:
print("PLCLEAR received")
try:
shutil.rmtree('images')
except OSError:
pass
finally:
os.mkdir('images')
try:
shutil.rmtree('todownload')
except OSError:
pass
finally:
os.mkdir('todownload')
files = collections.OrderedDict()
file_feedback_list = []
file_feedback_count = 0
ser.write('Payload <PLCLEAR> processed, images
cleared.', send_eol=True)
elif MHX_COMMAND_TIME in
data[0:len(MHX_COMMAND_TIME)]:
tstr = data[len(MHX_COMMAND_TIME):]
150
p = subprocess.Popen(['date', '--utc', tstr],
stdout=subprocess.PIPE, stderr=subprocess.PIPE)
results, err = p.communicate()
p.wait()
t = time.time()
tstr = time.strftime('%Y-%m-%d %H:%M:%S')
print('Time synched from Bus to %s'%tstr)
ser.write('Payload time synched.', send_eol=True)
if not payload_start:
time.sleep(0.5)
continue
if len(file_feedback_list) == 0:
# this only happens in the beginning before any image for
downloading has been taken
file_list = glob.glob('todownload/*')
if len(file_list) == 0:
continue
for file in file_list:
fname = file.split('/')[1]
if fname not in files:
files[fname] = {'chunker':CHUNKER(),
'started':False, 'downloaded':False, 'download_count':0}
file_feedback_list.append(fname)
if fname_processing == '':
fname_processing = fname
else:
print('selecting file')
while True:
fname_processing =
file_feedback_list[file_feedback_count]
print('fname_processing=%s'%fname_processing)
if ((not files[fname_processing]['downloaded'])) and
(files[fname_processing]['download_count'] < MAX_DOWNLOAD_COUNT):
break
else:
print('%s completed, skipping'%fname_processing)
fname_processing = ''
for fname in files:
if not files[fname]['downloaded']:
fname_processing = fname
break
151
if fname_processing != '':
break
else:
# update files to download by examining the
todownload directory again
print('checking for new files.')
file_list = glob.glob('todownload/*')
print(file_list)
for file in file_list:
fname = file.split('/')[1]
if fname not in files:
files[fname] =
{'chunker':CHUNKER(), 'started':False, 'downloaded':False, 'download_count':0}
file_feedback_list.append(fname)
fname_processing = fname
break
break
if fname_processing == '':
print('no file to process')
time.sleep(0.5)
continue
if not files[fname_processing]['started']:
files[fname_processing]['started'] = True
files[fname_processing]['chunker'].prep_file_for_chunking(fname_processing)
chunk =
files[fname_processing]['chunker'].make_next_chunk(files[fname_processing]['download
_count'])
if chunk != '' and chunk != None:
payload = HEADER + chunk + AFTER_PAYLOAD + HEADER
sock.sendto(payload, (SDR_UDP_HAB_IP,
SDR_UDP_HAB_TX_PORT))
HAB_TX_count += 1
if HAB_TX_count >= PAUSE_COUNT:
if PAUSE_HAB_TX > 0:
HAB_TX_count = 0
time.sleep(PAUSE_HAB_TX)
else:
files[fname_processing]['download_count'] += 1
files[fname_processing]['chunker'].start_over()
152
if files[fname_processing]['download_count'] >= 5:
files[fname_processing]['download_count'] = 0
file_feedback_count += 1
if file_feedback_count >= len(file_feedback_list):
file_feedback_count = 0
fname_processing = file_feedback_list[file_feedback_count]
if __name__ == "__main__":
random.seed()
if sys.argv[1] == 'a':
multi_file_send('', SDR_UDP_HAB_RX_PORT)
sys.exit()
elif sys.argv[1] == 'd':
c = CHUNKER(mode='Ground')
c.dechunk('', SDR_UDP_GROUND_RX_PORT)