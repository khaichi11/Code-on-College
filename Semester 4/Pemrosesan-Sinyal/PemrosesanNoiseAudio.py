import sounddevice as sd
import soundfile as sf
import numpy as np

# Parameter yang dapat diubah
# Sampling rate (Hz)
fs       = 44100    
# Durasi dari rekaman
duration = 10      
# Ukuran Noise (semakin kecil nilainya semakin kecil noisenya)
sigma    = 0.1     

# Filter FIR
b = [1/5, 1/5, 1/5, 1/5, 1/5] 
M = len(b) - 1                 

# Merekam audio
print("Mulai merekam...")
x = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()  
print("Selesai merekam.")

# Menyimpan rekaman asli
sf.write('original.wav', x, fs)
print("Tersimpan: original.wav")

# Menambahkan noise pada rekaman
noise = np.random.normal(0, sigma, x.shape)
noisy = x + noise
sf.write('noisy.wav', noisy, fs)
print("Tersimpan: noisy.wav")

# Melakukan Filtering pada audio menggunakan Filter FIR secara manual
# panjang sinyal
N = len(noisy)               
y = np.zeros_like(noisy)     
for n in range(N):
    acc = 0.0               
    for k in range(M+1):     
        if n - k >= 0:       
            acc += b[k] * noisy[n - k, 0]
    y[n, 0] = acc            

# Menyimpan hasil filter manual
sf.write('filtered_manual.wav', y, fs)
print("Tersimpan: filtered_manual.wav")

# Menampilkan informasi delay sistem
delay_samples = M / 2
delay_ms = delay_samples / fs * 1000
print(f"Filter manual: {M+1}-point moving-average")
print(f"Delay ≈ {delay_samples:.1f} sampel ({delay_ms:.2f} ms)")
