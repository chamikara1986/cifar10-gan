from keras.datasets import mnist, cifar10
from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import Conv2D, Conv2DTranspose
from keras.models import Sequential, Model
from keras.optimizers import Adam
import matplotlib.pyplot as plt
import numpy as np
import os

losses = []
accuracies = []
img_rows = 32
img_cols = 32
channels = 3
img_shape = (img_rows, img_cols, channels)
z_dim = 100
plt.switch_backend('agg')

def noisy_labels(label, batch_size):
    mislabeled = batch_size // 10
    labels = []
    if label:
        labels = np.concatenate([
            np.random.normal(0.7, 1, batch_size-mislabeled),
            np.random.normal(0, 0.3, mislabeled)], axis=0)
    else:
        labels = np.concatenate([
            np.random.normal(0, 0.3, batch_size-mislabeled),
            np.random.normal(0.7, 1, mislabeled)], axis=0)
    return np.array(labels)

def generator(img_shape, z_dim):
    model = Sequential()
    model.add(Dense(256 * 8 * 8, input_dim=z_dim))
    model.add(Reshape((8, 8, 256)))

    model.add(Conv2DTranspose(
                128, kernel_size=3, strides=2, padding='same'))
    model.add(BatchNormalization())
    model.add(LeakyReLU(alpha=0.01))
    model.add(Conv2DTranspose(
                64, kernel_size=3, strides=1, padding='same'))
    model.add(BatchNormalization())
    model.add(LeakyReLU(alpha=0.01))
    model.add(Conv2DTranspose(
                3, kernel_size=3, strides=2, padding='same'))
    model.add(Activation('tanh'))
    z = Input(shape=(z_dim,))
    img = model(z)
    return Model(z, img)

def discriminator(img_shape):
    model = Sequential()
    model.add(Conv2D(32, kernel_size=3, strides=2, 
                             input_shape=img_shape, padding='same'))
    model.add(LeakyReLU(alpha=0.01))
    model.add(Conv2D(64, kernel_size=3, strides=2, 
                             input_shape=img_shape, padding='same'))
    model.add(BatchNormalization())
    model.add(LeakyReLU(alpha=0.01))
    model.add(Conv2D(128, kernel_size=3, strides=2, 
                             input_shape=img_shape, padding='same'))
    model.add(BatchNormalization())
    model.add(LeakyReLU(alpha=0.01))
    model.add(Flatten())
    model.add(Dense(1, activation='sigmoid'))
    img = Input(shape=img_shape)
    prediction = model(img)
    return Model(img, prediction)

def filter_by_category(xt, yt, i):
    result = []
    for x, y in zip(xt, yt):
        if y in i:
            result.append(x)
    return np.array(result) 

def train(epochs, batch_size, sample_interval, categories):
    (X_train, Y_train), (_, _) = cifar10.load_data()

    X_train = filter_by_category(X_train, Y_train, categories)
      
    # Scale -1 to 1
    X_train = X_train / 127.5 - 1.

    ones = noisy_labels(1, batch_size)
    zeros = noisy_labels(0, batch_size)

    for epoch in range(epochs):
        
        ind = np.random.randint(0, X_train.shape[0], batch_size)
        images = X_train[ind]

        # Generate images
        z = np.random.normal(0, 1, (batch_size, 100))
        images_gen = generator.predict(z)
        
        # Discriminator loss
        d_loss = discriminator.train_on_batch(images, ones)
        d_loss_gen = discriminator.train_on_batch(images_gen, zeros)
        d_loss = 0.5 * np.add(d_loss, d_loss_gen)

        # Generate images -- What if we used the same ones as before?
        z = np.random.normal(0, 1, (batch_size, 100))
        images_gen = generator.predict(z)

        # Generator loss
        g_loss = combined.train_on_batch(z, ones)

        print ("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, d_loss[0], 100*d_loss[1], g_loss))

        losses.append((d_loss[0], g_loss))
        accuracies.append(100*d_loss[1])
        
        if epoch % sample_interval == 0:
            sample_images(epoch)

def sample_images(epoch, image_grid_rows=4, image_grid_columns=4):
    plt.figure(figsize=(10,10))
    
    # Sample random noise
    z = np.random.normal(0, 1, 
              (image_grid_rows * image_grid_columns, z_dim))

    # Generate images from random noise
    gen_imgs = generator.predict(z)

    # Rescale images to 0-1
    gen_imgs = 0.5 * gen_imgs + 0.5
 
    for i in range(gen_imgs.shape[0]):
        plt.subplot(4, 4, i+1)
        image = gen_imgs[i, :, :, :]

        try:
            image = np.reshape(image, [img_cols, img_rows, channels])
        except:
            image = np.reshape(image, [img_cols, img_rows])

        plt.imshow(image, cmap="gray")
        plt.axis('off')
    plt.tight_layout()
            
    if not os.path.exists("./images"):
        os.makedirs("./images")
    filename = "./images/sample_%d.png" % epoch
        
    plt.savefig(filename)
    plt.close("all")

#=================================================================
    
epochs = 1000000
batch_size = 32
sample_interval = 1000

discriminator = discriminator(img_shape)
discriminator.compile(loss='binary_crossentropy', 
                      optimizer=Adam(), metrics=['accuracy'])

generator = generator(img_shape, z_dim)

z = Input(shape=(100,))
img = generator(z)

discriminator.trainable = False

prediction = discriminator(img)

combined = Model(z, prediction)
combined.compile(loss='binary_crossentropy', optimizer=Adam())

#0 airplane
#1 automobile
#2 bird
#3 cat
#4 deer
#5 dog
#6 frog
#7 horse
#8 ship
#9 truck

train(epochs, batch_size, sample_interval, categories=[7])
