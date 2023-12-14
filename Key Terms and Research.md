Quadrature sampling
- two waves that are 90 degrees out of phase
- cos is in phase, sin is out of phase
- x = I cos (2pi f t) + Q sin (2 pi f t)
- the goal is to only have to adjust two amplitudes to achieve any function
- we use the imaginary component as a way to shift the original function to proper phase and magntude

FFT
- displays a graph with xaxis = frequency. This shows the magnitude, or time spent at, each frequency in the signal. It is no longer based on time.
- fft also figures out the delay (time shift) needed to apply to each of those frequencies s.t. the set of sinusoids can be added up to reconstruct the time-domain signal.
- We tell the SDR what frequency we want to sample at, or what frequency we want to transmit our samples at. On the receiver side, the SDR will provide us the IQ samples. For the transmitting side, we have to provide the SDR the IQ samples. In terms of data type, they will either be complex ints or floats.

Down-converting
- Let's say we want to sample at 2.4 GHz. An ADC capable of that is expensive!
- Downconverting shifts from a sinusoid function to a function centered at 0, with jsut the I and Q components
- 

Baseband
- frequency centered around 0 Hz
- create, record, or analyze signals here because we can use a lower sample rate
- signals are complex

Bandpass
- signal exists at some RF frequency that has been shifted up for the purpose of transmission.
- signals are real

IF
- intermediate frequency between baseband / bandpass

DC Spike
- if there is only a DC spike and the reste looks like noise, there is most likely not a signal there
- apparent when no signal is present

DC offset tuning
- Handled by oversampling a signal and off- tuning it.

Calculating Average Power
- usually done as a first step before attempting further dsp.
- * useful trick - if signal has a zero mean, you can use the variance. This is usually true for SDR *

Power Spectral Density
- Steps
1. Take FFT of samples (output of FFT is complex float)
1. Take the magnitude of FFT output
1. Square magnitude to get power
1. Normalize by dividing by FFT size and Sample rate
1. Convert to db using 10 log 10 (x)
1. Center the FFT at 0 Hz

Digital Modulation

1. Basically, digital modulation is a way of encoding multiple bits into symbols. Based on the modulation scheme, there can be many ways of changing the original signal to be transmitted. Based on the variations made, these can represent multiple bits of information.


Constellation Definition:
1. the IQ graph. Remember, I is amplitude and Q is phase.

Differential Coding
1. There is an inherent delay from flying through the air in the signal. This causes a random rotation to the constellation.
1. The purpose of differential coding is to provide a way to decide on if it is out of phase or not.
1. This is done by encoding by altering the transmission bits based on the value of the previous bit transmitted.
- Advantages: simple
- Disadvantages: if you have 1 error, now there is 2 errors.
- Alternative: Add pilot symbols periodically. Downside of this is you need to add a lot of them to be effective.


