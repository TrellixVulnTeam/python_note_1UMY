import keras
from keras import layers
from keras import backend as K
from keras.models import Model
import numpy as np
from keras.datasets import mnist
import matplotlib.pyplot as plt
from scipy.stats import norm

img_shape = (28,28,1)
batch_size = 16
latent_dim = 2

input_img = keras.Input(shape=img_shape)

x = layers.Conv2D(32,3,padding='same',activation='relu')(input_img)
x = layers.Conv2D(64,3,padding='same',activation='relu',strides=(2,2))(x)
x = layers.Conv2D(64,3,padding='same',activation='relu')(x)
x = layers.Conv2D(64,3,padding='same',activation='relu')(x)
shape_before_flattening = K.int_shape(x)

x = layers.Flatten()(x)
x = layers.Dense(32,activation='relu')(x)

z_mean = layers.Dense(latent_dim)(x)
z_log_var = layers.Dense(latent_dim)(x)

def samling(args):
    z_mean,z_log_var = args
    epsilon = K.random_normal(shape=(K.shape(z_mean)[0],latent_dim),mean=0,stddev=1.)
    return z_mean+K.exp(0.5*z_log_var)*epsilon
z = layers.Lambda(samling)([z_mean,z_log_var])

decoder_input = layers.Input(K.int_shape(z)[1:])

x = layers.Dense(np.prod(shape_before_flattening[1:]),activation='relu')(decoder_input)
x = layers.Reshape(shape_before_flattening[1:])(x)
x = layers.Conv2DTranspose(32,3,padding='same',activation='relu',strides=(2,2))(x)
decoder = Model(decoder_input,x)
z_decoded = decoder(z)


class CusstomVariationalLayer(keras.layers.Layer):
    def vae_loss(self,x,z_decoded):
        x = K.flatten(x)
        z_decoded = K.flatten(z_decoded)
        xent_loss = keras.metrics.binary_crossentropy(x,z_decoded)
        kl_loss = -5e-4 * K.mean(1+z_log_var-K.square(z_mean)-K.exp(z_log_var),axis = -1)
        return K.mean(xent_loss+kl_loss)
    def call(self, inputs):
        x = inputs[0]
        z_decoded = inputs[1]
        loss = self.vae_loss(x,z_decoded)
        self.add_loss(loss,inputs = inputs)
        return x

y = CusstomVariationalLayer()([input_img,z_decoded])

vae = Model(input_img,y)
vae.compile(optimizer='rmsprop',loss=None)
vae.summary()

from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("E:\\pycharm_Data\\mnist_dataset", one_hot=True)

x_train, y_train = mnist.train.images, mnist.train.labels
x_test, y_test = mnist.test.images, mnist.test.labels


x_train = x_train.astype('float32')/255.
x_train = x_train.reshape(x_train.shape + (1,))
x_test = x_test.astype('float32')/255.
x_test = x_test.reshape(x_test.shape + (1,))
print(type(x_test))

vae.fit(x = x_train,y = None,
        shuffle=True,
        epochs=10,
        batch_size=batch_size,
        validation_data=(x_test,None))
mp = "model_save/iris_model.h5"
vae.save(mp)

n = 15
digit_size = 28
figure = np.zeros((digit_size*n , digit_size*n))
grid_x = norm.ppf(np.linspace(0.05,0.95,n))
grid_y = norm.ppf(np.linspace(0.05,0.95,n))
for i,yi in enumerate(grid_x):
    for j,xi in enumerate(grid_y):
        z_sample = np.array([[xi,yi]])
        z_sample = np.tile(z_sample,batch_size).reshape(batch_size,2)
        x_decoded = decoder.predict(z_sample,batch_size=batch_size)
        digit = x_decoded[0].reshape(digit_size,digit_size)
        figure[i*digit_size:(j+1)*digit_size,
            j*digit_size:(j+1)*digit_size] = digit
plt.figure(figsize=(10,10))
plt.imshow(figure,cmap='Greys_r')
plt.show()

