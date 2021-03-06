from keras.models import Sequential
from keras.callbacks import LambdaCallback, ModelCheckpoint
from keras.layers import LSTM, Dense, Activation
import argparse
import itertools
import numpy as np
import random
import sys

from dataset import load_sonnets, load_syllables


def _sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


def construct_lstm_model(maxlen=40, initial_weights=None, layers=1):
    """Construct a 2-layer LSTM model on the sonnets dataset.

    Optionally, load from saved weights by passing a filename to initial_weights.

    """
    sonnets = load_sonnets()
    chars = sorted(set([c for s in sonnets for l in s for c in l]))

    model = Sequential()
    model.add(LSTM(256, input_shape=(maxlen, len(chars)), return_sequences=layers>1))
    for i in range(1, layers):
        model.add(LSTM(256, return_sequences=i<(layers-1)))
    model.add(Dense(len(chars)))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    if initial_weights:
        model.load_weights(initial_weights)

    return model


def train_lstm(model, initial_epoch=0, epochs=600, maxlen=40, file_suffix=None):
    def _on_epoch_end(epoch, logs):
        # Function invoked at end of each epoch. Prints generated text.
        print()
        print('----- Generating text after Epoch: %d' % epoch)

        start_index = random.randint(0, len(text) - maxlen - 1)
        for diversity in [0.2, 0.5, 1.0, 1.2]:
            print('----- diversity:', diversity)

            generated = ''
            sentence = text[start_index: start_index + maxlen]
            generated += sentence
            print('----- Generating with seed: "' + sentence + '"')
            sys.stdout.write(generated)

            for i in range(400):
                x_pred = np.zeros((1, maxlen, len(chars)))
                for t, char in enumerate(sentence):
                    x_pred[0, t, char_indices[char]] = 1.

                preds = model.predict(x_pred, verbose=0)[0]
                next_index = sample(preds, diversity)
                next_char = indices_char[next_index]

                generated += next_char
                sentence = sentence[1:] + next_char

                sys.stdout.write(next_char)
                sys.stdout.flush()
            print()

    sonnets = load_sonnets()
    chars = sorted(set([c for s in sonnets for l in s for c in l]))
    text = ''.join([c for s in sonnets for l in s for c in l])
    char_indices = dict((c, i) for i, c in enumerate(chars))
    indices_char = dict((i, c) for i, c in enumerate(chars))

    step = 1
    sentences = []
    next_chars = []
    for i in range(0, len(text) - maxlen, step):
        sentences.append(text[i: i + maxlen])
        next_chars.append(text[i + maxlen])
    print('nb sequences:', len(sentences))

    x = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
    y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
    for i, sentence in enumerate(sentences):
        for t, char in enumerate(sentence):
            x[i, t, char_indices[char]] = 1
        y[i, char_indices[next_chars[i]]] = 1

    print_callback = LambdaCallback(on_epoch_end=_on_epoch_end)
    file_suffix = file_suffix or ''
    filepath= 'weights-improvement-{epoch:02d}-{loss:.4f}%s.hdf5' % file_suffix
    checkpoint = ModelCheckpoint(filepath, monitor='loss', verbose=1, save_best_only=True, mode='min')

    print(x.shape)
    model.fit(x, y,
              batch_size=128,
              epochs=epochs,
              callbacks=[checkpoint],
              initial_epoch=initial_epoch)


def generate_sonnet(model, maxlen=40, sonnets=None, chars=None):
    """Generate a sonnet with the given model.

    Uses the trained model to predict a new sonnet and outputs it to stdout.

    """
    sonnets = sonnets or load_sonnets()
    chars = chars or sorted(set([c for s in sonnets for l in s for c in l]))
    char_indices = dict((c, i) for i, c in enumerate(chars))
    indices_char = dict((i, c) for i, c in enumerate(chars))
    text = ''.join([c for s in sonnets for l in s for c in l])
    start_index = random.randint(0, len(text) - maxlen - 1)
    for diversity in [0.25, 0.75, 1.5]:
        print('----- temperature:', diversity)

        generated = ''
        sentence = "shall i compare thee to a summer's day?\n"
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for i in range(670):
            x_pred = np.zeros((1, maxlen, len(chars)))
            for t, char in enumerate(sentence):
                x_pred[0, t, char_indices[char]] = 1.

            preds = model.predict(x_pred, verbose=0)[0]
            next_index = _sample(preds, diversity)
            next_char = indices_char[next_index]

            generated += next_char
            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str)
    parser.add_argument('--action', type=str, choices=['train', 'generate'], required=True)
    parser.add_argument('--initepoch', type=int, default=0)
    parser.add_argument('--epochs', type=int, default=600)
    parser.add_argument('--layers', type=int, default=1)
    args = parser.parse_args()

    model = construct_lstm_model(initial_weights=args.weights, layers=args.layers)

    if args.action == 'train':
        train_lstm(model, args.initepoch, args.epochs, file_suffix=f'-{args.layers}layer')
    elif args.action == 'generate':
        generate_sonnet(model)
