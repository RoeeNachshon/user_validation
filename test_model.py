from tensorflow import keras
import convert_to_windows
import user_interface as ui
import tkinter as tk
import numpy as np
from pynput import keyboard
from time import time
import sys
import threading
import collections
import os
import platform

q = collections.deque()  # queue for the windows prediction calculation
dwell = []  # The list of key dwell times
startTimes = np.zeros(254)  # Saves the time in witch a key was pressed
startTyping = 0  # start time
DownDown = []  # DownDown array
virtualKeysID = []  # key ID array
last_key_press_time = 0  # a variable used to calculate the duration between keystrokes
count = 0  # number of tuples inserted
model: keras.models.Sequential
sem = threading.Semaphore(0)  # semaphore to count the number of windows in the queue
mutex = threading.Semaphore(1)  # semaphore to protect the insert and pop operations on the queue
output_label: tk.Label
output_textbox2: tk.Text
window: tk.Tk
switch: tk.IntVar
username: str
should_record: str
fail_count = 0


def _on_press(key):
    """
    On press function
    :param key: The key that was pressed
    :return: None
    """
    global last_key_press_time
    global startTyping
    global count

    current_time = time()

    _is_first_typed(current_time)

    last_key_press_time = current_time
    vk = _get_virtual_key(key)
    startTimes[vk] = current_time
    virtualKeysID.append(vk / 254)
    sys.stdout.flush()


def _is_first_typed(current_time: float):
    """
    Record the time the first key was pressed
    :param current_time: The time of the event
    :return: None
    """
    global startTyping
    if startTyping == 0:
        startTyping = current_time
    if last_key_press_time != 0:
        DownDown.append(current_time - last_key_press_time)


def _on_release(key) -> bool:
    """
    On release function
    :param key: The key that was release
    :return: False if the key is escape
    """
    global count

    _append_times(key)

    if count > 30:
        _append_to_queue(count)

    count += 1

    if key == keyboard.Key.esc:
        return False


def _append_times(key):
    """
    Append the event times to the corresponding lists
    :param key: The key that was triggered
    :return: None
    """
    current_time = time()
    vk = _get_virtual_key(key)
    start = startTimes[vk]
    startTimes[vk] = 0
    dwell.append(current_time - start)


def _append_to_queue(num: int):
    """
    Appends to queue for the sliding window size
    :param num: The num to append
    :return: None
    """
    mutex.acquire()
    q.append(num)
    mutex.release()
    sem.release()


def _get_virtual_key(key) -> int:
    """
    Gets the correct windows virtual key code for the key
    :param key: The key to get its vk
    :return: The windows vk of the key
    """
    key_value = key.vk if hasattr(key, 'vk') else key.value.vk
    if platform.system() == "Darwin":
        try:
            key_value = convert_to_windows.macToPCDict[key_value]
        except KeyError:
            key_value = -1
    return key_value


def _predict_and_print(position_number: int):
    """
    Calculates the vector and predicts
    :param position_number: The position of the window
    :return: None
    """
    global dwell
    global DownDown
    global virtualKeysID
    global model

    dwell_chunk = np.array(dwell[position_number - 31:position_number])
    down_down_chunk = np.array(DownDown[position_number - 31:position_number])
    up_down_chunk = down_down_chunk - dwell_chunk

    final_vector = _get_final_vector(down_down_chunk, dwell_chunk, position_number, up_down_chunk, virtualKeysID)

    final_vector = np.array(final_vector)
    final_vector = final_vector.reshape(1, 30, 6)
    if should_record == "No":
        predictions = model.predict(x=final_vector, verbose=1)
        _print_predictions(predictions)


def _print_predictions(predictions: list):
    """
    Prints the predictions on the screen
    :param predictions: The prediction to print
    :return: None
    """
    global fail_count

    for prediction in predictions:
        print(prediction)
        ui.update_output_box(output_textbox2, prediction)
        _check_if_to_lock(prediction)


def _check_if_to_lock(prediction):
    """
    Checks if to lock the computer after 10 false predictions
    :param prediction: The predictions
    :return: None
    """
    global fail_count
    if prediction[1] > 0.5:
        ui.update_status_label(output_label, "user", "green")
        fail_count = 0
    else:
        ui.update_status_label(output_label, "not user", "red")
        if switch.get() == 1 and fail_count == 15:
            _turn_off()
            fail_count = 0
        elif switch.get() == 1:
            fail_count += 1


def _turn_off():
    """
    Turns off the computer
    :return: None
    """
    os.system("rundll32.exe user32.dll,LockWorkStation")  # windows
    os.system("osascript -e 'tell application \"System Events\" to keystroke \"q\" using {control down, command down}'")


def _get_final_vector(down_down_chunk: np.ndarray, dwell_chunk: np.ndarray, position_number: int,
                      up_down_chunk: np.ndarray, virtual_keys_id: list) -> list:
    """
    Calculates the final vector to predict with
    :param down_down_chunk: Keyboard timing list
    :param dwell_chunk: Keyboard timing list
    :param position_number: The position in the sliding windows
    :param up_down_chunk: Keyboard timing list
    :param virtual_keys_id: virtual key codes list
    :return: list of the final vector
    """
    final_vector = []
    index = position_number - 31
    for i in range(len(dwell_chunk) - 1):
        vector_to_append = (
            virtual_keys_id[i + index], virtual_keys_id[i + 1 + index], dwell_chunk[i], dwell_chunk[i + 1],
            down_down_chunk[i],
            up_down_chunk[i])
        final_vector.append(vector_to_append)
    if should_record == "Yes":
        _make_new_user_files(final_vector[-1])
    return final_vector


def _make_new_user_files(final_vector: tuple):
    """
    Makes new user txt files
    :param final_vector: the data to append
    :return: writes in the files
    """
    directory = f"keystrokes_data/{username}"
    if os.path.exists(directory):
        new_data = _arrange_new_data(final_vector)
        new_data = _get_data_to_write(directory, new_data)
        _write_in_file(directory, str(new_data))
    else:
        os.makedirs(directory, exist_ok=True)
        new_data = "["
        new_data += str(_arrange_new_data(final_vector))
        new_data += "]"
        _write_in_file(directory, str(new_data))

    ui.update_output_box(output_textbox2, "put")


def _arrange_new_data(new_data: tuple) -> tuple:
    """
    Arranges new data to match the DB format.
    :param new_data: The data to arrange
    :return: The arranged data
    """
    result = [int(new_data[0] * 254), int(new_data[1] * 254)]
    for i in range(2, len(new_data)):
        result.append(new_data[i])
    return tuple(result)


def _get_data_to_write(directory: str, final_vector: tuple) -> str:  # [(1,3,,3),()...]
    """
    If the file existed, combines the old data with the new one.
    :param directory: The file's path
    :param final_vector: The data to append
    :return: The new combined data
    """
    with open(f"{directory}/data.txt", "r") as file:
        old_data = file.read().split("]")
        new_data = old_data[0]
        new_data += ", "
        new_data += (str(final_vector))
        new_data += "]"
    return new_data


def _write_in_file(directory: str, new_data: str):
    """
    Writes in the given file.
    :param directory: The file to write
    :param new_data: The mode of the method
    :return: None
    """
    with open(f"{directory}/data.txt", "w") as file:
        file.write(new_data)


def _predictions_thread():
    """
    The prediction thread handling.
    :return: None
    """
    while True:
        sem.acquire()
        mutex.acquire()
        x = q.popleft()
        mutex.release()
        _predict_and_print(x)


def _get_model():
    """
    Gets the model by the username
    :return: None
    """
    global model
    if should_record == "No":
        if os.path.exists(f'saved_models/{username}/model.h5'):
            model = keras.models.load_model(f'saved_models/{username}/model.h5')
        else:
            print("No such model in the systems!")
            quit()


def main():
    """
    Test the system. it run the UI, and if needed creates train files and runs the train model
    :return: None
    """
    global output_label, output_textbox2, switch, username, should_record
    threading.Thread(target=_predictions_thread).start()
    with keyboard.Listener(on_press=_on_press, on_release=_on_release) as listener:
        root, output_label, output_textbox2, switch, username, should_record = ui.init()
        _get_model()
        root.mainloop()
        listener.start()


if __name__ == "__main__":
    main()
