# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import tensorflow as tf
import utils

import tensorflow.contrib.slim as slim

def xavier_init(size):
	in_dim = size[0]
	xavier_stddev = 1. / tf.sqrt(in_dim / 2.)
	return tf.random_normal(shape=size, stddev=xavier_stddev)

"""Contains the base class for models."""
class BaseModel(object):
	"""Inherit from this class when implementing new models."""

	def create_model(self, **unused_params):
		"""Define variables of the model."""
		raise NotImplementedError()

	def run_model(self, unused_model_input, **unused_params):
		"""Run model with given input."""
		raise NotImplementedError()

	def get_variables(self):
		"""Return all variables used by the model for training."""
		raise NotImplementedError()

class SampleGenerator(BaseModel):
	def __init__(self):
		self.noise_input_size = 100

	def create_model(self, output_size, **unused_params):
		h1_size = 256
		h2_size = 256
		self.G_W1 = tf.Variable(xavier_init([self.noise_input_size, h1_size]), name='g/w1')
		self.G_b1 = tf.Variable(tf.zeros(shape=[h1_size]), name='g/b1')

		self.G_W2 = tf.Variable(xavier_init([h1_size, h2_size]), name='g/w2')
		self.G_b2 = tf.Variable(tf.zeros(shape=[h2_size]), name='g/b2')

		self.G_W3 = tf.Variable(xavier_init([h2_size, output_size]), name='g/w3')
		self.G_b3 = tf.Variable(tf.zeros(shape=[output_size]), name='g/b3')

	def run_model(self, model_input, is_training=True, **unused_params):
		net = model_input

		net = tf.contrib.layers.batch_norm(net, is_training=is_training)
		net = slim.dropout(net, 0.75, is_training=is_training, scope='w/dropout_fc1')
		net = tf.nn.relu(tf.matmul(model_input, self.G_W1) + self.G_b1)
		
		net = tf.contrib.layers.batch_norm(net, is_training=is_training)
		net = slim.dropout(net, 0.75, is_training=is_training, scope='w/dropout_fc2')
		net = tf.nn.relu(tf.matmul(net, self.G_W2) + self.G_b2)

		net = slim.dropout(net, 0.75, is_training=is_training, scope='w/dropout_fc3')
		output = tf.nn.sigmoid(tf.matmul(net, self.G_W3) + self.G_b3)
		return {"output": output}

	def get_variables(self):
		return [self.G_W1, self.G_W2, self.G_b1, self.G_b2, self.G_W3, self.G_b3]

class SampleDiscriminator(BaseModel):
	def create_model(self, input_size, **unused_params):
		h1_size = 128
		self.D_W_conv11 = tf.Variable(xavier_init([3, 3, 1, 10]), name='D_W_conv11')
		self.D_W_conv12 = tf.Variable(xavier_init([3, 3, 10, 10]), name='D_W_conv12')
		
		self.D_W_conv21 = tf.Variable(xavier_init([3, 3, 10, 10]), name='D_W_conv21')
		self.D_W_conv22 = tf.Variable(xavier_init([3, 3, 10, 10]), name='D_W_conv22')

		self.D_W1 = tf.Variable(xavier_init([1690, h1_size]), name='d/w1')
		self.D_b1 = tf.Variable(tf.zeros(shape=[h1_size]), name='d/b1')

		self.D_W2 = tf.Variable(xavier_init([h1_size, 1]), name='d/w2')
		self.D_b2 = tf.Variable(tf.zeros(shape=[1]), name='d/b2')


	def run_model(self, model_input, is_training=True, **unused_params):
		net = model_input

		net = tf.reshape(model_input, shape=[-1, 50, 50, 1])
		net = tf.nn.conv2d(net, self.D_W_conv11, strides=[1, 1, 1, 1], padding='SAME')
		net = tf.nn.relu(net)
		net = tf.nn.conv2d(net, self.D_W_conv12, strides=[1, 1, 1, 1], padding='SAME')
		net = tf.nn.relu(net)
		net = tf.nn.max_pool(net, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

		net = tf.nn.conv2d(net, self.D_W_conv21, strides=[1, 1, 1, 1], padding='SAME')
		net = tf.nn.relu(net)
		net = tf.nn.conv2d(net, self.D_W_conv22, strides=[1, 1, 1, 1], padding='SAME')
		net = tf.nn.relu(net)
		net = tf.nn.max_pool(net, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
		
		print(net.get_shape())
		net = tf.reshape(net, [-1, 1690])
		print(net.get_shape())


		net = slim.dropout(net, 0.75, is_training=is_training, scope='d/dropout_fc1')
		net = tf.nn.relu(tf.matmul(net, self.D_W1) + self.D_b1)

		net = slim.dropout(net, 0.75, is_training=is_training, scope='d/dropout_fc2')
		logits = tf.matmul(net, self.D_W2) + self.D_b2
		predictions = tf.nn.sigmoid(logits)
		return {"logits": logits, "predictions": predictions}

	def get_variables(self):
		return [self.D_W1, self.D_W2, self.D_b1, self.D_b2, self.D_W_conv11, self.D_W_conv12]