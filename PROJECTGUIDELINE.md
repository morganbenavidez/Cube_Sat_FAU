# Project Group 9  

Development of a versatile telecommunications solution for nanosatellites and CubeSats operating in UHF and S-Bands.

---

## Design Guidelines

### Why was this document made?

Our scope is a bit confused. This purpose of this document is to more rigidly define the goal of this project, and how we might accomplish that. This document is largely guided by the advice of our sponsor.

### What is the end goal of our project?

The solution that we provide is **not** a satellite. It is also **not** the complete software package for that satellite.

Our project **is** the two *software radios* that will:
 - Collect data fed from the satellite. 
 - Transmit said data to a ground station.
 - Collect data transmitted from the satellite.
 - Decode transmitted data.
 - Output data.

The exact nature of the *input* and *output* is irrelevant to us, and beyond our scope. For all intents and purposes, we are just being feed binary data, that we must send and recover between a transmitter and receiver. Generation and processing of that data is, actually, beyond our scope. We can of-course help tackle these issues, but only once our radios are functional. 

### Where do we start?

To design these SDRs we need to understand and learn [GNU Radio](https://wiki.gnuradio.org). Start with the [tutorials](https://wiki.gnuradio.org/index.php?title=Tutorials) and work your way up. *Ideally* you will work until you complete [Narrowband FM](https://wiki.gnuradio.org/index.php?title=Simulation_example:_Narrowband_FM_transceiver) and [Frequency Shift Keying](https://wiki.gnuradio.org/index.php?title=Simulation_example:_FSK). Most of this doesn't require **actual** knowledge of how radios work. That, I believe, is fine. The reason for this will be explained in the next part. For know, remember that we are limited by time, and we may need to skip some tutorials to speed up the learning process. However, we should all do as many as we think we have time for.

### So how *exactly* do we make the radio for *our* project?

I don't have a specific answer to this, but I know how we will figure it out. There is an amateur satellite designed for schools and universities. It's called the [FUNcube](https://amsat-uk.org/funcube/funcube-cubesat/) and it has a lot of documentation. The plan is, we are going to use their [handbook](https://funcubetest2.files.wordpress.com/2010/11/funcube-handbook-en_v13.pdf) to recreate their *hardware* radio system as a *software* radio system. They explain every component in good detail, so the only challenge is to convert each component to its appropriate GNU Radio component. Once we have completed this, the bulk of our work is done. All that is left to (possibly) test against the gr-satellites' FUN-Cube-1 receiver, and to adjust the frequency to our own specification.

### What is the immediate next step?

As the assignments are coming due, we need to create documentation for the design of our SDR. Since we will following the FUNcube design, this should not be too hard.

---

*Document produced in Multi Markdown v6 by Zee Fisher*


[>SDR]: Software-Defined Radio
[>SDRs]: Software-Defined Radios

