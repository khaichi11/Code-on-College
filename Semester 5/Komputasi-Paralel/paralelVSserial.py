
import time
import multiprocessing as mp
from collections import Counter
import re

def proses_mengambil_potongan_teks(potongan_teks):
    kata = re.findall(r'\b[a-zA-Z]+\b', potongan_teks.lower())
    return Counter(kata)


def penghitung_kata_serial(teks):
    kata = re.findall(r'\b[a-zA-Z]+\b', teks.lower())
    return Counter(kata)


def penghitung_kata_parallel(teks, nproc=4):
    size = len(teks) // nproc
    potongan_teks = []

    for i in range(nproc):
        mulai = i * size 
        berakhir = len(teks) if i == nproc - 1 else (i + 1) * size
        potongan_teks.append(teks[mulai:berakhir])
    with mp.Pool(nproc) as p:
        results = p.map(proses_mengambil_potongan_teks, potongan_teks)
    total = Counter()
    for r in results:
        total.update(r)
    return total


def print_top(result):
    data = result.most_common(20)
    print("Rank  Kata                        Jumlah")
    print("-----------------------------------------")
    for i, (w, c) in enumerate(data, 1):
        print(f"{i:<5} {w:<25} {c}")


def main():
    try:
        t0 = time.time() 
        with open("data.txt", "r", encoding="utf-8") as f:
            teks = f.read()
        print(f"File dibaca ({time.time() - t0:.4f} detik)")

    except FileNotFoundError:
        print("data.txt tidak ditemukan")
        return

    # ini kode untuk serial processing
    print("\nMenjalankan serial processing")
    t1 = time.time()
    serial_result = penghitung_kata_serial(teks)
    serial_time = time.time() - t1
    print(f"Waktu serial : {serial_time:.4f} detik")
    print(f"Total kata   : {sum(serial_result.values())}")
    print(f"Kata unik    : {len(serial_result)}")
    print("\nTop 20 kata menggunakan serial processing:")
    print_top(serial_result)

    # ini kode untuk parallel processing
    nproc = 16
    print(f"\nMenjalankan parallel processing dengan ({nproc} proses)")
    t2 = time.time()
    parallel_result = penghitung_kata_parallel(teks, nproc)
    parallel_time = time.time() - t2
    print(f"Waktu parallel : {parallel_time:.4f} detik")
    print(f"Total kata     : {sum(parallel_result.values())}")
    print(f"Kata unik      : {len(parallel_result)}")

    print("\nTop 20 kata menggunakan parallel processing:")
    print_top(parallel_result)
    
    # ini perbandingan kecepatan dan waktunya antara paraller dan serial 
    print("\nPerbandingan:")
    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print(f"Speedup        : {speedup:.2f}")
    print(f"Selisih waktu  : {serial_time - parallel_time:.4f} detik")


if __name__ == "__main__":
    # mp.freeze_support() 
    main()
