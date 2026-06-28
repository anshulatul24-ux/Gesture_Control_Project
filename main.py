import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, model_complexity=1)

cap = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

prev_x, prev_y = 0, 0
smooth = 6
cooldown = 0
prev_scroll_y = 0

gesture_text = "NONE"
status_text = "ACTIVE"

pTime = 0

# -------- Finger Detection (FIXED THUMB LOGIC) --------
def fingers_up(hand_landmarks, hand_label):
    fingers = []

    # Thumb (hand-aware)
    if hand_label == "Right":
        fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
    else:  # Left hand
        fingers.append(1 if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x else 0)

    # Other fingers
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers
# ------------------------------------------------------

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    gesture_text = "NONE"
    status_text = "ACTIVE"

    if result.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(result.multi_hand_landmarks):

            hand_label = result.multi_handedness[i].classification[0].label
            fingers = fingers_up(hand_landmarks, hand_label)

            index = hand_landmarks.landmark[8]
            thumb = hand_landmarks.landmark[4]
            wrist = hand_landmarks.landmark[0]

            x = int(index.x * screen_w)
            y = int(index.y * screen_h)

            curr_x = prev_x + (x - prev_x) / smooth
            curr_y = prev_y + (y - prev_y) / smooth

            if cooldown > 0:
                cooldown -= 1

            # ✊ PAUSE
            if fingers == [0,0,0,0,0]:
                status_text = "PAUSED"
                gesture_text = "FIST"
                continue

            # ☝️ MOVE
            elif fingers == [0,1,0,0,0]:
                pyautogui.moveTo(curr_x, curr_y)
                gesture_text = "MOVE"

            # 🤏 LEFT CLICK
            elif fingers[0] == 1 and fingers[1] == 1 and cooldown == 0:
                pyautogui.click()
                gesture_text = "LEFT CLICK"
                cooldown = 10

            # ✌️ RIGHT CLICK
            elif fingers[1] == 1 and fingers[2] == 1 and cooldown == 0:
                pyautogui.rightClick()
                gesture_text = "RIGHT CLICK"
                cooldown = 10

            # 🤟 DOUBLE CLICK
            elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and cooldown == 0:
                pyautogui.doubleClick()
                gesture_text = "DOUBLE CLICK"
                cooldown = 10

            # 🖐️ SCROLL (UP/DOWN)
            elif fingers == [1,1,1,1,1]:
                curr_y_scroll = index.y

                if prev_scroll_y != 0:
                    if curr_y_scroll < prev_scroll_y - 0.01:
                        pyautogui.scroll(50)
                        gesture_text = "SCROLL UP"

                    elif curr_y_scroll > prev_scroll_y + 0.01:
                        pyautogui.scroll(-50)
                        gesture_text = "SCROLL DOWN"

                prev_scroll_y = curr_y_scroll

            # 👍 VOLUME UP
            elif thumb.y < index.y - 0.05:
                pyautogui.press("volumeup")
                gesture_text = "VOL UP"
                time.sleep(0.3)

            # 👎 VOLUME DOWN
            elif thumb.y > index.y + 0.05:
                pyautogui.press("volumedown")
                gesture_text = "VOL DOWN"
                time.sleep(0.3)

            prev_x, prev_y = curr_x, curr_y

    # -------- FPS --------
    cTime = time.time()
    fps = int(1 / (cTime - pTime + 0.0001))
    pTime = cTime

    # -------- UI --------
    cv2.putText(frame, f'Gesture: {gesture_text}', (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.putText(frame, f'Status: {status_text}', (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)

    cv2.putText(frame, f'FPS: {fps}', (500, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

    cv2.imshow("🔥 Ultimate AI Gesture System", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()