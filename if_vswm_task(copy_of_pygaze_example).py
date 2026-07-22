# example script for using PyGaze

# # # # #
# importing the relevant libraries
import random
import csv
import warnings
import re

from psychopy import gui, logging # these submodules are not loaded from a general import statement for psychopy.

import constants
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker

# # # # #
# experiment setup

# Current pilot is feedback / no feedback for a between subject
# Future versions will have within subject design with parametric variation of feedback to compare effects.
# Visual feedback = when the subject sees where the target and saccadic endpoints (could be just these two points, the
# two points with a line, or the two points with a line and a numeric measure of error, for instance) whereas abstract
# feedback is anything that isnt visual according to HC (for instance, this could be just providing a numeric measure of error).
# Todo If you can build in the option to do either between ir withing subjects design. If between all trials have feedback.
#  If within, assume it will have parametric or system variation of feedback. User will need to supply the number of
#  feedback types and the feedback condition (non, type 1, type two, fo instance will be assigned at the block level when initializing the experiment)

#  Todo build out the states [iti, fixation, stimulus, delay, response, feedback]. At this points get it to display the
#   desired stimulus types using the param file for the desired time (from param file), in the correct place
#   (specified in param file), accept a fixation in response, display appropriate
#
#  TODO Add in lines that will create the trial table. As an example to data for a trial table was saved to stateData
#   and trialData in Genexpy/context_task. Look up best practices for merging eyetracking data with experiment data. Custom
#   scripts? (this is a known solution, but it time consuming. Even if this is the option, there are still probably best
#   practices to maximize efficiency) Messages from tracker? Is there a way to have the experiment's output .csv basically
#   be a functional trial table with eye movement and trial level experiment data?

# TODO Why does the existing version of the task use images as opposed to dots? Whatever you decide to use make sure
#  that the size of the stimulus remains the same. It should likely also be greyscale. If you use dots, pay important
#  attention to the color of the dots (should be assigned in the param file. If using images, make sure that you account
#  for memorability.

# Todo Wait for fixation to start the trial. If break fixation, stimulus or delay, start next trial and add this one to the end.
#  Maybe have an option to turn this feature off in the param file.

# TODO add in breaks at regular intervals. Lengths of time in between breaks should be specified in the param file.

# TODO Make autopilot function and an option for the cursor to be used when the eyetracker is not connected. Both of these
#  would be used for testing.This comes after you get a basic working program. Wondering if dummy mode on pygaze automatically
#  does the cursor thing.

# Todo add practice round. Subjects should only advance to the actual task after achieving an average performance in the practice
#  round. Look at DOR task articles to find out what average performance is. Should be able to choose whether to include
#  the practice round in the dialog box.

# todo you are currently writing this as one long script. You should go back and make these functions and call the functions
#  instead of just running one long script. It will increase usability in the future and efficiency overall.

# create display object
disp = libscreen.Display()

## import parameters from csv file
# first create an empty dictionary
# TODO check to make sure that the use of the param file is comprehensive. Check the values set in HCL lab tools and your
#  context_ET param file as a way of ensuring that you have defined all necessary parameters.
param_dict = {}

# open the param file and iterate through the rows to populate the parameter dictionary
with open ('param.csv', newline='', encoding='utf-8-sig') as file:
	reader = csv.reader(file)
	for row in reader:
		# skip empty lines and those where the first column begins with '#' (# will be used to make comments)
		if not row or row[0].strip().startswith('#'):
			continue

		# map the first column in the csv as the key and the second as the value and add it to param_dict
		key = row[0].strip()
		value = row[1].strip()

		# Convert comma-separated values to a list
		if "," in value:
			param_dict[key] = [v.strip() for v in value.split(",")]
		else:
			param_dict[key] = value

## dialog box for experiment settings and subject ID
# Todo when referencing information collected from the dialog box dlg.data is a dictionary with the recorded responses.
#  Keys are 'experiment mode', 'include practice' and 'subject ID'

# Todo autopilot and cursor testing still need to be built

# Todo When varying the type of feedback provided, can use the dialog box to determine which type(s) of feedback the
#  subject sees throughout the experiment. Look for notes on feedback from your first year presentation, I think Xi had
#  comments about how to do this.
# start by making a dict with fields for the dialogue box
db_fields = {'subject ID': '', 'experiment mode': ['data collection', 'autopilot', 'cursor testing'],
			 'design': ['between subjects', 'within subjects'], 'include practice': True}


# create the dialog box
dlg = gui.DlgFromDict(dictionary=db_fields, title='Enter Experiment Info', tip= {
	'subject ID': '', 'experiment mode': 'data collection mode will initiate a connection to the eyetracker. autopilot '
										 'and cursor testing will start the experiment in dummy mode. Autopilot runs '
										 'through the experiment automatically, cursor testing allows the user to simulate '
										 'eye movements with the cursor using the mouse', 'include practice': 'When '
										 'selected, the subject must successfully complete the practice round before advancing '
										 'to the actual task'})

# check that an acceptable response was provided through the dialog box. If not, stop the experiment.
if not dlg.OK:
	logging.warning('User canceled info entry. Experiment ending...')
	warnings.warn('User canceled info entry. Experiment ending...')
	disp.close()
	libtime.expend()


## create eyetracker object
# Todo need conditional statement referencing dictionary with info from dialog box (see above) that will determine whether tracker type is 'eyelink'
#  or 'dummy' based on experiment mode. Need to think more about the best way to provide and automatic response for autopilot
#  to work. There is probably a way to quickly generate a fake, but plausible mouse input that will allow the experiment
#  to run without input from the user during testing.
tracker = eyetracker.EyeTracker(disp, 'eyelink', ())

## create keyboard object
keyboard = libinput.Keyboard(keylist=['space'], timeout=None)

## create logfile object
log = liblog.Logfile()
log.write(["trialnr", "trialtype", "endpos", "latency", "correct"])

## create screens
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

### Initialize the experiment
# create an empty data frame (DF)
exp_info =  {}

## calculate the total number of blocks
# find all the parameter fields related to the desired number of blocks
pattern = re.compile(r"n_(.+)_blocks")

# convert matching values to integers
for key in param_dict:
    if pattern.fullmatch(key):
        param_dict[key] = int(param_dict[key])

# sum them for the total number of blocks
total_blocks = sum( value for key, value in param_dict.items()
					if re.fullmatch(pattern, key))


## extract the number of experiments -> This will be based on the number of unique values that meet the regex pattern in
# the preceding lines of code.
unique_exp_values = {
    match.group(1)
    for key in param_dict
    if (match := pattern.fullmatch(key))
}
num_exp = len(unique_exp_values)
num_exp = list(range(1,num_exp+1))
## generate a list that will define the experiment type for each block
block_order = []

# convert variable type
param_dict["exp_types_s_consec"] = [
    int(v) for v in param_dict["exp_types_s_consec"]]

for _ in range(1,total_blocks+1):
	while True:
		candidate = random.choice(num_exp)

		if block_order and candidate in param_dict['exp_types_s_consec'] and candidate == block_order[-1]:
			continue
		block_order.append(candidate)
		break


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
