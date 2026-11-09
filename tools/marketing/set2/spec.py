import sys,numpy as np,wave
from scipy import signal
from PIL import Image
w=wave.open(sys.argv[1]);x=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).mean(1)/32768
f,t,S=signal.spectrogram(x,44100,nperseg=2048,noverlap=1536)
S=10*np.log10(S+1e-12);fl=np.geomspace(30,16000,300);idx=np.searchsorted(f,fl)
img=S[idx][::-1];img=np.clip((img+110)/80,0,1)
im=Image.fromarray((img*255).astype('uint8')).resize((1200,300));im.save(sys.argv[2])
