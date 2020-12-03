from droughtwatch.params import IMG_DIM, NUM_CLASSES, SIZE, SIZE_TRAIN, SIZE_VAL, TOTAL_TRAIN, TOTAL_VAL
import os
import numpy as np
import tensorflow.compat.v1 as tf
import argparse
import math
import numpy as np
import os
from tensorflow.keras import optimizers
from tensorflow.keras import layers, initializers
from tensorflow.keras import models
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from google.cloud import storage

#from keras.models import model_from_json

features = {
  'B1': tf.io.FixedLenFeature([], tf.string),
  'B2': tf.io.FixedLenFeature([], tf.string),
  'B3': tf.io.FixedLenFeature([], tf.string),
  'B4': tf.io.FixedLenFeature([], tf.string),
  'B5': tf.io.FixedLenFeature([], tf.string),
  'B6': tf.io.FixedLenFeature([], tf.string),
  'B7': tf.io.FixedLenFeature([], tf.string),
  'B8': tf.io.FixedLenFeature([], tf.string),
  'B9': tf.io.FixedLenFeature([], tf.string),
  'B10': tf.io.FixedLenFeature([], tf.string),
  'B11': tf.io.FixedLenFeature([], tf.string),
  'label': tf.io.FixedLenFeature([], tf.int64),
}

BUCKET_NAME = 'tfrecords_data'
BUCKET_DATA_PATH = 'data'

# B1  30 meters   0.43 - 0.45 µm  Coastal aerosol
# B2  30 meters   0.45 - 0.51 µm  Blue
# B3  30 meters   0.53 - 0.59 µm  Green
# B4  30 meters   0.64 - 0.67 µm  Red
# B5  30 meters   0.85 - 0.88 µm  Near infrared
# B6  30 meters   1.57 - 1.65 µm  Shortwave infrared 1
# B7  30 meters   2.11 - 2.29 µm  Shortwave infrared 2
# B8  15 meters   0.52 - 0.90 µm  Band 8 Panchromatic
# B9  15 meters   1.36 - 1.38 µm  Cirrus
# B10 30 meters   10.60 - 11.19 µm Thermal infrared 1, resampled from 100m to 30m
# B11 30 meters   11.50 - 12.51 µm Thermal infrared 2, resampled from 100m to 30m


def load_data_gcp():
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    train = file_list_from_gcp("train", bucket)
    val = file_list_from_gcp("val", bucket)
    return train, val

def file_list_from_gcp(folder, bucket):
    filelist = []
    os.mkdir(f'data/{folder}')
    client = storage.Client()
    for filename in list(client.list_blobs(bucket)):
      if str(filename).startswith("<Blob: tfrecords_data, data/"+folder+'/part-'):
        name = str(filename)
        name = name[:-19]
        name = name.replace('<Blob: tfrecords_data, ', '')
        filelist.append(name)
    file_obj_list = []
    for items in filelist:
      blob = bucket.get_blob(items) 
      blob = bucket.blob(items)
      blobstring = blob.download_as_string()
      with open("testfile", "wb") as file_obj:
          file_obj_list.append(blob.download_to_file(file_obj))
    return file_obj_list


def parse_tfrecords(filelist, batch_size, buffer_size, include_viz=False):
  # try a subset of possible bands
    def _parse_(serialized_example, keylist=['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8']):
        example = tf.io.parse_single_example(serialized_example, features)

        def getband(example_key):
            img = tf.io.decode_raw(example_key, tf.uint8)
            return tf.reshape(img[:IMG_DIM**2], shape=(IMG_DIM, IMG_DIM, 1))

        bandlist = [getband(example[key]) for key in keylist]
        # combine bands into tensor
        image = tf.concat(bandlist, -1)

        # one-hot encode ground truth labels
        label = tf.cast(example['label'], tf.int32)
        label = tf.one_hot(label, NUM_CLASSES)

        return {'image': image}, label

    tfrecord_dataset = tf.data.TFRecordDataset(filelist)
    tfrecord_dataset = tfrecord_dataset.map(lambda x:_parse_(x)).shuffle(buffer_size).repeat(-1).batch(batch_size)
    tfrecord_iterator = tfrecord_dataset.make_one_shot_iterator()
    image, label = tfrecord_iterator.get_next()
    return image, label

os.mkdir('test_folder/test_folder2')
#client = storage.Client()
#bucket = client.get_bucket(BUCKET_NAME)
#train = file_list_from_gcp("train", bucket)
#val = file_list_from_gcp("val", bucket)

    #training_files = dirlist('data/train/')

    #train = file_list_from_folder("train", "data/")
    #val = file_list_from_folder("val", 'data/')


      # Merge folders containing parts of the dataset into one folder
      #dirlist = lambda di: [os.path.join(di, file)\
      #for file in os.listdir(di) if 'part-' in file]