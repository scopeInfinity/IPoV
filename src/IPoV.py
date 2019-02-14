import threading
import time
import logging
import math
from config import *
import sounddevice as sd
import numpy as np 

	
logging.basicConfig()
logger = logging.getLogger("IPoV")
slogger = logging.getLogger("IPoV::Sender")
rlogger = logging.getLogger("IPoV::Receiver")
logger.setLevel(log_level);
slogger.setLevel(log_level);
rlogger.setLevel(log_level);

BITRATE       = 10
BYTEMULTIPLEX = 1
POLLTIME_SEND = 0.2 # seconds

assert BYTEMULTIPLEX == 1

class IPoV():
	"""Point to Point connection for IPoV"""
	def __init__(self):
		self.send_buffer = []
		self.receive_buffer = []
		self.delim = '#'
		
		self.send_thread = threading.Thread(target=sender, args = (self,))
		self.send_thread.daemon = True
		self.send_thread.start()
		
		self.recv_thread = threading.Thread(target=capture_audio, args = (self, None))
		self.recv_thread.daemon = True
		self.recv_thread.start()
		logger.info("IPoV created")

	def send(self, message):
		self.send_buffer.extend(list(message + self.delim))
	
	def receive_pull(self):
		msg = None
		if self.delim in self.receive_buffer:
			parts = str(self.receive_buffer).partition(self.delim)
			msg = parts[0]
			self.receive_buffer = list(parts[2])
		return msg

	def sendByte(self):
		if self.send_buffer:
			byte = self.send_buffer[0]
			self.forwardByte(byte)
			self.send_buffer = self.send_buffer[1:]
			slogger.info("'{}' byte send.".format(byte))
			return True
		return False

	def forwardByte(self, byte):
		'''just forward a byte, no checks'''
		byte = ord(byte)
		# MSB on high index,, little or small?? ending
		bits = [1 if byte&(1<<i) else 0 for i in range(8)]
		slogger.debug("Going to play: {}".format(bits))
		duration = 1 #seconds
		
		frequencies = [getfreq(i) for i, bit in enumerate(bits) if bit]
		slogger.debug("Playing '{}' Started!".format(byte))
		play_freq(frequencies, duration)
		time.sleep(duration) #Silent gap
		slogger.debug("Playing '{}' Completed!".format(byte))
		

def play_freq(frequencies, duration, wait = True):
	'''play frequenceies in hz and duration in seconds'''
	samples = duration * SAMPLERATE
	signal = np.array([0] * samples)
	for freq in frequencies:
		signal_freq = []
		for x in range(samples):
			amplitude = math.sin(2*math.pi/SAMPLERATE*x*freq)
			signal_freq.append(amplitude)
		signal = signal + np.array(signal_freq)
	# Averaging signal
	signal = signal / len(frequencies)
	sd.play(signal, SAMPLERATE)
	if wait:
		sd.wait()

def sender(connection):
	slogger.info("Sender Started")
	while True:
		time.sleep(POLLTIME_SEND)
		while connection.sendByte():
			pass
		

def getfreq(bitposition):
	BIT_SPLIT = BYTEMULTIPLEX * 8
	assert bitposition>=0
	assert bitposition<BIT_SPLIT
	
	LOW = 1000
	HIGH = 10000
	LOG_BASE = 2
	low_log = math.log(LOW, LOG_BASE)
	high_log = math.log(HIGH, LOG_BASE)
	
	frequencies = [ (low_log*(BIT_SPLIT-1-i) + high_log*i)/(BIT_SPLIT-1) for i in range(BIT_SPLIT)]
	frequencies = [math.pow(LOG_BASE, f) for f in frequencies]
	return frequencies[bitposition]

def capture_audio(connection, callback):
    import pyaudio
    import wave as wv
    from array import array

    FORMAT=pyaudio.paInt16
    CHUNK=SAMPLERATE
    COUNTCHUNK= (SAMPLERATE+CHUNK-1)/CHUNK
    RECORD_SECONDS=1
    FILE_NAME="/tmp/mic_rec.wav"

    audio=pyaudio.PyAudio()

    stream=audio.open(format=FORMAT,
                      rate=SAMPLERATE,
                      channels=1,
                      input=True,
                      frames_per_buffer=CHUNK)

    #starting recording
    last = time.time()
    lastloudsoundtime = time.time()-100000
    wave = []
    time.sleep(5)
    rlogger.info("Started!")
    import matplotlib.pyplot as plt
    while True:
        data=stream.read(CHUNK)
        data_chunk=array('h',data)
        signal = [abs(x) for x in np.fft.fft(data_chunk)]
        
        print signal
        vol=max(signal)

        plt.plot(signal)
        plt.show()
        print(vol)
#         wave.append(data)
#         if len(wave) > COUNTCHUNK:
#             wave.pop(0)
#         if(vol>=1500):
#             lastloudsoundtime = time.time()
#         if(time.time()-last>0.05 and time.time()-lastloudsoundtime<0.8):
#             last = time.time()
#             if len(wave) == COUNTCHUNK:
#                 #writing to file
#                 wavfile=wv.open(FILE_NAME,'wb')
#                 wavfile.setnchannels(1)
#                 wavfile.setsampwidth(audio.get_sample_size(FORMAT))
#                 wavfile.setframerate(SAMPLERATE)
#                 wavfile.writeframes(b''.join(wave))
#                 wavfile.close()
#                 if callback_free[0]:
#                     callback_free[0]=False
#                     callback(callback_free,FILE_NAME,final_callback)
#                     # print("Something is said")
#         else:
#             pass
#             # callback(None,None)
#             # print("Nothing is said")
#         # print("\n")
#  