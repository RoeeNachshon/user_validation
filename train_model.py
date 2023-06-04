import math
import h5py
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.callbacks import LearningRateScheduler
from numpy import ndarray
from tensorflow import keras

BATCH_SIZE = 32
EPOCHS = 150
INPUT_SHAPE = (30, 6)


def get_data_from_files(username):
    with h5py.File(f'train_data/{username}/train_data.h5', 'r') as hdf:
        data = hdf.get('train_data')
        train_data = np.array(data)
        data = hdf.get('train_labels')
        train_labels = np.array(data)
    return train_data, train_labels


def sort_data_by_label(is_user: bool, train_data: ndarray, train_labels: ndarray) -> tuple:
    num = int(is_user)
    val_data = np.array([])
    for i in range(1000):
        if train_labels[i] == num:
            val_data = np.append(val_data, train_data[i])

    val_label = np.empty(int(val_data.shape[0] / (INPUT_SHAPE[0] * 6)))
    val_label.fill(num)
    return val_label, val_data


def get_data(username):
    train_data, train_labels = get_data_from_files(username)
    val1_labels, val1_data = sort_data_by_label(True, train_data, train_labels)
    val0_labels, val0_data = sort_data_by_label(False, train_data, train_labels)
    val1_data = val1_data.reshape(int(val1_labels.shape[0]), INPUT_SHAPE[0], 6)
    val0_data = val0_data.reshape(int(val0_labels.shape[0]), INPUT_SHAPE[0], 6)
    return val1_labels, val1_data, val0_labels, val0_data, train_data, train_labels


def train_model(train_data: ndarray, train_labels: ndarray):
    model = create_model()
    print(model.summary())
    train_data = train_data[1000:]
    train_labels = train_labels[1000:]
    lrate = LearningRateScheduler(step_decay)
    callbacks_list = [lrate]
    with tf.device('/device:GPU:0'):
        model.fit(train_data, train_labels, batch_size=BATCH_SIZE, validation_split=0.1, callbacks=callbacks_list,
                  epochs=EPOCHS, shuffle=True)
    return model


def step_decay(epoch):
    initial_lrate = 0.0001
    drop = 0.1
    epochs_drop = 100.0
    lrate = initial_lrate * math.pow(drop, math.floor((1 + epoch) / epochs_drop))
    return lrate


def compile_model(model):
    loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    optimizer = keras.optimizers.Adam(learning_rate=0.0)
    metrics = ["accuracy"]
    model.compile(loss=loss, optimizer=optimizer, metrics=metrics)
    return model


def create_model():
    model = keras.models.Sequential()
    model.add(layers.Conv1D(32, 2, activation='relu', input_shape=INPUT_SHAPE))
    model.add(tf.keras.layers.LSTM(32, return_sequences=True))
    model.add(layers.Dropout(0.5))
    model.add(tf.keras.layers.LSTM(32, return_sequences=True))
    model.add(layers.Dropout(0.5))
    model.add(layers.Flatten())
    model.add(layers.Dense(2, activation='softmax'))
    return compile_model(model)


def evaluate_model(model, val_data: ndarray, val_labels: ndarray):
    model.evaluate(val_data, val_labels, batch_size=BATCH_SIZE, verbose=1)
    probability_model = keras.models.Sequential([model, keras.layers.Softmax()])
    predictions = probability_model(val_data)
    pre0 = predictions[0]
    print(pre0)
    label0 = np.argmax(pre0)
    print(label0)


def get_model(username):
    val1_labels, val1_data, val0_labels, val0_data, train_data, train_labels = get_data(username)
    model = train_model(train_data, train_labels)
    # evaluate_model(model, val1_data, val1_labels)
    # evaluate_model(model, val0_data, val0_labels)
    model.save(f"saved_models/{username}/model.h5")
    print("DONE!")

