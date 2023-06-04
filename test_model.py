from tensorflow import keras
import user_interface as ui
import numpy as np
from pynput import keyboard
from time import time
import sys
import threading
import collections
import os

q = collections.deque()  # queue for the windows prediction calculation
dwell = []  # The list of key dwell times
startTimes = np.zeros(254)  # Saves the time in witch a key was pressed
startTyping = 0  # start time
DownDown = []  # DownDown array
virtualKeysID = []  # key ID array
last_key_press_time = 0  # a variable used to calculate the duration between keystrokes
count = 0  # number of tuples inserted
model = None
sem = threading.Semaphore(0)  # semaphore to count the number of windows in the queue
mutex = threading.Semaphore(1)  # semaphore to protect the insert and pop operations on the queue
output_label, output_textbox2, window, switch, username = None, None, None, None, None
fail_count = 0


def on_press(key):
    global last_key_press_time
    global startTyping
    global count

    current_time = time()

    is_first_typed(current_time)

    last_key_press_time = current_time
    vk = get_virtual_key(key)
    startTimes[vk] = current_time
    virtualKeysID.append(vk / 254)
    sys.stdout.flush()


def is_first_typed(current_time):
    global startTyping
    if startTyping == 0:
        startTyping = current_time
    if last_key_press_time != 0:
        DownDown.append(current_time - last_key_press_time)


def on_release(key):
    global count

    append_times(key)

    if count > 30:
        append_to_queue(count)

    count += 1

    if key == keyboard.Key.esc:
        return False


def append_times(key):
    current_time = time()
    vk = get_virtual_key(key)
    start = startTimes[vk]
    startTimes[vk] = 0
    dwell.append(current_time - start)


def append_to_queue(num):
    mutex.acquire()
    q.append(num)
    mutex.release()
    sem.release()


def get_virtual_key(key):
    return key.vk if hasattr(key, 'vk') else key.value.vk


def predict_and_print(position_number):
    global dwell
    global DownDown
    global virtualKeysID
    global model

    dwell_chunk = np.array(dwell[position_number - 31:position_number])
    down_down_chunk = np.array(DownDown[position_number - 31:position_number])
    up_down_chunk = down_down_chunk - dwell_chunk

    final_vector = get_final_vector(down_down_chunk, dwell_chunk, position_number, up_down_chunk, virtualKeysID)

    final_vector = np.array(final_vector)
    final_vector = final_vector.reshape(1, 30, 6)

    predictions = model.predict(x=final_vector, verbose=1)
    print_predictions(predictions)


def print_predictions(predictions):
    global fail_count

    for prediction in predictions:
        print(prediction)
        ui.update_output_box(output_textbox2, prediction)
        if prediction[1] > 0.5:
            ui.update_status_label(output_label, "user", "green")
            fail_count = 0
        else:
            ui.update_status_label(output_label, "not user", "red")
            if switch.get() == 1 and fail_count == 10:
                turn_off()
                fail_count = 0
            elif switch.get() == 1:
                fail_count += 1


def turn_off():
    os.system("rundll32.exe user32.dll,LockWorkStation")  # windows
    os.system("/System/Library/CoreServices/Menu\ Extras/User.menu/Contents/Resources/CGSession -suspend")  # mac


def get_final_vector(down_down_chunk, dwell_chunk, position_number, up_down_chunk, virtual_keys_id):
    final_vector = []
    index = position_number - 31
    for i in range(len(dwell_chunk) - 1):
        vector_to_append = (
            virtual_keys_id[i + index], virtual_keys_id[i + 1 + index], dwell_chunk[i], dwell_chunk[i + 1],
            down_down_chunk[i],
            up_down_chunk[i])
        final_vector.append(vector_to_append)
    return final_vector


def predictions_thread():
    while True:
        sem.acquire()
        mutex.acquire()
        x = q.popleft()
        mutex.release()
        predict_and_print(x)


def get_model():
    global model
    try:
        model = keras.models.load_model(f'saved_models/{username}/model.h5')
    except OSError:
        print("No such user in the systems!")
        quit()


def main():
    global output_label, output_textbox2, switch, username
    threading.Thread(target=predictions_thread).start()
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        root, output_label, output_textbox2, switch, username = ui.init()
        get_model()
        root.mainloop()
        listener.start()


if __name__ == "__main__":
    main()
