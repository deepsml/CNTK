# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

# This example shows how to train a very basic CNTK model for logistic regression.
# The task is to classify a 2-dimensional vector as belong to one of two classes.
# The data is artificially created. Each class' data follows a normal distribution.

# Import the relevant components
from __future__ import print_function
import cntk
import numpy as np

# Define the task
input_dim = 2    # classify 2-dimensional data
num_classes = 2  # into one of two classes

num_samples_to_train = 20000
num_samples_to_test  = 1000

# Generate our synthetic data
#  X[sample_size,input_dim] - our input data
#  Y[sample_size]           - labels (0 or 1), in one-hot representation
sample_size = 32
np.random.seed(0)
def generate_synthetic_data(N):
    # labels
    Y = np.random.randint(size=N, low=0, high=num_classes)
    # data
    X = (np.random.randn(N, input_dim)+3) * (Y[:,None]+1)
    # our model expects float32 features, and cross-entropy expects one-hot encoded labels
    from scipy import sparse
    Y = sparse.csr_matrix((np.ones(N,np.float32), (range(N), Y)), shape=(N, num_classes))
    X = X.astype(np.float32)
    return X, Y
X_train, Y_train = generate_synthetic_data(num_samples_to_train)
X_test,  Y_test  = generate_synthetic_data(num_samples_to_test)

# Define the CNTK model. A model is defined as a function that maps
# input data to some form of predictions, in our case 2-dimensional
# input vectors to a 2-dimensional vector of scores.
# This simple logistic-regression model just uses a linear transform,
# which corresponds to a Dense layer without activation function.
# A Dense layer implements the formula y = x @ W + b, where W and b
# are learnable model parameters.
model = cntk.layers.Dense(num_classes, activation=None)

# Define the CNTK criterion function. A criterion function maps
# (input vectors, labels) to a loss function and an optional additional
# metric. The loss function is used to train the model parameters.
# We use cross entropy as a loss function.
# We use CNTK @Signature to declare the input types at this point.
# The cross-entropy formula requires the labels to be in one-hot format.
@cntk.FunctionWithSignature(cntk.layers.Tensor[input_dim], cntk.layers.SparseTensor[num_classes])
def criterion(data, label_one_hot):
    z = model(data)  # apply model. Computes a non-normalized log probability for every output class.
    loss   = cntk.cross_entropy_with_softmax(z, label_one_hot)
    metric = cntk.classification_error(z, label_one_hot)
    return loss, metric

# Instantiate the trainer object to drive the model training
learning_rate = 0.5
learner = cntk.sgd(model.parameters, cntk.learning_rate_schedule(learning_rate, cntk.UnitType.minibatch))

# Initialize the parameters for the trainer
minibatch_size = 25
training_progress_output_freq = 1250 // minibatch_size
progress_writer = cntk.logging.ProgressPrinter(training_progress_output_freq)

losses, metrics, num_samples = criterion.train((X_train, Y_train),
                                               minibatch_size=minibatch_size, max_samples=len(X_train), parameter_learners=[learner],
                                               progress_writers=[progress_writer], progress_frequency=len(X_train))

metric, num_samples = criterion.test((X_test, Y_test), minibatch_size=minibatch_size, progress_writers=[progress_writer])

# Checking prediction on one minibatch
# For evaluation, we map the output of the network between 0-1 and convert them into probabilities
# for the two classes. We use a softmax function to get the probabilities of each of the class.
@cntk.FunctionWithSignature(cntk.layers.Tensor[input_dim])
def get_probability(data):
    return cntk.softmax(model(data))

X_check,  Y_check = generate_synthetic_data(25) # a small batch of 25 examples
result = get_probability(X_check)

print("Label    :", [label.argmax() for label in Y_check])
print("Predicted:", [result[i,:].argmax() for i in range(len(result))])