import cv2
import mediapipe as mp
import time


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5,
                 modelComplexity=1):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.modelComplexity = modelComplexity   # 0 = faster, 1 = more accurate

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(static_image_mode=self.mode,
                                        max_num_hands=self.maxHands,
                                        model_complexity=self.modelComplexity,
                                        min_detection_confidence=self.detectionCon,
                                        min_tracking_confidence=self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

        # Clean, thin drawing style for the hand skeleton
        self.lmStyle = self.mpDraw.DrawingSpec(color=(255, 255, 255),
                                               thickness=2, circle_radius=3)
        self.connStyle = self.mpDraw.DrawingSpec(color=(200, 200, 200),
                                                 thickness=2)

        self.results = None   # filled by findHands()

    def findHands(self, img, draw=True, detectWidth=None):
        """
        Finds hands in the image.
        detectWidth: if set (e.g. 640), detection runs on a smaller copy of the
                     image (much faster at HD). Drawing still happens on the
                     full-size image.
        """
        if detectWidth and img.shape[1] > detectWidth:
            scale = detectWidth / img.shape[1]
            small = cv2.resize(img, (detectWidth, int(img.shape[0] * scale)))
        else:
            small = img

        imgRGB = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS,
                                               self.lmStyle, self.connStyle)

        return img

    def findPosition(self, img, handNo=0, draw=True):
        lmList = []
        if self.results is not None and self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                h, w, c = img.shape
                for id, lm in enumerate(myHand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        return lmList


def main():
    pTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()

    while True:
        success, img = cap.read()
        if not success:
            print("Camera not working")
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img)
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


if __name__ == "__main__":
    main()
