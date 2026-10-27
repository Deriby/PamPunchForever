"""Original synthesized temp soundtrack and effects, no samples from third parties."""
from pathlib import Path
import numpy as np, wave
OUT=Path(__file__).resolve().parents[1]/'assets/audio'; OUT.mkdir(exist_ok=True)
S=22050
rng=np.random.default_rng(14)
def write(name,a):
 a=np.asarray(a); a=np.tanh(a*.8)
 with wave.open(str(OUT/(name+'.wav')),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(S);w.writeframes((a*26000).astype('<i2').tobytes())
def tone(f,d,decay=8):
 t=np.arange(int(d*S))/S
 return (np.sin(2*np.pi*f*t)+.3*np.sin(2*np.pi*f*2*t)+.12*np.sin(2*np.pi*f*3*t))*np.exp(-t*decay)*np.minimum(1,t*200)
def noise(d,decay=20):
 t=np.arange(int(d*S))/S
 return rng.normal(0,.3,len(t))*np.exp(-t*decay)
def put(a,b,t,vol=1):
 i=int(t*S);n=min(len(b),len(a)-i)
 if n>0:a[i:i+n]+=b[:n]*vol
beat=60/106;duration=beat*64
song=np.zeros(int(duration*S))
# 16-bar original groove, restrained low pentatonic plucks, bass, skin-like percussion.
melody=[0,7,10,7,3,5,7,-2,0,3,5,10,7,5,3,-2]
for b in range(64):
 sec=b*beat
 t=np.arange(int(.24*S))/S
 kick=np.sin(2*np.pi*(72*t-70*t*t))*np.exp(-t*20)
 put(song,kick,sec,.6 if b%2==0 else .24)
 if b%4 in [1,3]:put(song,tone(190,.16,25)+noise(.16,32),sec,.33)
 put(song,noise(.065,55),sec+beat*.5,.3)
 bass=55*2**([0,0,3,-2][(b//4)%4]/12)
 put(song,tone(bass,beat*.9,6),sec,.26)
 if b%2==0:
  f=220*2**(melody[(b//2)%16]/12)
  put(song,tone(f,.8,5),sec,.20)
 # quiet shimmering string with space; no EDM build or drop.
 if b%8==0:
  put(song,tone(440*2**([0,3,5,-2][b//16]/12),2.8,1.9),sec+beat*.25,.065)
write('trilha',song)
write('swing',noise(.18,18)*.9)
write('hit',tone(85,.22,22)+noise(.22,34)*1.4)
write('break',noise(.32,15)+tone(140,.32,20)*.3)
write('jump',tone(400,.18,16)*.6)
write('boom',noise(.65,8)*2+tone(42,.65,8))
write('fuse',noise(.6,2)*.4)
a=np.zeros(int(.5*S))
for i,f in enumerate([660,880,1100]):put(a,tone(f,.28,17),i*.07,.5)
write('collect',a)
a=np.zeros(int(1.8*S))
for i,f in enumerate([330,440,495,660]):put(a,tone(f,1.1,5),i*.13,.5)
write('checkpoint',a)
print('Original temporary audio rendered')
