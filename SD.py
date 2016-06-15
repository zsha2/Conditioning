"""
 SD conditioning

 Create a GUI window to make user enter parameters
 And implement the actions of presenting reward 
 according to whether the rat has achieved the criterion
 within the duration of presenting SD

 The circuit:
 * Red LED attached from pin 11 to +5V
 * Green LED attached from pin 12 to +5V
 * 560 Ohm resistors attached from pin 11&12 to GND
 * Servo attached to pin 13
 * Button attached to pin 3

 """

# Import all needed libraries
import tkinter # GUI window
from time import sleep # delay to achieve time sequence
import pyfirmata # Arduino Uno board
import csv # saving information to files
import sys # correctly shut down the program
import time # give the rative time to record actions 
import math # help do calculation when getting ralative time

# inital variables
times = 0 
interval = 0 
duration = 0
sdinterval = 0
intertrial = 0

#associate the port
port = 'COM9'
board = pyfirmata.Arduino(port)

# Using iterator thread to avoid buffer overflow
it = pyfirmata.util.Iterator(board)
it.start()

# Define pins and corresponding mode
buttonpin = board.get_pin('d:3:i')
LEDpin = board.get_pin('d:11:o')
sdpin = board.get_pin('d:12:o')
servoPin = 13
board.digital[servoPin].mode = pyfirmata.SERVO


# create a variable to achieve correct detection of the state of button
# it is initially set to zero, once the button is pressed, it changed to 1, indicating the button is pressed
# and it will be changed to zero again only when the button is released
# after it back to zero, another press will be detected and count as active press
# meanwhile, this variable can count for the rising and falling edge of button
upanddown = 0
currenttimes = 0 # the times that the rat already press
looptime = 0 # record the start time of each trail

# open the file and save actions during experiment
output = open('output_sd.txt', 'w', newline='')

# start time of the experiment
starttime = time.time()

def startpressbutton():
    global times
    global interval
    global duration
    global sdinterval
    global intertrial
    global looptime
    global upanddown
    
    # disable the start button to avoid double-click during executing
    startButton.config(state=tkinter.DISABLED)
    
    # If user choose to pre-test
    # automatically start a trial that implement all the hardware
    # in order to check basic settings
    if preVar.get():
        sdpin.write(1)
        print ('please press the button once')
        if buttonpin.read() == 1: # if button is pressed, .read() will return 1
            if upanddown==0:
                sdpin.write(0)
                LEDpin.write(1)
                sleep(0.1)
                LEDpin.write(0) # make the LED blink once to indicate the press lead to reward
                currenttimes += 1 # count it into presses that lead to reward
                
                # if one press is detected, deliver the food
                if currenttimes == 1:
                    print ('press completed')
                    top.update()            
                    sleep(1)
                    print ('start feeding')
                    for i in range(0, 180):
                        # well-built function to control servo 
                        # which make the user can directly write the angle of servo
                        board.digital[servoPin].write(i)
                        top.update()
                        sleep(0.01)
                    print ('stay feeding')
                    sleep(2)
                    print ('feeding end')
                    for i in range(180, 1, -1):
                        board.digital[servoPin].write(i)
                        top.update()
                        sleep(0.01)
                    currenttimes = 0 # reset for a new trail                 
        if upanddown == 1:
            if buttonpin.read() == 0:
                upanddown = 0 

    # implement the experiment    
    else:
        # whether load the configuration
        # don't read from existing configuration
        if loadVar.get() == 0:
            times = float(timesEntry.get()) # the value get from GUI window, need to be converted into floating number
            interval = float(intervalEntry.get())
            duration = float(durationEntry.get())
            sdinterval = float(sdintervalEntry.get())
            intertrial = float(intertrialEntry.get())
            with open('configuration_sd.csv', 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(["times", "interval", "duration", "sdinterval", "intertrial"])
                data = [times, interval, duration, sdinterval, intertrial]
                w.writerow(data)
        # read from existing configuration and print them out
        else:
            with open('configuration_sd.csv', 'r', newline='') as f:
                r = csv.reader(f)
                data = None
                count = 0
                for row in r:
                    if count == 1:
                        data = row
                    count += 1
                times = float(data[0])
                interval = float(data[1])
                duration= float(data[2])
                sdinterval = float(data[3])
                intertrial = float(data[4])
                print("times: " + str(times))
                print("interval: " + str(interval))
                print("duration: " + str(duration))
                print("sdinterval: " + str(sdinterval))
                print("intertrial: " + str(intertrial))
                
        looptime = time.time() # get the start time for the first trial
        sdpin.write(1) # turn on SD
        # begin the first trail
        # call the function that contains the main body
        run()

def run():
    global times
    global interval
    global duration
    global sdinterval
    global intertrial
    global upanddown
    global currenttimes
    global looptime
    
    # if the difference between current and the start point of the trial is the duration of sd
    # in this statement, use very closing value to represent the equal condition
    # because the loop will be called every 1ms, regarding the deviation, the range is better than exactly equal
    # this means that the rat has not achieved the criterion so that the sd is not turn off
    if (time.time() - looptime) > (sdinterval - 0.001) and (time.time() - looptime) < (sdinterval + 0.001):
        #calculate the relative time for the press
        processtime = time.time() - starttime # unit in second
        hour = math.floor(processtime // 3600) # calculate hour
        minute = math.floor(processtime // 60 - (60 * hour)) # calculate minute
        second = round(processtime % 60, 2) # calculate seconds containing 2 digit of siginificant figures
        strtime = str(hour) + ":" + str(minute) + ":" + str(second)# time in the form of hh:mm:ss.xx
        outputstr = strtime + " : an sd end with no enough times pressed"
        output.write(outputstr + "\n") # record this action down to the file
        sdpin.write(0) # turn off SD
        
        # wait for intertrial interval
        # the reason that break down the delay is in order to update the condition to GUI window 
        # to avoid it fall into 'No responding'
        # also, during this process, useless presses can be detected and recorded
        ud3=0
        i=0
        t=intertrial*100
        while i<= t:
            i+=1
            top.update()
            sleep(0.01)
            if buttonpin.read() == 1:
                if ud3 == 0:
                    ud3 = 1
                    processtime = time.time() - starttime
                    hour = math.floor(processtime // 3600)
                    minute = math.floor(processtime // 60 - (60 * hour))
                    second = round(processtime % 60, 2)
                    strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                    outputstr = strtime + " : the rat press the button with NR"
                    output.write(outputstr + "\n")
            if ud3 == 1:
                if buttonpin.read() == 0:
                    processtime = time.time() - starttime
                    hour = math.floor(processtime // 3600)
                    minute = math.floor(processtime // 60 - (60 * hour))
                    second = round(processtime % 60, 2)
                    strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                    outputstr = strtime + " : the rat release the button"
                    output.write(outputstr + "\n")
                    ud3 = 0
                    
        # start a new trial
        processtime = time.time() - starttime
        hour = math.floor(processtime // 3600)
        minute = math.floor(processtime // 60 - (60 * hour))
        second = round(processtime % 60, 2)
        strtime = str(hour) + ":" + str(minute) + ":" + str(second)
        outputstr = strtime + " : a new sd start"
        output.write(outputstr + "\n")
        sdpin.write(1) # turn on SD
        looptime = time.time() # get the start time of the new trial
        
    if buttonpin.read() == 1:
        if upanddown == 0:
            upanddown = 1
            processtime = time.time() - starttime
            hour = math.floor(processtime // 3600)
            minute = math.floor(processtime // 60 - (60 * hour))
            second = round(processtime % 60, 2)
            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
            outputstr = strtime + " : the rat press the button with RR"
            output.write(outputstr + "\n")
            LEDpin.write(1)
            top.update()
            sleep(0.1)
            LEDpin.write(0)
            currenttimes += 1 # increase the number of presses that lead to reward
            
            # if the rat achieve the criterion, that actions according to the time sequence
            # during this section, all actions and presses that do not lead to reward are recorded to file as well
            if currenttimes == times:
                sdpin.write(0) # stop SD first
                # record the time that it achieves the criterion
                processtime = time.time() - starttime
                hour = math.floor(processtime // 3600)
                minute = math.floor(processtime // 60 - (60 * hour))
                second = round(processtime % 60, 2)
                strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                outputstr = strtime + " : enough times were pressed"
                output.write(outputstr + "\n")
                
                # delay for the interval between completing presses and delivering food
                # and the uesless presses during this interval is recorded
                ud1=0
                i=0
                t=interval*100
                while i<= t:
                    i+=1
                    top.update()
                    sleep(0.01)
                    if buttonpin.read() == 1:
                        if ud1 == 0:
                            ud1 = 1
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat press the button with NR"
                            output.write(outputstr + "\n")
                    if ud1 == 1:
                        if buttonpin.read() == 0:
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat release the button"
                            output.write(outputstr + "\n")
                            ud1 = 0
                            
                # deliver the food and record the time down
                processtime = time.time() - starttime
                hour = math.floor(processtime // 3600)
                minute = math.floor(processtime // 60 - (60 * hour))
                second = round(processtime % 60, 2)
                strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                outputstr = strtime + " : begin feeding"
                output.write(outputstr + "\n")
                for i in range(0, 180):
                    board.digital[servoPin].write(i)
                    top.update()
                    sleep(0.01)
                    
                # stay feeding and record the useless presses
                ud2=0
                i=0
                t=duration*100
                while i<= t:
                    i+=1
                    top.update()
                    sleep(0.01)
                    if buttonpin.read() == 1:
                        if ud2 == 0:
                            ud2 = 1
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat press the button with NR"
                            output.write(outputstr + "\n")
                    if ud2 == 1:
                        if buttonpin.read() == 0:
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat release the button"
                            output.write(outputstr + "\n")
                            ud2 = 0
                            
                # remove the food and record the time down
                processtime = time.time() - starttime
                hour = math.floor(processtime // 3600)
                minute = math.floor(processtime // 60 - (60 * hour))
                second = round(processtime % 60, 2)
                strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                outputstr = strtime + " : feeding finished"
                output.write(outputstr + "\n")
                for i in range(180, 1, -1):
                    board.digital[servoPin].write(i)
                    top.update()
                    sleep(0.01)
                    
                currenttimes=0 # reset currenttimes for new trial
                
                # after feeding
                # wait for intertrial interval and record the useless presses
                ud3=0
                i=0
                t=intertrial*100
                while i<= t:
                    i+=1
                    top.update()
                    sleep(0.01)
                    if buttonpin.read() == 1:
                        if ud3 == 0:
                            ud3 = 1
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat press the button with NR"
                            output.write(outputstr + "\n")
                    if ud3 == 1:
                        if buttonpin.read() == 0:
                            processtime = time.time() - starttime
                            hour = math.floor(processtime // 3600)
                            minute = math.floor(processtime // 60 - (60 * hour))
                            second = round(processtime % 60, 2)
                            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                            outputstr = strtime + " : the rat release the button"
                            output.write(outputstr + "\n")
                            ud3 = 0
                            
                # start a new trail and record the time 
                processtime = time.time() - starttime
                hour = math.floor(processtime // 3600)
                minute = math.floor(processtime // 60 - (60 * hour))
                second = round(processtime % 60, 2)
                strtime = str(hour) + ":" + str(minute) + ":" + str(second)
                outputstr = strtime + " : a new sd start"
                output.write(outputstr + "\n")
                sdpin.write(1)
                looptime = time.time() # get the start time of the new trial
    if upanddown == 1:
        if buttonpin.read() == 0:
            # record the releasing of the button
            processtime = time.time() - starttime
            hour = math.floor(processtime // 3600)
            minute = math.floor(processtime // 60 - (60 * hour))
            second = round(processtime % 60, 2)
            strtime = str(hour) + ":" + str(minute) + ":" + str(second)
            outputstr = strtime + " : rat releases the button, RR's rising edge"
            output.write(outputstr + "\n")
            upanddown = 0
            
    # recall itself every 1milisecond in order to keep monitoring the press         
    top.after(1,run)


# exit button function
def exit():
    board.exit()
    top.destroy()
    sys.exit()


# Initialize main windows with title
top = tkinter.Tk()
top.title("SD cdt")

#create the checkbox for pre-test
preVar = tkinter.IntVar()
preCheckBox = tkinter.Checkbutton(top,
                                  text="PRE-TEST MODE",
                                  variable=preVar)
preCheckBox.grid(column=2, row=1) # to manage the location on window

# create the checkbox for user to decide whether read previous configuration or not
loadVar = tkinter.IntVar()
loadCheckBox = tkinter.Checkbutton(top, text = "load config?", variable = loadVar)
loadCheckBox.grid(column = 2, row = 2)

# the times need to active the feeding
tkinter.Label(top, text = "Criterion: ").grid(column = 1, row = 3)
timesEntry = tkinter.Entry(top)
timesEntry.grid(column = 2, row = 3)
timesEntry.focus_set()

# the interval between receive and act
tkinter.Label(top, text = "Interval: ").grid(column = 1, row = 4)
intervalEntry = tkinter.Entry(top)
intervalEntry.grid(column = 2, row = 4)
intervalEntry.focus_set()

# how long will the feeding last
tkinter.Label(top, text = "Duration: ").grid(column = 1, row = 5)
durationEntry = tkinter.Entry(top)
durationEntry.grid(column = 2, row = 5)
durationEntry.focus_set()

# the interval between each time
tkinter.Label(top, text = "SD Duration: ").grid(column = 1, row = 6)
sdintervalEntry = tkinter.Entry(top)
sdintervalEntry.grid(column = 2, row = 6)
sdintervalEntry.focus_set()

# the intertrial between each time
tkinter.Label(top, text = "Intertrial interval: ").grid(column = 1, row = 7)
intertrialEntry = tkinter.Entry(top)
intertrialEntry.grid(column = 2, row = 7)
intertrialEntry.focus_set()


# Create Start and Exit button

# button for main function
startButton = tkinter.Button(top, text="Start", command=startpressbutton)
startButton.grid(column=2, row=8)

# exit button
exitButton = tkinter.Button(top, text="Exit", command=exit)
exitButton.grid(column=3, row=8)



# Start and open the window
top.mainloop()