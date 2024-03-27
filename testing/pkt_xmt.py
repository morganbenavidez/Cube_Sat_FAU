#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: pkt_xmt
# Author: Jonathan Mazurkiewicz
# Description: packet transmit (for GNURadio 3.8.5)
# GNU Radio version: 3.8.5.0

from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import iio
import numpy
import packet_format_gr38


class pkt_xmt(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "pkt_xmt")

        ##################################################
        # Variables
        ##################################################
        self.usrp_rate = usrp_rate = 768000
        self.sps = sps = 2
        self.samp_rate = samp_rate = 1000000
        self.rs_ratio = rs_ratio = 1.04
        self.gain = gain = 0
        self.freq = freq = 915000000
        self.excess_bw = excess_bw = 0.35
        self.buffer_size = buffer_size = 0x8000
        self.bpsk = bpsk = digital.constellation_bpsk().base()
        self.bandwidth = bandwidth = 20000000
        self.SDR_ID = SDR_ID = "ip:192.168.3.1"

        ##################################################
        # Blocks
        ##################################################
        self.packet_format_gr38 = packet_format_gr38.blk()
        self.mmse_resampler_xx_0 = filter.mmse_resampler_cc(0, 1.0/((usrp_rate/samp_rate)*rs_ratio))
        self.iio_pluto_sink_0 = iio.pluto_sink(SDR_ID, freq, samp_rate, bandwidth, buffer_size, True, gain, '', True)
        self.digital_crc32_async_bb_1 = digital.crc32_async_bb(False)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=bpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False)
        self.blocks_tagged_stream_to_pdu_1 = blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 32, "packet_len")
        self.blocks_pdu_to_tagged_stream_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'packet_len')
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.5)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, './input_csv.csv', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_tagged_stream_to_pdu_1, 'pdus'), (self.digital_crc32_async_bb_1, 'in'))
        self.msg_connect((self.digital_crc32_async_bb_1, 'out'), (self.packet_format_gr38, 'PDU_in'))
        self.msg_connect((self.packet_format_gr38, 'PDU_out0'), (self.blocks_pdu_to_tagged_stream_0, 'pdus'))
        self.connect((self.blocks_file_source_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.mmse_resampler_xx_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_tagged_stream_to_pdu_1, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.mmse_resampler_xx_0, 0), (self.iio_pluto_sink_0, 0))


    def get_usrp_rate(self):
        return self.usrp_rate

    def set_usrp_rate(self, usrp_rate):
        self.usrp_rate = usrp_rate
        self.mmse_resampler_xx_0.set_resamp_ratio(1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio))

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.iio_pluto_sink_0.set_params(self.freq, self.samp_rate, self.bandwidth, self.gain, '', True)
        self.mmse_resampler_xx_0.set_resamp_ratio(1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio))

    def get_rs_ratio(self):
        return self.rs_ratio

    def set_rs_ratio(self, rs_ratio):
        self.rs_ratio = rs_ratio
        self.mmse_resampler_xx_0.set_resamp_ratio(1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio))

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.iio_pluto_sink_0.set_params(self.freq, self.samp_rate, self.bandwidth, self.gain, '', True)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.iio_pluto_sink_0.set_params(self.freq, self.samp_rate, self.bandwidth, self.gain, '', True)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw

    def get_buffer_size(self):
        return self.buffer_size

    def set_buffer_size(self, buffer_size):
        self.buffer_size = buffer_size

    def get_bpsk(self):
        return self.bpsk

    def set_bpsk(self, bpsk):
        self.bpsk = bpsk

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.iio_pluto_sink_0.set_params(self.freq, self.samp_rate, self.bandwidth, self.gain, '', True)

    def get_SDR_ID(self):
        return self.SDR_ID

    def set_SDR_ID(self, SDR_ID):
        self.SDR_ID = SDR_ID



def main(top_block_cls=pkt_xmt, options=None):
    
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass

    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
