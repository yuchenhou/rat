import datetime
import numpy as np
from sklearn import metrics, cross_validation
import math
import tensorflow as tf
from tensorflow.contrib import learn
from rat.clean import get_segments, get_indices

SEGMENT_LENGTH = 500


def char_cnn_model(x, y):
    n_filters = 10
    alphabet_size = 256
    y = tf.one_hot(y, 2, 1, 0)
    layer1 = tf.reshape(learn.ops.one_hot_matrix(x, alphabet_size), [-1, SEGMENT_LENGTH, alphabet_size, 1])
    layer2 = tf.nn.relu(learn.ops.conv2d(layer1, n_filters, [20, alphabet_size], padding='VALID'))
    layer3 = tf.nn.max_pool(layer2, ksize=[1, 4, 1, 1], strides=[1, 2, 1, 1], padding='SAME')
    layer3 = tf.transpose(layer3, [0, 1, 3, 2])
    layer4 = learn.ops.conv2d(layer3, n_filters, [20, n_filters], padding='VALID')
    layer5 = tf.squeeze(tf.reduce_max(layer4, 1), squeeze_dims=[1])
    prediction, loss = learn.models.logistic_regression(layer5, y)
    train_op = tf.contrib.layers.optimize_loss(loss, tf.contrib.framework.get_global_step(), 0.1, 'SGD')
    return {'class': tf.argmax(prediction, 1), 'prob': prediction}, loss, train_op


def main():
    begin = datetime.datetime.now()
    batch_size = 8
    indices = get_indices('DMRs-germ-chr20.csv', SEGMENT_LENGTH, None)
    segments = get_segments('rat-chr20.fa', indices, SEGMENT_LENGTH)
    x = segments['sequence']
    y = segments['label']
    positive_samples = segments[segments['label'] == 1]
    negative_samples = segments[segments['label'] == 0].sample(len(positive_samples))
    samples_train = positive_samples.append(negative_samples, ignore_index=True)
    x_train = samples_train['sequence']
    y_train = samples_train['label']
    processor = learn.preprocessing.ByteProcessor(SEGMENT_LENGTH)
    x = np.array(list(processor.fit_transform(x)))
    x_train = np.array(list(processor.fit_transform(x_train)))
    n_steps = len(x_train) // batch_size
    # x_train, x_validation, y_train, y_validation = cross_validation.train_test_split(x, y, test_size=0.2)
    # validation_monitor = learn.monitors.ValidationMonitor(x_validation, y_validation, every_n_steps=n_steps,
    #                                                       early_stopping_rounds=1)
    classifier = learn.Estimator(model_fn=char_cnn_model)
    # classifier.fit(x_train, y_train, steps=math.inf, batch_size=batch_size, monitors=[validation_monitor])
    print(datetime.datetime.now() - begin)
    classifier.fit(x_train, y_train, steps=1 * n_steps, batch_size=batch_size)
    print(datetime.datetime.now() - begin)
    y_predicted = [p['class'] for p in classifier.predict(x, batch_size=batch_size, as_iterable=True)]
    y_train_predicted = [p['class'] for p in classifier.predict(x_train, batch_size=batch_size, as_iterable=True)]
    # print('Accuracy: {0:f}'.format(metrics.accuracy_score(y, y_predicted)))
    print(metrics.confusion_matrix(y, y_predicted))
    print(metrics.confusion_matrix(y_train, y_train_predicted))
    print(datetime.datetime.now() - begin)


if __name__ == '__main__':
    main()
