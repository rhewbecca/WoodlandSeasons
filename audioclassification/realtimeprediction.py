from tensorflow.keras.models import load_model
from clean import downsample_mono, envelope
from kapre.time_frequency import STFT, Magnitude, ApplyFilterbank, MagnitudeToDecibel
from sklearn.preprocessing import LabelEncoder
import numpy as np
from glob import glob
import argparse
import os
import pandas as pd
from tqdm import tqdm
import sounddevice as sd
import time
from pythonosc import osc_message_builder
from pythonosc import udp_client
#import stick

'''
def make_prediction(args):

    model = load_model(args.model_fn,
        custom_objects={'STFT':STFT,
                        'Magnitude':Magnitude,
                        'ApplyFilterbank':ApplyFilterbank,
                        'MagnitudeToDecibel':MagnitudeToDecibel})
    wav_paths = glob('{}/**'.format(args.src_dir), recursive=True)
    wav_paths = sorted([x.replace(os.sep, '/') for x in wav_paths if '.wav' in x])
    classes = sorted(os.listdir(args.src_dir))
    labels = [os.path.split(x)[0].split('/')[-1] for x in wav_paths]
    le = LabelEncoder()
    y_true = le.fit_transform(labels)
    results = []

    for z, wav_fn in tqdm(enumerate(wav_paths), total=len(wav_paths)):
        rate, wav = downsample_mono(wav_fn, args.sr)
        mask, env = envelope(wav, rate, threshold=args.threshold)
        clean_wav = wav[mask]
        step = int(args.sr*args.dt)
        batch = []

        for i in range(0, clean_wav.shape[0], step):
            sample = clean_wav[i:i+step]
            sample = sample.reshape(-1, 1)
            if sample.shape[0] < step:
                tmp = np.zeros(shape=(step, 1), dtype=np.float32)
                tmp[:sample.shape[0],:] = sample.flatten().reshape(-1, 1)
                sample = tmp
            batch.append(sample)
        X_batch = np.array(batch, dtype=np.float32)
        y_pred = model.predict(X_batch)
        y_mean = np.mean(y_pred, axis=0)
        y_pred = np.argmax(y_mean)
        real_class = os.path.dirname(wav_fn).split('/')[-1]
        print('Actual class: {}, Predicted class: {}'.format(real_class, classes[y_pred]))
        results.append(y_mean)

    np.save(os.path.join('logs', args.pred_fn), np.array(results))
'''

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
    
def callback(indata, frames, time, status):
    global window, model, classes, counter
    screening_window = np.array((2,2))
    if any(indata):
        window=window[indata.shape[0]:window.shape[0],:]   
        window=np.concatenate((window, indata), axis=0)
        x = np.expand_dims(window, axis=0)
        #each 5 updates make and print prediction
        if (counter%10)==0:
            if np.max(x)>300:            
                #mask, env = envelope(x[0,:,0], args.sr, threshold=args.threshold)
                #x = x[0,mask,0]
                yhat = model.predict(x)
                hittedby = np.argmax(yhat)  # 0 = heart , 1 = irregular, 2 = sphere
                hittedby = int(hittedby)
                #yhat = np.argmax(yhat)
                print(classes[np.argmax(yhat)], yhat)
                client.send_message('/stick', hittedby)
                #stick.stick = hittedby                
        counter=counter+1


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Audio Classification Training')
    parser.add_argument('--model_fn', type=str, default='audioclassification/models/conv2d.h5',
                        help='model file to make predictions')
    parser.add_argument('--pred_fn', type=str, default='y_pred',
                        help='fn to write predictions in logs dir')
    parser.add_argument('--src_dir', type=str, default='audioclassification/wavfiles',
                        help='directory containing wavfiles to predict')
    parser.add_argument('--dt', type=float, default=1.0,
                        help='time in seconds to sample audio')
    parser.add_argument('--sr', type=int, default=16000,
                        help='sample rate of clean audio')
    parser.add_argument('--threshold', type=str, default=20,
                        help='threshold magnitude for np.int16 dtype')
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    args, _ = parser.parse_known_args()

    #inizialize osc client
    client = udp_client.SimpleUDPClient("192.168.178.106", 12345)
    


    window = np.random.randint(-32768,32768,size=(4800, 1))
    model = load_model(args.model_fn,
        custom_objects={'STFT':STFT,
                        'Magnitude':Magnitude,
                        'ApplyFilterbank':ApplyFilterbank,
                        'MagnitudeToDecibel':MagnitudeToDecibel})
    classes = sorted(os.listdir(args.src_dir))
    counter=0

    stream = sd.InputStream(device=args.device, channels=1, callback=callback, blocksize=480,
                           samplerate=args.sr,
                           dtype= np.int16)
    
    stream.start()
    #stick.initialize()
    #currentstick=stick.stick
    #with stream:
    #    while True:
    #        if currentstick!=stick.stick:
    #            currentstick=stick.stick
    #            print(currentstick)


    #while True:
    #    if currentstick!=stick.stick:
    #        currentstick=stick.stick
    #        print(currentstick)


    
    time.sleep(90)
    stream.stop()

    

    ##make_prediction(args)