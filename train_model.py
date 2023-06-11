import math
import h5py
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.callbacks import LearningRateScheduler
from numpy import ndarray
from tensorflow import keras
import os

BATCH_SIZE = 32
EPOCHS = 150
INPUT_SHAPE = (30, 6)


def _get_data_from_files(username: str):
    """
    Extracts the data from the file
    :param username: A string of the user name
    :return: Tuple of the data and labels
    """
    with h5py.File(f'train_data/{username}/data.h5', 'r') as hdf:
        data = hdf.get('train_data')
        train_data = np.array(data)
        data = hdf.get('train_labels')
        train_labels = np.array(data)
    return train_data, train_labels


def _sort_data_by_label(is_user: bool, train_data: ndarray, train_labels: ndarray) -> tuple:
    """
    Sorts the data by the labels and the user type.
    :param is_user: 1 if user 0 if not
    :param train_data: The data to sort
    :param train_labels: The data labels
    :return: Tuple of the sorted data and labels
    """
    num = int(is_user)
    val_data = np.array([])
    for i in range(1000):
        if train_labels[i] == num:
            val_data = np.append(val_data, train_data[i])

    val_label = np.empty(int(val_data.shape[0] / (INPUT_SHAPE[0] * 6)))
    val_label.fill(num)
    return val_label, val_data


def _get_data(username: str) -> tuple:
    """
    Gets the sorted data from the files
    :param username: A string of the user name
    :return: a list of val1_labels, val1_data, val0_labels, val0_data, train_data, train_labels
    """
    train_data, train_labels = _get_data_from_files(username)
    val1_labels, val1_data = _sort_data_by_label(True, train_data, train_labels)
    val0_labels, val0_data = _sort_data_by_label(False, train_data, train_labels)
    val1_data = val1_data.reshape(int(val1_labels.shape[0]), INPUT_SHAPE[0], 6)
    val0_data = val0_data.reshape(int(val0_labels.shape[0]), INPUT_SHAPE[0], 6)
    return val1_labels, val1_data, val0_labels, val0_data, train_data, train_labels


def _train_model(train_data: ndarray, train_labels: ndarray) -> keras.models.Sequential:
    """
    Trains the model with the labels and the data
    :param train_data: The data to train it with
    :param train_labels: The data labels
    :return: The trained model
    """
    model = _create_model()
    print(model.summary())
    train_data = train_data[1000:]
    train_labels = train_labels[1000:]
    lrate = LearningRateScheduler(_step_decay)
    callbacks_list = [lrate]
    with tf.device('/device:GPU:0'):
        model.fit(train_data, train_labels, batch_size=BATCH_SIZE, validation_split=0.1, callbacks=callbacks_list,
                  epochs=EPOCHS, shuffle=True)
    return model


def _step_decay(epoch) -> float:
    """
    Gets the decay rate of the model training.
    :param epoch: A complete iteration of the entire training dataset
    :return: The rate
    """
    initial_lrate = 0.0001
    drop = 0.1
    epochs_drop = 100.0
    lrate = initial_lrate * math.pow(drop, math.floor((1 + epoch) / epochs_drop))
    return lrate


def _compile_model(model: keras.models.Sequential) -> keras.models.Sequential:
    """
    Compiles the model
    :param model: The model to compile
    :return: The compiled model
    """
    loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    optimizer = keras.optimizers.Adam(learning_rate=0.0)
    metrics = ["accuracy"]
    model.compile(loss=loss, optimizer=optimizer, metrics=metrics)
    return model


def _create_model() -> keras.models.Sequential:
    """
    Creates the model
    :return: The new model
    """
    model = keras.models.Sequential()
    model.add(layers.Conv1D(32, 2, activation='relu', input_shape=INPUT_SHAPE))
    model.add(tf.keras.layers.LSTM(32, return_sequences=True))
    model.add(layers.Dropout(0.5))
    model.add(tf.keras.layers.LSTM(32, return_sequences=True))
    model.add(layers.Dropout(0.5))
    model.add(layers.Flatten())
    model.add(layers.Dense(2, activation='softmax'))
    return _compile_model(model)


def _evaluate_model(model: keras.models.Sequential, val_data: ndarray, val_labels: ndarray):
    """
    Evaluates the model
    :param model: The model to evaluate
    :param val_data: The data to evaluate the model with
    :param val_labels: The data labels
    :return: None
    """
    model.evaluate(val_data, val_labels, batch_size=BATCH_SIZE, verbose=1)
    probability_model = keras.models.Sequential([model, keras.layers.Softmax()])
    predictions = probability_model(val_data)
    pre0 = predictions[0]
    print(pre0)
    label0 = np.argmax(pre0)
    print(label0)


def init_model(username: str):
    """
    Creates the model ans initiates the learn process.
    :param username: A string of the user name
    :return: Saves the model as h5 file
    """
    val1_labels, val1_data, val0_labels, val0_data, train_data, train_labels = _get_data(username)
    model = _train_model(train_data, train_labels)
    # evaluate_model(model, val1_data, val1_labels)
    # evaluate_model(model, val0_data, val0_labels)
    directory = f"saved_models/{username}"
    os.makedirs(directory, exist_ok=True)
    model.save(f"{directory}/model.h5")
    print("DONE!")
