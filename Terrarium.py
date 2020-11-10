# Terrarium mini project for EEE3095S

import threading 
import datetime 
import busio 
import board 
import digitalio 
import math 
import adafruit_mcp3xxx.mcp3008 as MCP 
from adafruit_mcp3xxx.analog_in import AnalogIn 
import RPi.GPIO as GPIO
import os
import ES2EEPROMUtils
import random
import BlynkLib

BLYNK_AUTH = 'iGH2zQoSe7PfZNE6GJGL8-rBwRzVqD-Z' #insert your Auth Token here
blynk = BlynkLib.Blynk(BLYNK_AUTH)
#timer = blynktimer.Timer()
GPIO.setmode(GPIO.BCM) # default setup is BCM

#define pins used and other admin
btn_power = 26
sample_rate = 5  # default is 5
pin = 6
value = 1
value2 = 2
btn = 19
is_on = True
thread = None
temp = ''
# get the starting time of the program
start_time = datetime.datetime.now()
current_time = 0
eeprom = ES2EEPROMUtils.ES2EEPROM()

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0 (LDR)
chan = AnalogIn(mcp, MCP.P0)

# creat an analog input channel on pin 1 (temp sensor)
chan1 = AnalogIn(mcp, MCP.P1)


def save_sample(time_start ,time_current , temp , buz):
    amount_samples = eeprom.read_byte(0)
    samples = []
    samples = eeprom.read_block(1,amount_samples*4)
    if  amount_samples < 21:
        samples.reverse()           #reverse list so that most recent is last
        samples.append(buz)         #add items to list in reverse order
        sample.append(temp)
        samples.append(time_current)
        samples.append(time_start)
        samples.reverse()           #reverse list back to original form but now with most recent 1st
        saver_samples(samples)
        pass
    else:
<<<<<<< HEAD
        a_list = collections.deque(samples)     # use python built in to rotate list 4 to the right
        a_list.rotate(4)
        samples_new = a_list
        samples[0] = time_start                 #after rotation last sample will be in 1st position
        samples[1] = time_current               #replace this with the most recent sample
=======
        #a_list = collections.deque(samples)     # use python built in to rotate list 4 to the right
        #a_list.rotate(4)
        #samples_new = a_list
        samples[0] = time_start
        samples[1] = time_current
>>>>>>> 2b2f09eb475063c0e39fbb8e79438ca93f73d17a
        samples[2] = temp
        samples[3] = buz



def timed_thread():
	#  use flag here to set condition for which when is_on is true, print as normal 
	global thread
	global is_on
	global sample_rate
	global start_time
	global current_time
	global temp
	thread = threading.Timer(sample_rate, timed_thread)
	thread.daemon = True
	thread.start()
	if is_on:
		temp = str(round(((chan1.voltage - 0.500)/0.010), 2))
		current_time = math.trunc((datetime.datetime.now() - start_time).total_seconds())
		print(str(start_time) + "s\t" + str(current_time) + "s\t\t" + temp + 'C' + "\t\t" + "*")
		save_sample(start_time, current_time, round(((chan1.voltage - 0.500)/0.010), 2), "*")
	else:
		print("logging disabled")

pass


def callback(self): # simple function to change sample rate between 3 states
	global sample_rate
	if sample_rate == 10:
		sample_rate = 5
	elif sample_rate == 5:
		sample_rate = 1
	else:
		sample_rate = 10
	pass


def callback_power(self):
	global is_on
	global thread
	if is_on:
		thread.join()
		os.system('clear')
		print("logging stopped")
		#		thread needs to be stopped on callback event, loggging is NOT stopped.yet
		is_on = False
		pass
	else:
		os.system('clear')
		startup()
#		timed_thread()
		is_on = True


@blynk.VIRTUAL_READ(7)
def V7_read_handler():
	global temp
	blynk.virtual_write(7, temp)


@blynk.VIRTUAL_READ(8)
def V8_read_handler():
	global sample_rate
	blynk.virtual_write(8, sample_rate)


@blynk.VIRTUAL_READ(9)
def V9_read_handler():
	global current_time
	blynk.virtual_write(9, current_time)


@blynk.VIRTUAL_READ(10)
def V10_read_handler():
	global is_on
	if is_on:
		blynk.virtual_write(10, 0)
	else:
		blynk.virtual_write(10, 1)
	

# Register Virtual Pins
@blynk.VIRTUAL_WRITE(1)
def my_write_handler(value):
	global is_on
	global thread
	if is_on:
		thread.join()
		os.system('clear')
		print("logging stopped")
		#		thread needs to be stopped on callback event, loggging is NOT stopped.yet
		is_on = False
		pass
	else:
		os.system('clear')
		startup()
#		timed_thread()
		is_on = True


# Register Virtual Pins
@blynk.VIRTUAL_WRITE(2)
def my_write_handler(value2):
	global sample_rate
	if sample_rate == 10:
		sample_rate = 5
	elif sample_rate == 5:
		sample_rate = 1
	else:
		sample_rate = 10
	pass


#@blynk.on("V6")
#def V6_read_handler(pin):
#	global temp
#	print('what')
#	output = (str(start_time) + "s\t" + str(current_time) + "s\t\t" + temp + 'C' + "\t\t" + "*")
#	blynk.virtual_write(pin, output)


def setup():
	timed_thread() # call it once to start thread
	GPIO.setup(btn_power, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button in pull up mode
	GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP) # configure as pull up resistor
	GPIO.add_event_detect(btn_power, GPIO.FALLING, callback=callback_power, bouncetime=1000) # set listener for button with 1000ms bounce time
	GPIO.add_event_detect(btn, GPIO.FALLING, callback=callback, bouncetime=500)	# adds detection event for falling edge with bounce of 0.5s
	pass


def startup():
	print("Time" + "\t\t\t" + "Sys Timer" + "\t" + "Temp" + "\t" + "Buzzer") # setting up display on program start, will need to set listener in setup after this


if __name__ == "__main__":
	startup() # calls initial display setup
	setup() #  call setup function to start up program
	# tell program to run indefinitely
	while True:
		blynk.run()
#		timer.run()
