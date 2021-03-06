import sys
import time
import os
import threading

sys.path.append(os.getcwd()+"/lib")

from Phidget22.Devices.BLDCMotor import *
from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from Phidget22.Net import *
from Phidget22.Devices.Encoder import *

# Variable initialization
prevValue = 0.0
prevTime=time.perf_counter()
vel=0
measVel=0
fileName="data.txt"
setVel=3 #Hz
maxVel=0.2 #Duty Cycle
maxAcc=0.2 #Duty Cycle/s
scale=360/12 #360 degrees/12 poles
encoderDataRate=20 #Must be int and is in milliseconds
motorDataRate=100 #Must be int and is in milliseconds
avVel=0.0
N=1
sumVel=0.0
stopped=False

class EncoderThread(threading.Thread):
    global encoderDataRate, avVel, setVel,f,fileSave
    def run(self):
        def PositionChangeHandler(self, positionChange, timeChange, indexTriggered):
            global prevTime
            currentTime=time.perf_counter()
##            print(str((currentTime-prevTime)*1000)+" "+str(positionChange/timeChange/360/4*1000))##
            if ("y" in fileSave) or ("Y" in fileSave):
##                f.write(str(positionChange/timeChange/360/4*1000)+"\r\n")
                f.write(str((currentTime-prevTime)*1000)+"\r\n")
            avVel=positionChange
            prevTime=currentTime
            
        def EncoderAttached(e):
            try:
                attached = e
                print("\nEncoder Attached")
                print("\n")
            except PhidgetException as e:
                print("Exception %i: %s" % (e.code, e.details))
                print("Press Enter to Exit...\n")
                readin = sys.stdin.read(1)
                exit(1)   
    
        def EncoderDetached(e):
            detached = e
            try:
                print("\nEncoder Detached")
            except PhidgetException as e:
                print("Exception %i: %s" % (e.code, e.details))
                print("Press Enter to Exit...\n")
                readin = sys.stdin.read(1)
                exit(1)
                

        def ErrorEvent(e, eCode, description):
            print("Error %i : %s" % (eCode, description))
    
        en= Encoder()   
        while not stopped:
            if not en.getAttached():
                try:
                    en.setOnAttachHandler(EncoderAttached)
                    en.setOnDetachHandler(EncoderDetached)
                    en.setOnErrorHandler(ErrorEvent)
                    en.setOnPositionChangeHandler(PositionChangeHandler)
                    
                    print("\nWaiting for encoder to attach")
                    en.openWaitForAttachment(5000)
                    
                    if(not en.getEnabled()):
                        en.setEnabled(1)
                    
                except PhidgetException as e:
                    print("Exception %i: %s" % (e.code, e.details))
                    print("Press Enter to Exit\n")
                    readin = sys.stdin.read(1)
                    exit(1)
                    
                en.setDataInterval(encoderDataRate)

        en.close()
        

# Motor connection
try:
    print("LIGO NCal Control")
    fileSave=input("Save data? (y/n)")
    if ("y" in fileSave) or ("Y" in fileSave):
        fileName=input("Enter data file name: ")
        # Data file to be appended to
        if ".txt" in fileName:
            if not os.path.exists("data/"+fileName):
                f=open("data/"+fileName,"a+")
            else:
                option=input("File already exists\nOverwrite, Append, or New file: ")
                if ("a" in option) or ("A" in option):
                    f=open("data/"+fileName,"a+")
                elif ("o" in option) or ("O" in option):
                    f=open("data/"+fileName,"w+")
                else:
                    i=1
                    newFileName=fileName.replace(".txt","")+"("+str(i)+")"+".txt"
                    while(os.path.exists("data/"+newFileName)):
                        newFileName=fileName.replace(".txt","")+"("+str(i)+")"+".txt"
                        i+=1
                    f=open("data/"+newFileName,"a+")
        else:
            if not os.path.exists("data/"+fileName+".txt"):
                f=open("data/"+fileName+".txt","a+")
            else:
                option=input("File already exists\nOverwrite, Append, or New file: ")
                if ("a" in option) or ("A" in option):
                    f=open("data/"+fileName+".txt","a+")
                elif ("o" in option) or ("O" in option):
                    f=open("data/"+fileName+".txt","w+")
                else:
                    i=1
                    newFileName=fileName+"("+str(i)+")"+".txt"
                    while(os.path.exists("data/"+newFileName)):
                        newFileName=fileName+"("+str(i)+")"+".txt"
                        i+=1
                    f=open("data/"+newFileName,"a+")
                    
    setVel=float(input("Set rotor frequency in Hz: "))
    
    if setVel>(maxVel*4000/60):
        print("Set velocity is greater than maximum.")
        print("Velocity set to "+str(maxVel*4000/60))
        
    ch = BLDCMotor()
    
except RuntimeError as e:
    print("Exception %s" % e.details)
    print("Press Enter to Exit...\n")
    readin = sys.stdin.read(1)
    exit(1)

def BLDCMotorAttached(e):
    try:
        attached = e
        print("\nMotor Attached")
        print("\n")
    except PhidgetException as e:
        print("Exception %i: %s" % (e.code, e.details))
        print("Press Enter to Exit...\n")
        readin = sys.stdin.read(1)
        exit(1)   
    
def BLDCMotorDetached(e):
    detached = e
    try:
        print("\nMotor Detached")
    except PhidgetException as e:
        print("Exception %i: %s" % (e.code, e.details))
        print("Press Enter to Exit...\n")
        readin = sys.stdin.read(1)
        exit(1)        

def ErrorEvent(e, eCode, description):
    print("Error %i : %s" % (eCode, description))

# This event is called at a regular cadence set by DataInterval timed by the controllers clock.    
def MotorVelocityUpdateHandler(e, velocity):
    global prevValue, prevTime, measVel, fileSave, avVel, N, sumVel

    currentValue=ch.getPosition()
    currentTime=time.perf_counter()
    
    # Outputs and saves set velocity and measured velocity
    print(str(ch.getVelocity()*4000/60) + "   " + str((currentValue-prevValue)/360/(currentTime-prevTime)))

    if ("y" in fileSave) or ("Y" in fileSave):
        f.write(str(ch.getVelocity()*4000/60) + "   " + str((currentValue-prevValue)/360/(currentTime-prevTime))+"\r\n")

    measVel=(currentValue-prevValue)/360/(currentTime-prevTime)
    
##    if N<10:
##        sumVel+=measVel
##        N+=1
##    else:
##        sumVel+=measVel
##        avVel=sumVel/10.0
##        N=1
##        sumVel=0.0
        
    prevValue=currentValue
    prevTime=currentTime

enThread=EncoderThread(name="Encoder Thread")
enThread.start()

# Initial setup
try:
    ch.setOnAttachHandler(BLDCMotorAttached)
    ch.setOnDetachHandler(BLDCMotorDetached)
    ch.setOnErrorHandler(ErrorEvent)
    #ch.setOnVelocityUpdateHandler(MotorVelocityUpdateHandler)

    print("\nWaiting for motor to attach")
    ch.openWaitForAttachment(5000)
except PhidgetException as e:
    print("Exception %i: %s" % (e.code, e.details))
    print("Press Enter to Exit\n")
    readin = sys.stdin.read(1)
    exit(1)

ch.setDataInterval(motorDataRate)    
ch.setRescaleFactor(scale) # Sets scaling of Position readout
ch.setAcceleration(maxAcc)

# Feedback loop
try:
    while(1):
##        vel=abs(0.5*(setVel-avVel)+setVel)/4000*60
        vel=setVel/4000*60
        # Velocity limit
        try:
            if(vel <=maxVel):            
                ch.setTargetVelocity(vel)
            else:            
                ch.setTargetVelocity(maxVel)
        except PhidgetException as e:
            print("Exception %i: %s" % (e.code, e.details))

        time.sleep(1)
            
except KeyboardInterrupt:
    # Close out
    stopped=True
    ch.setTargetVelocity(0)
    time.sleep(1)
    try:        
        ch.close()
        if ("y" in fileSave) or ("Y" in fileSave):
            f.close()
            
    except PhidgetException as e:
        print("Exception %i: %s" % (e.code, e.details))
        print("Press Enter to Exit\n")
        readin = sys.stdin.read(1)
        exit(1) 
    print("Disconnected from motor")   

                  

