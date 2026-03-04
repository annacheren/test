# -*- coding: utf-8 -*-
from pepper.robot import Pepper
from demo import uploadPhotoToWeb
import random, os, time
import qi

''' 
This is a minimal demo showing you how to work with Pepper class and reach some of the frequently used functions.

Please keep in mind that this code only works with Python 2!

To launch the demo on your computer, you need to have the Pepper SDK 2.5.10 library for Python 2.7 
(imported as qi or naoqi). It can be installed from: 
https://www.softbankrobotics.com/emea/en/support/pepper-naoqi-2-9/downloads-softwares
Also, if you have Linux, add the path to qi in your .bashrc:
export PYTHONPATH=${PYTHONPATH}:/home/yourusername/pynaoqi/lib/python2.7/site-packages

Then install all the other requirements using:
pip2 install -r ./requirements.txt 
'''


def basic_demo(robot):
    """ Shows how to work with the Pepper class and how to use the basic functions."""
    robot.set_english_language()
    robot.set_volume(50)
    robot.say("Hello, I am Pepper robot. This is a demo for upcoming experiment.")
    #robot.start_animation(random.choice(["Hey_1", "Hey_3", "Hey_4", "Hey_6"]))

    robot.say("First, I will try to recognize you. If I know you, I will greet you by your name. If not, I will say that I don't know you yet.")



    robot.say("The last important thing is to switch between autonomous mode. Now it is turned on and thanks to that I'm interactive. If "
              "I should move, the autonomous regime needs to be turned off so that it doesn't confuse me.")
    #robot autonimous life is off
    robot.autonomous_life_off()
    #contextual gestures off when bodylanguage is disabled
    robot.say("Thats it.My Autonimous life is off and contextual gestures is disabled ", 
    bodylanguage="disabled")


    robot.move_joint_by_angle(["LShoulderRoll", "LShoulderPitch", "RShoulderRoll", "RShoulderPitch"], [-2.9,-1, -2.9, -1], 0.4)
    time.sleep(2)
    robot.stand()
    robot.autonomous_life_on()

def raise_and_release_object(self, table_height_cm):
    """
    Pepper raises right hand to (table_height + 40cm),
    says sentence,
    releases object,
    and returns to neutral.
    Fully safe for NAOqi + Python 2.7.
    """

    import time

    # -------------------------
    # Compute Target Height
    # -------------------------
    target_height = table_height_cm + 40.0

    if target_height < 95.0:
        target_height = 95.0
    if target_height > 135.0:
        target_height = 135.0

    shoulder_pitch = 1.45 - ((target_height - 90.0) * (0.7 / 30.0))

    if shoulder_pitch < 0.5:
        shoulder_pitch = 0.5
    if shoulder_pitch > 1.5:
        shoulder_pitch = 1.5

    # -------------------------
    # Prepare Robot
    # -------------------------
    self.motion_service.wakeUp()
    self.posture_service.goToPosture("StandInit", 0.5)
    time.sleep(1.0)

    # -------------------------
    # 1️⃣ Close Hand (joint control only)
    # -------------------------
    self.motion_service.angleInterpolation(
        ["RHand"],
        [[0.0]],          # 0 = closed
        [[1.0]],
        True
    )

    # -------------------------
    # 2️⃣ Raise Arm Smoothly
    # -------------------------
    names = [
        "HeadPitch", "HeadYaw",
        "RShoulderPitch", "RShoulderRoll",
        "RElbowYaw", "RElbowRoll"
    ]

    angleLists = [
        [0.15],               # HeadPitch (look slightly at hand)
        [-0.1],               # HeadYaw
        [shoulder_pitch],     # ShoulderPitch (height control)
        [-0.15],              # ShoulderRoll
        [1.2],                # ElbowYaw
        [1.1]                 # ElbowRoll
    ]

    timeLists = [
        [2.5],
        [2.5],
        [2.5],
        [2.5],
        [2.5],
        [2.5]
    ]

    self.motion_service.angleInterpolation(
        names,
        angleLists,
        timeLists,
        True
    )

    # -------------------------
    # 3️⃣ Rotate Wrist (Palm Down)
    # -------------------------
    self.motion_service.angleInterpolation(
        ["RWristYaw"],
        [[-1.3]],
        [[1.5]],
        True
    )

    time.sleep(0.3)

    # -------------------------
    # 4️⃣ Speak (SAFE – TextToSpeech only)
    # -------------------------
    self.tts.say("Here is what you asked to bring")

    # -------------------------
    # 5️⃣ Open Hand (Release)
    # -------------------------
    self.motion_service.angleInterpolation(
        ["RHand"],
        [[1.0]],          # 1 = open
        [[1.0]],
        True
    )

    time.sleep(0.8)

    # -------------------------
    # 6️⃣ Small Human Micro Lift
    # -------------------------
    self.motion_service.angleInterpolation(
        ["RShoulderPitch"],
        [[shoulder_pitch + 0.05]],
        [[1.0]],
        True
    )

    # Close hand again
    self.motion_service.angleInterpolation(
        ["RHand"],
        [[0.0]],
        [[1.0]],
        True
    )

    # -------------------------
    # 7️⃣ Return to Neutral
    # -------------------------
    names_return = [
        "HeadPitch", "HeadYaw",
        "RWristYaw",
        "RShoulderPitch",
        "RShoulderRoll",
        "RElbowRoll"
    ]

    angleLists_return = [
        [0.0],
        [0.0],
        [0.0],
        [1.45],
        [-0.05],
        [1.0]
    ]

    timeLists_return = [
        [2.5],
        [2.5],
        [2.5],
        [2.5],
        [2.5],
        [2.5]
    ]

    self.motion_service.angleInterpolation(
        names_return,
        angleLists_return,
        timeLists_return,
        True
    )

    time.sleep(1.0)
def rpy_to_rotvec(roll, pitch, yaw):
    """
    Convert Roll-Pitch-Yaw to rotation vector (axis-angle).
    Pure math, Python 2.7 compatible.
    """

    import math

    # Rotation matrices
    cr = math.cos(roll)
    sr = math.sin(roll)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)

    # R = Rz(yaw) * Ry(pitch) * Rx(roll)
    R11 = cy*cp
    R12 = cy*sp*sr - sy*cr
    R13 = cy*sp*cr + sy*sr

    R21 = sy*cp
    R22 = sy*sp*sr + cy*cr
    R23 = sy*sp*cr - cy*sr

    R31 = -sp
    R32 = cp*sr
    R33 = cp*cr

    # Convert rotation matrix to axis-angle
    trace = R11 + R22 + R33
    angle = math.acos((trace - 1.0) / 2.0)

    if abs(angle) < 1e-6:
        return 0.0, 0.0, 0.0

    rx = (R32 - R23) / (2.0 * math.sin(angle))
    ry = (R13 - R31) / (2.0 * math.sin(angle))
    rz = (R21 - R12) / (2.0 * math.sin(angle))

    return rx * angle, ry * angle, rz * angle
def point_table_precise(robot,
                        table_center_x,
                        table_center_y,
                        table_width,
                        table_length,
                        table_height,
                        direction,
                        arm="auto"):

    import math
    import time

    motion = robot.motion_service

    # --------------------------------------------------
    # 1️⃣ Compute exact target on table
    # --------------------------------------------------

    if direction == "left":
        target_y = table_center_y + table_width / 2.0
    elif direction == "right":
        target_y = table_center_y - table_width / 2.0
    else:
        target_y = table_center_y

    target_x = table_center_x
    target_z = table_height

    # --------------------------------------------------
    # 2️⃣ Choose arm automatically
    # --------------------------------------------------

    if arm == "auto":
        effector = "L" if target_y > 0 else "R"
    else:
        effector = "L" if arm == "left" else "R"

    # --------------------------------------------------
    # 3️⃣ Compute pointing geometry
    # --------------------------------------------------

    horizontal_dist = math.sqrt(target_x**2 + target_y**2)

    # Lift arm high enough to go above table
    shoulder_pitch = 0.35   # strong forward lift
    shoulder_roll = (-0.3 if effector == "R" else 0.3)

    # Add lateral correction toward target
    shoulder_roll += (-target_y * 0.6 if effector == "R"
                      else -target_y * 0.6)

    shoulder_roll = max(-1.2, min(1.2, shoulder_roll))

    # Strong elbow extension for pointing
    elbow_yaw = 1.5 if effector == "R" else -1.5
    elbow_roll = 1.2 if effector == "R" else -1.2

    # Wrist aligned flat toward table
    wrist_yaw = -1.5 if effector == "R" else 1.5

    # --------------------------------------------------
    # 4️⃣ Raise Arm Above Desk
    # --------------------------------------------------

    names = [
        effector + "ShoulderPitch",
        effector + "ShoulderRoll",
        effector + "ElbowYaw",
        effector + "ElbowRoll",
        effector + "WristYaw"
    ]

    angles = [
        [shoulder_pitch],
        [shoulder_roll],
        [elbow_yaw],
        [elbow_roll],
        [wrist_yaw]
    ]

    times = [
        [2.0],
        [2.0],
        [2.0],
        [2.0],
        [2.0]
    ]

    motion.angleInterpolation(names, angles, times, True)

    # --------------------------------------------------
    # 5️⃣ Make Hand Look Like Finger Pointing
    # --------------------------------------------------

    # Close hand slightly (creates pointing illusion)
    motion.angleInterpolation(
        [effector + "Hand"],
        [[0.3]],   # mostly closed but not fist
        [[1.0]],
        True
    )

    # --------------------------------------------------
    # 6️⃣ Head Follows Finger Direction
    # --------------------------------------------------

    head_yaw = math.atan2(target_y, target_x)

    # Look slightly downward to table
    head_pitch = 0.3

    motion.angleInterpolation(
        ["HeadYaw", "HeadPitch"],
        [[head_yaw], [head_pitch]],
        [[1.2], [1.2]],
        True
    )

    time.sleep(1.5)

    # --------------------------------------------------
    # 7️⃣ Look Back at Person
    # --------------------------------------------------

    motion.angleInterpolation(
        ["HeadYaw", "HeadPitch"],
        [[0.0], [0.0]],
        [[1.2], [1.2]],
        True
    )

    # --------------------------------------------------
    # 8️⃣ Speak
    # --------------------------------------------------

    robot.tts.say("Looks like this one is right")
if __name__ == "__main__":
    # Press Pepper's chest button once and he will tell you his IP address
    ip_address = "192.168.0.200"
    port = 9559
    
    robot = Pepper(ip_address, port)
    #basic_demo(robot)
    robot.set_security_distance(0.01)
    
    #  1. => Turn OFF autonomous life
    robot.autonomous_life_off()

    # 2. Disable breathing (very important)
    robot.motion_service.setBreathEnabled("Body", False)

    # 3. Disable idle posture
    robot.motion_service.setIdlePostureEnabled("Body", False)


    #  4. Initialize TextToSpeech
    robot.tts = robot.session.service("ALTextToSpeech")
    
    
    # 4. Disable awareness
    awareness = robot.session.service("ALBasicAwareness")
    awareness.stopAwareness()
    awareness.setEngagementMode("Unengaged")

    # 5. Disable contextual gestures
    animated_speech = robot.session.service("ALAnimatedSpeech")
    #animated_speech.setBodyLanguageMode("disabled")<=this is not working for some reason, so we will disable contextual gestures using the method below


    #  5. Run your function
    #
    # raise_and_release_object(robot, 150)
    #setup_experiment_mode(robot)

    point_table_precise(
    robot,
    table_center_x=1.0,
    table_center_y=0.0,
    table_width=0.36,
    table_length=0.61,
    table_height=0.75,
    direction="left",
    arm="auto"
    )
    raise_and_release_object(robot, 150)

    #  6. (Optional) Turn autonomous life back ON
    #robot.autonomous_life_on()





