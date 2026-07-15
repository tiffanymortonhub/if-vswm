# example script for using PyGaze

# # # # #
# importing the relevant libraries
import random
import csv
import pandas as pd
from psychopy.experiment import params

import constants
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker

# # # # #
# experiment setup
#  TODO Add in lines that will create the trial table. As an example to data for a trial table was saved to stateData
#   and trialData in Genexpy/context_task.

# TODO Why does the existing version of the task use images as opposed to dots? Whatever you decide to use make sure
#  that the size of the stimulus remains the same. It should likely also be greyscale. If you use dots, pay important
#  attention to the color of the dots (should be assigned in the param file. If using images, make sure that you account
#  for memorability.

# TODO add in breaks at regular intervals. Lengths of time in between breaks should be specified in the param file.

# TODO add dialogue box for scanner type, participant ID and autopilot.

# TODO Make autopilot function and an option for the cursur to be used when the eyetracker is not connected. Both of these
#  would be used for testing.This comes after you get a basic working program. Wondering if dummy mode on pygaze automatically
#  does the cursor thing.
# create display object
disp = libscreen.Display()

# import parameters from csv file as a dictionary

# first create an empty dictionary
# TODO check to make sure that the use of the param file is comprehensive. Check the values set in HCL lab tools and your
#  context_ET param file as a way of ensuring that you have defined all necessary parameters.
param_dict = {}

with open ('param.csv', newline='', encoding='utf-8-sig') as file:
	reader = csv.reader(file)
	for row in reader:
		# skip empty lines and those where the first column begins with '#' (# will be used to make comments)
		if not row or row[0].strip().startswith('#'):
			continue
		# map the first column in the csv as the key and the second as the value and add it to param_dict
		key = row[0].strip()
		value = row[1].strip()
		param_dict[key] = value

# open dialogue box that prompts the user to choose experiment settings and supply subject ID

# Todo autopilot and cursor testing still need to be built


# create eyetracker object
tracker = eyetracker.EyeTracker(disp, 'eyelink', ())

# create keyboard object
keyboard = libinput.Keyboard(keylist=['space'], timeout=None)

# create logfile object
log = liblog.Logfile()
log.write(["trialnr", "trialtype", "endpos", "latency", "correct"])

# create screens
inscreen = libscreen.Screen()
inscreen.draw_text(text="When you see a cross, look at it and press space. Then make an eye movement to the black circle when it appears.\n\n(press space to start)", fontsize=24)
fixscreen = libscreen.Screen()
fixscreen.draw_fixation(fixtype='cross',pw=3)
targetscreens = {}
targetscreens['left'] = libscreen.Screen()
targetscreens['left'].draw_circle(pos=(int(constants.DISPSIZE[0]*0.25),constants.DISPSIZE[1]/2), fill=True)
targetscreens['right'] = libscreen.Screen()
targetscreens['right'].draw_circle(pos=(int(constants.DISPSIZE[0]*0.75),constants.DISPSIZE[1]/2), fill=True)
feedbackscreens = {}
feedbackscreens[1] = libscreen.Screen()
feedbackscreens[1].draw_text(text='correct', colour=(0,255,0), fontsize=24)
feedbackscreens[0] = libscreen.Screen()
feedbackscreens[0].draw_text(text='incorrect', colour=(255,0,0), fontsize=24)

# # # # #
# run the experiment

# calibrate eye tracker
tracker.calibrate()

# show instructions
disp.fill(inscreen)
disp.show()
keyboard.get_key()

# run 20 trials
for trialnr in range(1,21):
	# prepare trial
	trialtype = random.choice(['left','right'])

	# drift correction
	checked = False
	while not checked:
		disp.fill(fixscreen)
		disp.show()
		checked = tracker.drift_correction()

	# start eye tracking
	tracker.start_recording()
	tracker.status_msg("trial %d" % trialnr)
	tracker.log("start_trial %d trialtype %s" % (trialnr, trialtype))
	
	# present fixation
	disp.fill(screen=fixscreen)
	disp.show()
	tracker.log("fixation")
	libtime.pause(random.randint(750, 1250))
	
	# present target
	disp.fill(targetscreens[trialtype])
	t0 = disp.show()
	tracker.log("target %s" % trialtype)
	
	# wait for eye movement
	t1, startpos = tracker.wait_for_saccade_start()
	endtime, startpos, endpos = tracker.wait_for_saccade_end()
	
	# stop eye tracking
	tracker.stop_recording()
	
	# process input:
	if (trialtype == 'left' and endpos[0] < constants.DISPSIZE[0]/2) or (trialtype == 'right' and endpos[0] > constants.DISPSIZE[0]/2):
		correct = 1
	else:
		correct = 0
	
	# present feedback
	disp.fill(feedbackscreens[correct])
	disp.show()
	libtime.pause(500)
	
	# log stuff
	log.write([trialnr, trialtype, endpos, t1-t0, correct])

# end the experiment
log.close()
tracker.close()
disp.close()
libtime.expend()
