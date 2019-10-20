import json
import os
import random
import numpy as np
import tensorflow as tf
from gpt2 import model, sample, encoder
from textgen.text_seeds import LEGAL_SENTENCE_LIST, LEGAL_HEADING_LIST


def generate_text(raw_text, model_name='117M', seed=None, nsamples=5, batch_size=1, length=8,
                   temperature=0.35, top_k=40, top_p=20, models_dir='C:\\developer\\aws_ocr_test\\gpt2\\models'):
    models_dir = os.path.expanduser(os.path.expandvars(models_dir))
    if batch_size is None:
        batch_size = 1
    assert nsamples % batch_size == 0

    enc = encoder.get_encoder(model_name, models_dir)
    hparams = model.default_hparams()
    with open(os.path.join(models_dir, model_name, 'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))

    if length is None:
        length = hparams.n_ctx // 2
    elif length > hparams.n_ctx:
        raise ValueError("Can't get samples longer than window size: %s" % hparams.n_ctx)

    with tf.Session(graph=tf.Graph()) as sess:
        context = tf.placeholder(tf.int32, [batch_size, None])
        np.random.seed(seed)
        tf.set_random_seed(seed)
        output = sample.sample_sequence(
            hparams=hparams, length=length,
            context=context,
            batch_size=batch_size,
            temperature=temperature, top_k=top_k, top_p=top_p
        )

        saver = tf.train.Saver()
        ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, model_name))
        saver.restore(sess, ckpt)

        context_tokens = enc.encode(raw_text)
        generated = 0
        text_list = []
        for _ in range(nsamples // batch_size):
            out = sess.run(output, feed_dict={
                context: [context_tokens for _ in range(batch_size)]
            })[:, len(context_tokens):]
            for i in range(batch_size):
                generated += 1
                text = enc.decode(out[i])
                text_list.append(text.strip().replace('\n\n', ''))
        return text_list


def generate_paragraph(length=600, base_test=None):
    if base_test is None:
        base_test = random.choice(LEGAL_SENTENCE_LIST)
    return generate_text(base_test, nsamples=1, length=length, temperature=0.55)


def generate_heading(length=10, base_test=None):
    if base_test is None:
        base_test = random.choice(LEGAL_HEADING_LIST)
    return generate_text(base_test, nsamples=1, length=length, temperature=0.55)


if __name__ == '__main__':
    # text = generate_text('Saturday night is football night.')
    text = generate_heading()
    print(text)
