import cv2
import time
import numpy as np 
import HandTrackingModule as htm
import math
from ctypes import cast,POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wcam, hcam = 640,480

cap = cv2.VideoCapture(0)
cap.set(3,wcam)
cap.set(4,hcam)
pTime = 0

detector = htm.handDetector(detectionCon=0.7)


device = AudioUtilities.GetSpeakers()
inference = device._dev.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
)
volume = cast(inference,POINTER(IAudioEndpointVolume))
#volume.GetMute()
#volume.GetMasterVolume()
volRange = volume.GetVolumeRange()
minvol = volRange[0]
maxvol = volRange[1]
vol = 0
volBar = 400
volper = 0

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:
        #print(lmList[4],lmList[8])

        x1, y1 = lmList[4][1],lmList[4][2]
        x2, y2 = lmList[8][1],lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1,y1),7,(255, 255, 0),cv2.FILLED)
        cv2.circle(img, (x2,y2),7,(255, 255, 0),cv2.FILLED)
        cv2.line(img,(x1,y1),(x2,y2),(255,255,0),3)
        cv2.circle(img,(cx,cy),7,(255,255,0),cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        print(length)

        #Hand range 50 - 300(21.5 265)
        # volume range = -63.5 to 0

        volBar = np.interp(length,[50,220],[400, 150])
        volper = np.interp(length,[50,220],[0,100])

        print(volper)
        volume.SetMasterVolumeLevelScalar(volper/100, None)

        if length <= 50:
            cv2.circle(img,(cx,cy),7,(255,0,255),cv2.FILLED)


    cv2.rectangle(img,(50,150),(85,400),(255,255,0),3)
    cv2.rectangle(img,(50,int(volBar)),(85,400),(255,255,0),cv2.FILLED)
    cv2.putText(img, f'{int(volper)} % ',(40,450),cv2.FONT_HERSHEY_COMPLEX,
            1,(255,255,0),2)
     
    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime

    cv2.putText(img, f'FPS : {int(fps)}',(40,50),cv2.FONT_HERSHEY_COMPLEX,
                1,(255,0,0),3)
    

    cv2.imshow("image",img)
    cv2.waitKey(1)
 