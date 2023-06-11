from sklearn.utils import shuffle
import numpy as np
import os
import ast
import h5py
import random

PATH = "keystrokes_data/"
WINDOW_SIZE = 30
train_labels = np.array([])
sliding_window_data = np.array([])


def create_train_file(username: str):
    """
    Creates the h5 file for the model to work with from the txt files.
    :param username: A string of the user name, to create the files names.
    :return: Saves the h5 file.
    """
    _normalize_main_user(username)

    _normalize_other_users()

    _save_normalized_data(username)
    print("DONE!")


def _normalize_main_user(username: str):
    """
    Normalize the main user txt file.
    :param username: A string of the user name
    :return: None
    """
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


def _finish_norm_main_user(user_data: np.ndarray):
    """
    Finishing the normalization of the main user.
    :param user_data: An np array of the user's data.
    :return: None
    """
    user_data = user_data.reshape(int(user_data.shape[0] / 6), 6)
    user_data = _normalize_keys_values(user_data)
    _append_to_sw(user_data)
    _append_to_labels(1, user_data)


def _normalize_other_users():
    """
    Extracts the folder paths for the other's data
    :return: None
    """
    users_paths = _get_others_data_file_path()
    for path in users_paths:
        _norm_other_users_data(path)


def _save_normalized_data(username: str):
    """
    Saves the end product of the normalization process.
    :param username: A string of the user name
    :return: Saves as an h5 file, with the username's name.
    """
    global train_labels
    global sliding_window_data

    train_labels = train_labels.reshape(int(train_labels.shape[0]), 1)
    sliding_window_data = sliding_window_data.reshape(int(train_labels.shape[0]), WINDOW_SIZE, 6)
    sliding_window_data, train_labels = shuffle(sliding_window_data, train_labels)
    directory = f"train_data/{username}"
    os.makedirs(directory, exist_ok=True)
    with h5py.File(f'{directory}/data.h5', 'w') as hdf:
        hdf.create_dataset('train_data', data=sliding_window_data)
        hdf.create_dataset('train_labels', data=train_labels)


def _norm_other_users_data(folder_path: str):
    """
    Extracts the file paths for the other's data
    :param folder_path: A path for the folder of the other users DB
    :return: None
    """
    for filename in os.listdir(folder_path):
        print(filename)
        _norm_others_values(filename, folder_path)


def _get_file_data_type(filepath: str) -> np.ndarray:
    """
    Estimates the type of the txt file data
    :param filepath: The txt file path to interpret.
    :return: The file data as a value
    """
    with open(filepath, 'r') as file:
        file_data = file.readlines()
        for line in file_data:
            line = _remove_line_brackets(line)
            file_data = ast.literal_eval(line)
    return file_data


def _remove_line_brackets(file_line: str) -> str:
    """
    Removes brackets
    :param file_line: A line from a file's data
    :return: The file data without brackets
    """
    file_line.replace('[', "")
    file_line.replace(']', "")
    return file_line


def _norm_others_values(filename: str, folder_path: str):
    """
    Normalize other users' values.
    :param filename: The file name to norm
    :param folder_path: The folder where the file is
    :return: None
    """
    filepath = os.path.join(folder_path, filename)
    new_train_data = np.array(_get_file_data_type(filepath))
    new_train_data = _normalize_keys_values(new_train_data)
    new_train_data = _cut_data_80_values(new_train_data)
    _append_to_sw(new_train_data)
    _append_to_labels(0, new_train_data)


def _append_to_labels(user_type: int, data: np.ndarray):
    """
    Appends data to the labels foe the data
    :param user_type: 1 for main 0 for others
    :param data: the data to relate the labels to.
    :return: None
    """
    global train_labels

    label = np.empty(int(data.shape[0] - WINDOW_SIZE))
    label.fill(user_type)
    train_labels = np.append(train_labels, label)


def _append_to_sw(data: np.ndarray):
    """
    Append the data to the sliding windows.
    :param data: The data to append
    :return: None
    """
    global sliding_window_data

    for line in range(data.shape[0] - WINDOW_SIZE):
        sliding_window_data = np.append(sliding_window_data, data[line:line + WINDOW_SIZE])


def _cut_data_80_values(data: np.ndarray) -> np.ndarray:
    """
    Cuts the data and takes 80 lines of it
    :param data: The data to cut
    :return: 80 lines of the data
    """
    cut_value = random.randint(0, data.shape[0] - 81)
    return data[cut_value:cut_value + 80]


def _normalize_keys_values(data: np.ndarray) -> np.ndarray:
    """
    Normalize the vk of the keys.
    :param data: The data to norm
    :return: The normalized data
    """
    for j in range(0, len(data)):
        data[j][0] = data[j][0] / 254
        data[j][1] = data[j][1] / 254
    return data


def _get_others_data_file_path() -> list:
    """
    Gets the file path for the DB data
    :return: a list of paths.
    """
    result = []
    for filename in os.listdir(PATH):
        if filename.find("user") != -1:
            filepath = os.path.join(PATH, filename)
            result.append(filepath)
    return result
