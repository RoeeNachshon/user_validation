from sklearn.utils import shuffle
import numpy as np
import os
import ast
import h5py
import random
from numpy import ndarray

PATH = "keystrokes_data/"
WINDOW_SIZE = 30
train_labels = np.array([])
sliding_window_data = np.array([])


def create_train_file(username):
    _normalize_main_user(username)

    _normalize_other_users()

    _save_normalized_data(username)
    print("DONE!")


def _normalize_main_user(username):
    user_data = np.array([])
    if os.path.exists(PATH + username):
        for filename in os.listdir(PATH + username):
            print(filename)
            filepath = os.path.join(PATH + username, filename)
            new_data = np.array(_get_file_data_type(filepath))
            user_data = np.append(user_data, new_data)

        _finish_norm_main_user(user_data)
    else:
        print("No such user files!")
        quit()


def _finish_norm_main_user(user_data: ndarray):
    user_data = user_data.reshape(int(user_data.shape[0] / 6), 6)
    user_data = _normalize_keys_values(user_data)
    _append_to_sw(user_data)
    _append_to_labels(1, user_data)


def _normalize_other_users():
    users_paths = _get_others_data_file_path()
    for path in users_paths:
        _norm_other_users_data(path)


def _save_normalized_data(username):
    global train_labels
    global sliding_window_data

    train_labels = train_labels.reshape(int(train_labels.shape[0]), 1)
    sliding_window_data = sliding_window_data.reshape(int(train_labels.shape[0]), WINDOW_SIZE, 6)
    sliding_window_data, train_labels = shuffle(sliding_window_data, train_labels)
    with h5py.File(f'train_data/{username}/train_data.h5', 'w') as hdf:
        hdf.create_dataset('train_data', data=sliding_window_data)
        hdf.create_dataset('train_labels', data=train_labels)
    with open("names_for_system.txt", "a") as file:
        file.write("\n" + username)


def _norm_other_users_data(folder_path: str):
    for filename in os.listdir(folder_path):
        print(filename)
        _norm_others_values(filename, folder_path)


def _get_file_data_type(filepath: str) -> ndarray:
    with open(filepath, 'r') as file:
        file_data = file.readlines()
        for line in file_data:
            line = _remove_line_brackets(line)
            file_data = ast.literal_eval(line)
    return file_data


def _remove_line_brackets(file_line: str) -> str:
    file_line.replace('[', "")
    file_line.replace(']', "")
    return file_line


def _norm_others_values(filename: str, folder_path: str):
    filepath = os.path.join(folder_path, filename)
    new_train_data = np.array(_get_file_data_type(filepath))
    new_train_data = _normalize_keys_values(new_train_data)
    new_train_data = _cut_data_80_values(new_train_data)
    _append_to_sw(new_train_data)
    _append_to_labels(0, new_train_data)


def _append_to_labels(user_type: int, data: ndarray):
    global train_labels

    label = np.empty(int(data.shape[0] - WINDOW_SIZE))
    label.fill(user_type)
    train_labels = np.append(train_labels, label)


def _append_to_sw(data: ndarray):
    global sliding_window_data

    for line in range(data.shape[0] - WINDOW_SIZE):
        sliding_window_data = np.append(sliding_window_data, data[line:line + WINDOW_SIZE])


def _cut_data_80_values(data: ndarray) -> ndarray:
    cut_value = random.randint(0, data.shape[0] - 81)
    return data[cut_value:cut_value + 80]


def _normalize_keys_values(data: ndarray) -> ndarray:
    for j in range(0, len(data)):
        data[j][0] = data[j][0] / 254
        data[j][1] = data[j][1] / 254
    return data


def _get_others_data_file_path() -> list:
    result = []
    for filename in os.listdir(PATH):
        if filename.find("user") != -1:
            filepath = os.path.join(PATH, filename)
            result.append(filepath)
    return result
