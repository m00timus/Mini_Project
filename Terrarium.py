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
import blynklib

BLYNK_AUTH = 'iGH2zQoSe7PfZNE6GJGL8-rBwRzVqD-Z' #insert your Auth Token here
blynk = blynklib.Blynk(BLYNK_AUTH)
GPIO.setmode(GPIO.BCM) # default setup is BCM

#define pins used and other admin
btn_power = 26
sample_rate = 5  # default is 5
is_on = True
thread = None
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
        #a_list = collections.deque(samples)     # use python built in to rotate list 4 to the right
        #a_list.rotate(4)
        #samples_new = a_list
        samples[0] = time_start
        samples[1] = time_current
        samples[2] = temp
        samples[3] = buz


def timed_thread():
	#  use flag here to set condition for which when is_on is true, print as normal 
	global thread
	global is_on
	global sample_rate
	global start_time
	global current_time
	thread = threading.Timer(sample_rate, timed_thread)
	thread.daemon = True
	thread.start()
	if is_on:
		current_time = math.trunc((datetime.datetime.now() - start_time).total_seconds())
		print(str(start_time) + "s\t" + str(current_time) + "s\t\t" + str(round(((chan1.voltage - 0.500)/0.010), 2)) + 'C' + "\t\t" + "*")
		temp = str(round(((chan1.voltage - 0.500)/0.010), 2))
		#data = 'test data'
		#blynk.virtual_write(7, temp)
		save_sample(start_time, current_time, round(((chan1.voltage - 0.500)/0.010), 2), "*")
	else:
		print("logging disabled")

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


@blynk.handle_event('read temp (V7)')
def write_to_blynk_temp(pin):
	temp = '0'
    # Example: get sensor value, perform calculations, etc
	temp = str(round(((chan1.voltage - 0.500)/0.010), 2))
    # send value to Virtual Pin and store it in Blynk Cloud
	blynk.virtual_write(7, temp)


@blynk.handle_event('read paused state (V12)')
def write_to_blynk_is_on(pin):
	global is_on
    # send value to Virtual Pin and store it in Blynk Cloud
	blynk.virtual_write(12, is_on)


WRITE_EVENT_PRINT_MSG = "[WRITE_VIRTUAL_PIN_EVENT] Pin: V{} Value: '{}'"


@blynk.handle_event('write to V4 LED')
def write_virtual_pin_handler(pin, value):
	global is_on
	print(WRITE_EVENT_PRINT_MSG.format(pin, value))


def setup():
	timed_thread() # call it once to start thread
	GPIO.setup(btn_power, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button in pull up mode
	GPIO.add_event_detect(btn_power, GPIO.FALLING, callback=callback_power, bouncetime=500) # set listener for button with 500ms bounce time
	pass


def startup():
	print("Time" + "\t\t\t" + "Sys Timer" + "\t" + "Temp" + "\t" + "Buzzer") # setting up display on program start, will need to set listener in setup after this


if __name__ == "__main__":
	startup() # calls initial display setup
	setup() #  call setup function to start up program
	# tell program to run indefinitely
	while True:
		blynk.run()
