import cv2
import time
import HandTrackingModule as htm

pTime = 0
cTime = 0
cap = cv2.VideoCapture(0)
detector = htm.handDetector()

while True:
    success, img = cap.read()
    if not success:
        print("Camera not working")
        break

    img = detector.findHands(img, draw=False)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:
        print(lmList[4])

    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime

    cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN,
                2, (255, 0, 50), 2)

    cv2.imshow("image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):   # press q to quit
        break

cap.release()
cv2.destroyAllWindows()
