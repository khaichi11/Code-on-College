import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Gaya Matplotlib (Lebih Bersih) ---
plt.style.use('default') # Kembali ke dasar

# --- Warna untuk Visualisasi (Definisi Jelas) ---
WHITE = "#FFFFFF"
GREY = "#C0C0C0"   # Netral / Belum
BLUE = "#007FFF"   # Sedang DILIHAT / Dibandingkan
RED = "#FF0000"    # TUKAR! / PINDAH!
GREEN = "#00B200"  # BENAR! / Sudah Terurut
YELLOW = "#FFFF00" # DITEMUKAN! (Min / Key)
PURPLE = "#8A2BE2" # PIVOT! (Quick Sort)
ORANGE = "#FFA500" # Area Kerja (Merge Sort)
BLACK = "#000000"  # Penunjuk / Teks

# --- Fungsi Swap ---
def swap(data, i, j):
    """Menukar dua elemen dalam list."""
    data[i], data[j] = data[j], data[i]

# --- Fungsi Sorting (Tetap Sama) ---
def bubbleSort(data, draw_data, time_tick):
    """Gelembung: Cek tetangga, geser yang besar."""
    n = len(data)
    for i in range(n - 1):
        swapped = False
        status = f"Putaran {i+1}: Kita dorong angka terbesar ke kanan."
        yield {'data': data, 'colors': [GREY] * (n-i) + [GREEN] * i, 'status': status}

        for j in range(n - i - 1):
            colors = [GREY] * (n - i - 1) + [GREEN] * (i + 1)
            colors[j] = BLUE
            colors[j + 1] = BLUE
            pointers = {j: '▼', j + 1: '▼'}
            status = f"Apakah {data[j]} (kiri) > {data[j+1]} (kanan)?"
            yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers}

            if data[j] > data[j + 1]:
                swap(data, j, j + 1)
                swapped = True
                colors[j] = RED
                colors[j + 1] = RED
                status = f"Ya! Tukar posisi mereka."
                yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers}
            else:
                status = f"Tidak. Biarkan saja."
                yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers}

        colors = [GREY] * (n - i - 1) + [GREEN] * (i + 1)
        yield {'data': data, 'colors': colors, 'status': f"{data[n-i-1]} sudah di tempatnya."}

        if not swapped:
            yield {'data': data, 'colors': [GREEN] * n, 'status': "Semua sudah urut! Berhenti."}
            return
    yield {'data': data, 'colors': [GREEN] * n, 'status': "Bubble Sort Selesai!"}

def selectionSort(data, draw_data, time_tick):
    """Seleksi: Cari paling kecil, pindah ke depan."""
    n = len(data)
    for i in range(n - 1):
        min_index = i
        colors = [GREEN] * i + [GREY] * (n - i)
        colors[i] = ORANGE # Posisi yang mau diisi
        vline = i - 0.5
        status = f"Sekarang cari angka terkecil untuk ditaruh di Posisi {i}."
        yield {'data': data, 'colors': colors, 'status': status, 'vline': vline}

        for j in range(i + 1, n):
            colors[j] = BLUE # Cek angka ini
            colors[min_index] = YELLOW # Ini yang terkecil sejauh ini
            pointers = {j: '?', min_index: '★'}
            status = f"Cek {data[j]}. Apa lebih kecil dari {data[min_index]}?"
            yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': vline}

            if data[j] < data[min_index]:
                colors[min_index] = GREY # Hapus tanda kuning lama
                min_index = j
                colors[min_index] = YELLOW # Tanda kuning baru
                status = f"Ya! Angka terkecil sekarang {data[min_index]}."
                yield {'data': data, 'colors': colors, 'status': status, 'pointers': {min_index: '★'}, 'vline': vline}

            colors[j] = GREY # Kembalikan warna biru ke abu-abu

        colors[min_index] = YELLOW
        colors[i] = ORANGE
        pointers = {i: '🎯', min_index: '★'}
        status = f"Oke, yang terkecil adalah {data[min_index]}. Ayo tukar dengan Posisi {i}."
        yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': vline}
        # Hapus time.sleep agar mode manual tidak terpengaruh
        # time.sleep(time_tick * 0.5)

        if min_index != i:
            swap(data, i, min_index)
            colors[i] = RED
            colors[min_index] = RED
            status = f"TUKAR! {data[i]} sekarang di Posisi {i}."
            yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': vline}

        colors = [GREEN] * (i + 1) + [GREY] * (n - i - 1)
        yield {'data': data, 'colors': colors, 'status': f"Posisi {i} ({data[i]}) beres!", 'vline': i + 0.5}

    yield {'data': data, 'colors': [GREEN] * n, 'status': "Selection Sort Selesai!"}

def insertionSort(data, draw_data, time_tick):
    """Sisip: Ambil satu, cari tempatnya, sisipkan."""
    n = len(data)
    for i in range(1, n):
        key = data[i]
        j = i - 1
        colors = [GREEN] * i + [YELLOW] + [GREY] * (n - i - 1) # Kuning = kartu di tangan
        vline = i - 0.5
        pointers = {i: '✋'} # Tangan memegang kartu
        status = f"Ambil kartu '{key}'. Cari tempatnya di bagian hijau."
        yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': vline}

        while j >= 0 and data[j] > key:
            data[j + 1] = data[j] # Geser kartu hijau ke kanan
            colors = [GREEN] * j + [BLUE, RED] + [GREY] * (n - j - 2)
            colors[i] = YELLOW # Posisi asli tetap kuning
            pointers = {j: '>', j + 1: ' '}
            status = f"Geser {data[j]} ke kanan, karena {key} lebih kecil."
            yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': vline}
            j -= 1

        data[j + 1] = key # Sisipkan kartu ke tempatnya
        colors = [GREEN] * (i + 1) + [GREY] * (n - i - 1)
        pointers = {j + 1: '✅'}
        status = f"Sisipkan {key} di sini!"
        yield {'data': data, 'colors': colors, 'status': status, 'pointers': pointers, 'vline': i + 0.5}

    yield {'data': data, 'colors': [GREEN] * n, 'status': "Insertion Sort Selesai!"}

def partition(data, low, high, draw_data, time_tick):
    pivot = data[high]
    i = low - 1
    colors = [GREY] * len(data)
    for k in range(low, high + 1): colors[k] = ORANGE # Area kerja
    colors[high] = PURPLE # Pivot!
    pointers = {high: '🎯'}
    yield {'data': data, 'colors': colors, 'status': f"Pilih Pivot = {pivot}. Partisi {low}-{high}.", 'pointers': pointers}

    for j in range(low, high):
        colors[j] = BLUE
        yield {'data': data, 'colors': colors, 'status': f"Lihat {data[j]}. Apakah < {pivot}?"}

        if data[j] < pivot:
            i += 1
            swap(data, i, j)
            colors[i] = RED
            colors[j] = RED
            yield {'data': data, 'colors': colors, 'status': f"Ya. Tukar {data[i]} & {data[j]}."}
            colors[i] = ORANGE
            colors[j] = ORANGE
        else:
            colors[j] = ORANGE # Kembalikan ke Orange jika tidak tukar
            yield {'data': data, 'colors': colors, 'status': f"Tidak. Lanjut."}


    swap(data, i + 1, high)
    colors = [GREY] * len(data)
    colors[i + 1] = GREEN # Pivot di posisi benar
    yield {'data': data, 'colors': colors, 'status': f"Pivot {pivot} di tempatnya (Pos {i+1})."}
    return i + 1

def quickSort(data, low, high, draw_data, time_tick):
    if low < high:
        pi_gen = partition(data, low, high, draw_data, time_tick)
        while True:
            try: yield next(pi_gen)
            except StopIteration as e: pi = e.value; break
        yield from quickSort(data, low, pi - 1, draw_data, time_tick)
        yield from quickSort(data, pi + 1, high, draw_data, time_tick)
    elif low == high and low >= 0 and low < len(data): # Tandai elemen tunggal sebagai 'sorted'
        colors = [GREY] * len(data)
        colors[low] = GREEN
        yield {'data': data, 'colors': colors, 'status': f"Elemen {data[low]} sudah di posisi."}


def merge(data, left, mid, right, draw_data, time_tick):
    colors = [GREY] * len(data)
    for k in range(left, right + 1): colors[k] = ORANGE
    yield {'data': data, 'colors': colors, 'status': f"Gabung: Kiri ({left}-{mid}) & Kanan ({mid+1}-{right})."}

    L = data[left : mid + 1]
    R = data[mid + 1 : right + 1]
    i = j = 0
    k = left

    while i < len(L) and j < len(R):
        # Tunjukkan elemen yang dibandingkan
        colors_comp = colors[:]
        colors_comp[left + i] = BLUE
        colors_comp[mid + 1 + j] = BLUE
        yield {'data': data, 'colors': colors_comp, 'status': f"Bandingkan Kiri ({L[i]}) & Kanan ({R[j]})."}

        if L[i] <= R[j]:
            data[k] = L[i]
            status = f"Ambil {L[i]} (Kiri)."
            i += 1
        else:
            data[k] = R[j]
            status = f"Ambil {R[j]} (Kanan)."
            j += 1
        colors[k] = RED # Tunjukkan elemen yang dipindah
        yield {'data': data, 'colors': colors, 'status': status + f" Taruh di Pos {k}."}
        colors[k] = GREEN # Tandai sebagai sudah di merge
        k += 1

    while i < len(L):
        data[k] = L[i]
        colors[k] = RED
        yield {'data': data, 'colors': colors, 'status': f"Ambil sisa Kiri {L[i]}."}
        colors[k] = GREEN
        i += 1
        k += 1

    while j < len(R):
        data[k] = R[j]
        colors[k] = RED
        yield {'data': data, 'colors': colors, 'status': f"Ambil sisa Kanan {R[j]}."}
        colors[k] = GREEN
        j += 1
        k += 1

    yield {'data': data, 'colors': [GREEN if left <= x <= right else GREY for x in range(len(data))], 'status': f"Bagian {left}-{right} selesai digabung."}

def mergeSort(data, left, right, draw_data, time_tick):
    if left < right:
        mid = left + (right - left) // 2
        yield {'data': data, 'colors': [GREY]*len(data), 'status': f"Bagi: {left}-{right} jadi {left}-{mid} & {mid+1}-{right}."}
        yield from mergeSort(data, left, mid, draw_data, time_tick)
        yield from mergeSort(data, mid + 1, right, draw_data, time_tick)
        yield from merge(data, left, mid, right, draw_data, time_tick)
    elif left == right and left >= 0 and left < len(data): # Tandai elemen tunggal
         colors = [GREY] * len(data)
         colors[left] = GREEN
         yield {'data': data, 'colors': colors, 'status': f"Elemen {data[left]} siap digabung."}


# --- Kelas Utama GUI (Diperbarui untuk Mode Manual) ---

class SortVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yuk Belajar Sorting! (Otomatis & Manual) 🎨")
        self.root.geometry("1000x850+100+30")
        self.root.config(bg=WHITE)
        self.root.minsize(900, 750) # Ukuran window minimum

        self.data = []
        self.original_data = []
        self.sorting_generator = None
        self.sorting_in_progress = False
        self.stop_requested = False
        self.drawn_elements = []

        # --- Frame Kontrol ---
        self.ui_frame = tk.Frame(self.root, bg=WHITE)
        self.ui_frame.pack(pady=10, padx=10, fill=tk.X)

        # --- Konfigurasi Grid ---
        self.ui_frame.grid_columnconfigure(0, weight=0) # Kolom Label
        self.ui_frame.grid_columnconfigure(1, weight=1) # Kolom Kontrol/Tombol
        self.ui_frame.grid_columnconfigure(2, weight=1) # Kolom Kontrol/Tombol
        self.ui_frame.grid_columnconfigure(3, weight=1) # Kolom Kontrol/Tombol
        self.ui_frame.grid_columnconfigure(4, weight=1) # Kolom Tombol

        pad_x = 5
        pad_y = 6
        btn_pad_y = 4 # Padding vertikal internal tombol

        # Baris 0: Algoritma & Kecepatan
        tk.Label(self.ui_frame, text="1. Pilih Cara Urut:", bg=WHITE).grid(row=0, column=0, padx=pad_x, pady=pad_y, sticky=tk.W)
        self.algo_var = tk.StringVar()
        self.algo_menu = ttk.Combobox(self.ui_frame, textvariable=self.algo_var,
                                      values=['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Quick Sort', 'Merge Sort'],
                                      width=18, state='readonly')
        self.algo_menu.grid(row=0, column=1, padx=pad_x, pady=pad_y, sticky=tk.EW)
        self.algo_menu.current(0)

        tk.Label(self.ui_frame, text="2. Atur Kecepatan:", bg=WHITE).grid(row=0, column=2, padx=(pad_x + 10, pad_x), pady=pad_y, sticky=tk.W)
        self.speed_scale = tk.Scale(self.ui_frame, from_=0.1, to=2.0, resolution=0.05, orient=tk.HORIZONTAL,
                                    length=200, bg=WHITE, highlightthickness=0, label="Lambat <---> Cepat")
        self.speed_scale.set(0.8)
        self.speed_scale.grid(row=0, column=3, padx=pad_x, pady=0, sticky=tk.EW, columnspan=2)

        # Baris 1: Ukuran Data & Input Manual
        tk.Label(self.ui_frame, text="3. Pilih Data:", bg=WHITE).grid(row=1, column=0, padx=pad_x, pady=pad_y, sticky=tk.W)
        self.size_scale = tk.Scale(self.ui_frame, from_=5, to=30, resolution=1, orient=tk.HORIZONTAL,
                                   length=150, bg=WHITE, highlightthickness=0, label="Jumlah Acak (Max 30)")
        self.size_scale.set(12)
        self.size_scale.grid(row=1, column=1, padx=pad_x, pady=0, sticky=tk.EW)

        tk.Label(self.ui_frame, text="Atau Input Angka:", bg=WHITE).grid(row=1, column=2, padx=(pad_x + 10, pad_x), pady=pad_y, sticky=tk.W)
        self.input_entry = tk.Entry(self.ui_frame, width=35)
        self.input_entry.grid(row=1, column=3, padx=pad_x, pady=pad_y, sticky=tk.EW)
        self.load_button = tk.Button(self.ui_frame, text="Pakai Ini", command=self.load_input_data, bg="#4A90E2", fg=WHITE, pady=btn_pad_y)
        self.load_button.grid(row=1, column=4, padx=pad_x, pady=pad_y, sticky=tk.EW)

        # Baris 2: Mode & Tombol Manual
        tk.Label(self.ui_frame, text="4. Mode Urut:", bg=WHITE).grid(row=2, column=0, padx=pad_x, pady=pad_y, sticky=tk.W)
        self.mode_frame = tk.Frame(self.ui_frame, bg=WHITE) # Simpan frame sebagai atribut
        self.mode_frame.grid(row=2, column=1, columnspan=2, padx=pad_x, pady=pad_y, sticky=tk.EW)
        self.mode_var = tk.StringVar(value="Otomatis")
        self.radio_auto = ttk.Radiobutton(self.mode_frame, text="Otomatis ▶", variable=self.mode_var, value="Otomatis", command=self.update_mode)
        self.radio_auto.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.radio_manual = ttk.Radiobutton(self.mode_frame, text="Manual 👣", variable=self.mode_var, value="Manual", command=self.update_mode)
        self.radio_manual.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.next_step_button = tk.Button(self.ui_frame, text="Langkah ➡", command=self.next_step_command, state=tk.DISABLED, pady=btn_pad_y, bg="#CCCCCC")
        self.next_step_button.grid(row=2, column=3, padx=pad_x, pady=pad_y, sticky=tk.EW, columnspan=2)

        # Baris 3: Tombol Aksi
        tk.Label(self.ui_frame, text="5. Aksi:", bg=WHITE).grid(row=3, column=0, padx=pad_x, pady=(pad_y+5, pad_y), sticky=tk.W)
        self.generate_button = tk.Button(self.ui_frame, text="Buat Acak", command=self.generate_data, bg="#F6B26B", fg=WHITE, pady=btn_pad_y)
        self.generate_button.grid(row=3, column=1, padx=pad_x, pady=(pad_y+5, pad_y), sticky=tk.EW)
        self.start_button = tk.Button(self.ui_frame, text="MULAI!", command=self.start_sorting, bg="#6AA84F", fg=WHITE, font=('Arial', 10, 'bold'), pady=btn_pad_y)
        self.start_button.grid(row=3, column=2, padx=pad_x, pady=(pad_y+5, pad_y), sticky=tk.EW)
        self.stop_button = tk.Button(self.ui_frame, text="BERHENTI", command=self.stop_sorting, bg="#FF4136", fg=WHITE, state=tk.DISABLED, pady=btn_pad_y)
        self.stop_button.grid(row=3, column=3, padx=pad_x, pady=(pad_y+5, pad_y), sticky=tk.EW)
        self.reset_button = tk.Button(self.ui_frame, text="Reset", command=self.reset_data, bg="#FFDC00", pady=btn_pad_y)
        self.reset_button.grid(row=3, column=4, padx=pad_x, pady=(pad_y+5, pad_y), sticky=tk.EW)

        # --- Frame Canvas ---
        self.canvas_frame = tk.Frame(self.root, width=980, height=580, bg=WHITE)
        self.canvas_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#333333", fg=WHITE, font=('Arial', 11, 'italic'))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.generate_data()
        self.update_mode() # Set initial state for speed scale

    def update_mode(self):
        """Update UI based on selected mode."""
        if self.mode_var.get() == "Manual":
            self.speed_scale.config(state=tk.DISABLED)
            self.status_var.set("Mode Manual dipilih. Gunakan tombol 'Langkah ➡' setelah 'MULAI!'.")
        else:
            self.speed_scale.config(state=tk.NORMAL)
            self.status_var.set("Mode Otomatis dipilih. Atur kecepatan dan tekan 'MULAI!'.")

    def next_step_command(self):
        """Called when 'Next Step' button is pressed."""
        if self.sorting_in_progress and self.mode_var.get() == "Manual":
            self.run_visual_step(manual_trigger=True)

    def _set_controls_state(self, state):
        """Mengatur status (aktif/nonaktif) semua kontrol UI."""
        self.generate_button.config(state=state)
        self.start_button.config(state=state)
        self.load_button.config(state=state)
        self.input_entry.config(state='normal' if state == tk.NORMAL else 'disabled')
        self.algo_menu.config(state='readonly' if state == tk.NORMAL else 'disabled')
        self.size_scale.config(state=state)

        mode_state = 'normal' if state == tk.NORMAL else 'disabled'
        self.radio_auto.config(state=mode_state)
        self.radio_manual.config(state=mode_state)

        # Hanya aktifkan speed scale jika NORMAL & Otomatis
        if state == tk.NORMAL and self.mode_var.get() == "Otomatis":
             self.speed_scale.config(state=tk.NORMAL)
        else:
             self.speed_scale.config(state=tk.DISABLED)

        # Tombol Next Step selalu nonaktif saat tidak sorting
        if state == tk.NORMAL:
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")

    def load_input_data(self):
        """Memuat data dari input manual."""
        if self.sorting_in_progress: return
        try:
            input_str = self.input_entry.get()
            if not input_str: messagebox.showwarning("Input Kosong", "Silakan masukkan angka."); return
            data_list = [int(x.strip()) for x in input_str.split(',') if x.strip()]
            if not data_list: messagebox.showwarning("Input Tidak Valid", "Format angka tidak benar."); return
            if len(data_list) > 30: messagebox.showwarning("Terlalu Banyak Data", "Maksimal 30 angka agar visualisasi jelas."); data_list = data_list[:30]
            if any(x <= 0 for x in data_list): messagebox.showwarning("Input Tidak Valid", "Angka harus lebih besar dari 0."); return

            self.data = data_list
            self.original_data = self.data[:]
            self.draw_data({'data': self.data, 'colors': [GREY] * len(self.data), 'status': "Data dari input siap."})
            self.sorting_generator = None; self.reset_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED);
            self.size_scale.set(len(self.data))
        except ValueError: messagebox.showerror("Input Error", "Pastikan semua input adalah angka (integer) dan dipisahkan koma.")
        except Exception as e: messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def generate_data(self):
        """Menghasilkan data acak."""
        if self.sorting_in_progress: return
        size = int(self.size_scale.get())
        min_val = 5; max_val = 100
        self.data = [random.randint(min_val, max_val) for _ in range(size)]
        self.original_data = self.data[:]
        self.draw_data({'data': self.data, 'colors': [GREY] * len(self.data), 'status': f"Data acak ({size} elemen) siap."})
        self.sorting_generator = None; self.reset_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED); self.input_entry.delete(0, tk.END)

    def reset_data(self):
        """Mengembalikan data ke kondisi awal."""
        if self.sorting_in_progress:
            messagebox.showwarning("Tunggu Dulu", "Sorting sedang berjalan, hentikan dulu jika ingin reset.")
            return

        self.stop_requested = False
        if not self.original_data:
            self.generate_data()
        else:
            self.data = self.original_data[:]
            self.draw_data({'data': self.data, 'colors': [GREY] * len(self.data), 'status': "Data kembali ke awal. Siap mulai lagi!"})

        self.sorting_generator = None
        self._set_controls_state(tk.NORMAL)
        self.reset_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")
        self.update_mode() # Panggil untuk set status speed scale

    def draw_data(self, draw_info):
        """Menggambar ulang bar chart dan elemen visual lainnya."""
        while self.drawn_elements:
            try: self.drawn_elements.pop().remove()
            except: pass
        self.ax.clear()
        data = draw_info.get('data', [])
        colors = draw_info.get('colors', [GREY] * len(data))
        status = draw_info.get('status', "")
        pointers = draw_info.get('pointers', {})
        vline_pos = draw_info.get('vline')
        if not data: return
        bar_width = 0.9
        self.ax.bar(range(len(data)), data, color=colors, width=bar_width, edgecolor=BLACK, linewidth=0.7)
        algo_title = self.algo_var.get() if self.sorting_in_progress else "Ayo Urutkan Angka!"
        self.ax.set_title(algo_title, fontsize=16, weight='bold', pad=20)
        self.ax.set_xticks(range(len(data)))
        self.ax.set_xticklabels(range(len(data)), fontsize=9)
        self.ax.set_xlabel("Posisi / Indeks", fontsize=10, labelpad=10)
        self.ax.set_yticks([])
        max_val = max(data) if data else 100
        self.ax.set_ylim(0, max_val * 1.35)
        for i, val in enumerate(data):
            self.drawn_elements.append(self.ax.text(i, val + max_val * 0.03, str(val), ha='center', va='bottom', fontsize=10, weight='bold'))
        for index, text in pointers.items():
            if 0 <= index < len(data):
                self.drawn_elements.append(self.ax.text(index, max_val * 1.15, text, ha='center', va='bottom', fontsize=18, color=BLACK, weight='bold'))
        if vline_pos is not None:
            self.drawn_elements.append(self.ax.axvline(x=vline_pos, color=PURPLE, linestyle='--', linewidth=2, ymax=0.85))
        self.ax.tick_params(axis='x', which='both', bottom=False, top=False)
        self.ax.spines['top'].set_visible(False); self.ax.spines['right'].set_visible(False); self.ax.spines['left'].set_visible(False); self.ax.spines['bottom'].set_visible(False)
        self.fig.tight_layout(pad=2.0)
        self.fig.canvas.draw_idle()
        self.status_var.set(f"APA YANG TERJADI: {status}")

    def start_sorting(self):
        """Memulai proses sorting."""
        if not self.data: messagebox.showwarning("Data Kosong", "Buat atau input data dulu ya!"); return
        if self.sorting_in_progress: return

        self.stop_requested = False
        algo = self.algo_var.get()
        self.sorting_in_progress = True
        self._set_controls_state(tk.DISABLED) # Nonaktifkan semua kontrol
        self.reset_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)

        data_to_sort = self.data[:]
        speed = self.speed_scale.get()

        def wrap_quickSort(data, low, high, draw_data, time_tick):
            yield from quickSort(data, low, high, draw_data, time_tick)
            yield {'data': data, 'colors': [GREEN] * len(data), 'status': "Quick Sort Selesai!"}

        def wrap_mergeSort(data, left, right, draw_data, time_tick):
            yield from mergeSort(data, left, right, draw_data, time_tick)
            yield {'data': data, 'colors': [GREEN] * len(data), 'status': "Merge Sort Selesai!"}

        if algo == 'Bubble Sort': self.sorting_generator = bubbleSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Selection Sort': self.sorting_generator = selectionSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Insertion Sort': self.sorting_generator = insertionSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Quick Sort': self.sorting_generator = wrap_quickSort(data_to_sort, 0, len(data_to_sort) - 1, self.draw_data, speed)
        elif algo == 'Merge Sort': self.sorting_generator = wrap_mergeSort(data_to_sort, 0, len(data_to_sort) - 1, self.draw_data, speed)
        else: # Seharusnya tidak terjadi
            self.sorting_in_progress = False; self._set_controls_state(tk.NORMAL); return

        # Jalankan berdasarkan mode
        if self.mode_var.get() == "Manual":
            self.next_step_button.config(state=tk.NORMAL, bg="#2ECC71") # Aktifkan tombol next
            self.status_var.set("Mode Manual: Tekan 'Langkah ➡' untuk memulai.")
        else:
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")
            self.run_visual_step(manual_trigger=False) # Mulai loop otomatis

    def stop_sorting(self):
        """Mengatur flag untuk menghentikan sorting."""
        if self.sorting_in_progress:
            self.stop_requested = True
            self.stop_button.config(state=tk.DISABLED)
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC") # Nonaktifkan juga next step

    def run_visual_step(self, manual_trigger=False):
        """Menjalankan satu langkah visualisasi."""
        if not self.sorting_in_progress: return

        # Jika mode manual, HANYA jalan jika dipicu oleh tombol
        if self.mode_var.get() == "Manual" and not manual_trigger:
            return

        if self.stop_requested:
            self.sorting_in_progress = False; self.stop_requested = False; self.sorting_generator = None
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")
            self.draw_data({'data': self.data, 'colors': [RED] * len(self.data), 'status': "Sorting DIHENTIKAN!"})
            self.update_mode()
            return

        try:
            # Nonaktifkan tombol 'Next' sebelum eksekusi (untuk mencegah klik ganda)
            if self.mode_var.get() == "Manual":
                 self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")

            draw_info = next(self.sorting_generator)
            self.data = draw_info.get('data', self.data)[:]
            self.draw_data(draw_info)

            # Jika mode manual, aktifkan kembali tombol 'Next' (jika belum selesai)
            if self.mode_var.get() == "Manual":
                self.next_step_button.config(state=tk.NORMAL, bg="#2ECC71")
            else: # Jika otomatis, jadwalkan langkah berikutnya
                delay_ms = int((2.1 - self.speed_scale.get()) * 800)
                self.root.after(delay_ms, self.run_visual_step, False)

        except StopIteration:
            final_status = self.status_var.get().replace("APA YANG TERJADI: ", "")
            if "Selesai" not in final_status:
                 final_status = f"{self.algo_var.get()} Selesai! SEMPURNA!"
            self.draw_data({'data': self.data, 'colors': [GREEN] * len(self.data), 'status': final_status})
            self.sorting_in_progress = False
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")
            self.update_mode()

        except Exception as e:
            messagebox.showerror("Runtime Error", f"Terjadi kesalahan: {e}")
            self.sorting_in_progress = False; self.stop_requested = False
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.next_step_button.config(state=tk.DISABLED, bg="#CCCCCC")
            self.status_var.set(f"Error: {e}")
            self.update_mode()

# --- Main Program ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SortVisualizerApp(root)
    root.mainloop()