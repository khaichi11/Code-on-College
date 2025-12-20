import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Gaya Matplotlib (Opsional, pilih salah satu atau tidak sama sekali) ---
# plt.style.use('seaborn-v0_8-pastel')
# plt.style.use('fivethirtyeight')
plt.style.use('ggplot') # Contoh menggunakan ggplot style

# --- Warna untuk Visualisasi ---
WHITE = "#FFFFFF"
GREY = "#B0B0B0" # Sedikit lebih gelap
BLUE = "#4A90E2"  # Perbandingan / Sedang diproses
RED = "#E06666"   # Pertukaran / Kunci / Berhenti
GREEN = "#6AA84F"  # Terurut / Hasil
ORANGE = "#F6B26B" # Elemen kunci / Batas
PURPLE = "#8E7CC3" # Pivot
YELLOW = "#FFD966" # Indeks minimum / Pencarian
DARK_GREY = "#555555" # Latar plot (jika tidak pakai style)

# --- Fungsi Swap ---
def swap(data, i, j):
    data[i], data[j] = data[j], data[i]

# --- Fungsi Sorting (Diperbarui dengan Pesan Status) ---

def bubbleSort(data, draw_data, time_tick):
    n = len(data)
    for i in range(n - 1):
        swapped = False
        for j in range(n - i - 1):
            colors = [GREY] * n
            colors[j] = BLUE
            colors[j + 1] = BLUE
            status = f"Bubble Sort: Membandingkan arr[{j}] ({data[j]}) dan arr[{j + 1}] ({data[j + 1]})"
            yield data, colors, status

            if data[j] > data[j + 1]:
                swap(data, j, j + 1)
                swapped = True
                colors[j] = RED
                colors[j + 1] = RED
                status = f"Bubble Sort: Menukar arr[{j}] ({data[j]}) dan arr[{j + 1}] ({data[j + 1]})"
                yield data, colors, status

        if not swapped:
            status = "Bubble Sort: Array sudah terurut, berhenti lebih awal."
            yield data, [GREEN] * n, status
            return # Keluar dari fungsi jika sudah terurut
    yield data, [GREEN] * n, "Bubble Sort Selesai!"


def selectionSort(data, draw_data, time_tick):
    n = len(data)
    for i in range(n - 1):
        min_index = i
        colors = [GREY] * n
        colors[i] = ORANGE # Posisi saat ini

        status = f"Selection Sort: Mencari minimum mulai dari indeks {i}"
        yield data, colors, status

        for j in range(i + 1, n):
            colors[j] = BLUE # Memeriksa elemen
            colors[min_index] = YELLOW # Minimum sementara
            status = f"Selection Sort: Cek arr[{j}] ({data[j]}), min_idx={min_index} ({data[min_index]})"
            yield data, colors, status
            colors[j] = GREY
            colors[min_index] = GREY if min_index != i else ORANGE

            if data[j] < data[min_index]:
                min_index = j

        colors[min_index] = YELLOW
        status = f"Selection Sort: Minimum ditemukan di indeks {min_index} ({data[min_index]})"
        yield data, colors, status
        time.sleep(time_tick)

        if min_index != i:
            swap(data, i, min_index)
            colors[i] = RED
            colors[min_index] = RED
            status = f"Selection Sort: Menukar arr[{i}] ({data[i]}) dengan arr[{min_index}] ({data[min_index]})"
            yield data, colors, status

        colors[i] = GREEN
        colors[min_index] = GREY
    colors[-1] = GREEN # Pastikan elemen terakhir hijau
    yield data, [GREEN] * n, "Selection Sort Selesai!"

def insertionSort(data, draw_data, time_tick):
    n = len(data)
    for i in range(1, n):
        key = data[i]
        j = i - 1
        colors = [GREEN] * i + [RED] + [GREY] * (n - i - 1)
        status = f"Insertion Sort: Mengambil 'key' = {key} dari indeks {i}"
        yield data, colors, status

        while j >= 0 and data[j] > key:
            data[j + 1] = data[j]
            colors = [GREEN] * (j) + [BLUE, BLUE] + [GREY] * (n - j - 2)
            colors[i] = RED # Tetap tandai posisi asli key
            status = f"Insertion Sort: Geser {data[j]} ke kanan"
            yield data, colors, status
            j -= 1

        data[j + 1] = key
        colors = [GREEN] * (i + 1) + [GREY] * (n - i - 1)
        status = f"Insertion Sort: Sisipkan {key} ke indeks {j+1}"
        yield data, colors, status
    yield data, [GREEN] * n, "Insertion Sort Selesai!"

def partition(data, low, high, draw_data, time_tick):
    pivot = data[high]
    i = low - 1
    colors = [GREY] * len(data)
    colors[high] = PURPLE # Pivot
    status = f"Quick Sort: Partisi {low}-{high}. Pivot = {pivot}"
    yield data, colors, status

    for j in range(low, high):
        colors[j] = BLUE
        yield data, colors, f"Quick Sort: Cek {data[j]} < {pivot}?"
        colors[j] = GREY

        if data[j] < pivot:
            i += 1
            swap(data, i, j)
            colors[i] = RED
            colors[j] = RED
            yield data, colors, f"Quick Sort: Tukar {data[i]} dan {data[j]}"
            colors[i] = GREY
            colors[j] = GREY

    swap(data, i + 1, high)
    colors[i + 1] = GREEN
    colors[high] = GREY
    yield data, colors, f"Quick Sort: Pivot {pivot} di posisi {i+1}"
    return i + 1

def quickSort(data, low, high, draw_data, time_tick):
    if low < high:
        pi_gen = partition(data, low, high, draw_data, time_tick)
        while True:
            try:
                val = next(pi_gen)
                yield val
            except StopIteration as e:
                pi = e.value
                break

        yield from quickSort(data, low, pi - 1, draw_data, time_tick)
        yield from quickSort(data, pi + 1, high, draw_data, time_tick)
    # Yield akhir untuk menandai bagian yang selesai (opsional)
    # else:
    #     if low >= 0 and high < len(data) and low <= high :
    #        colors = [GREY] * len(data)
    #        for k in range(low, high + 1): colors[k] = GREEN
    #        yield data, colors, f"Quick Sort: Bagian {low}-{high} terurut"


def merge(data, left, mid, right, draw_data, time_tick):
    colors = [GREY] * len(data)
    for k in range(left, right + 1): colors[k] = ORANGE # Tandai area merge

    status = f"Merge Sort: Menggabungkan {left}-{mid} dan {mid+1}-{right}"
    yield data, colors, status

    n1 = mid - left + 1
    n2 = right - mid
    L = data[left : left + n1]
    R = data[mid + 1 : mid + 1 + n2]
    i = j = 0
    k = left

    while i < n1 and j < n2:
        colors[left + i] = BLUE
        colors[mid + 1 + j] = BLUE
        yield data, colors, f"Merge Sort: Bandingkan {L[i]} dan {R[j]}"
        colors[left + i] = ORANGE
        colors[mid + 1 + j] = ORANGE

        if L[i] <= R[j]:
            data[k] = L[i]
            i += 1
        else:
            data[k] = R[j]
            j += 1
        colors[k] = RED # Menandakan data yang baru disalin
        yield data, colors, f"Merge Sort: Salin {data[k]} ke indeks {k}"
        colors[k] = GREEN # Tandai sebagai tergabung sementara
        k += 1

    while i < n1:
        data[k] = L[i]
        colors[k] = RED
        yield data, colors, f"Merge Sort: Salin sisa kiri {data[k]} ke {k}"
        colors[k] = GREEN
        i += 1
        k += 1

    while j < n2:
        data[k] = R[j]
        colors[k] = RED
        yield data, colors, f"Merge Sort: Salin sisa kanan {data[k]} ke {k}"
        colors[k] = GREEN
        j += 1
        k += 1

    # Tampilkan hasil merge hijau
    colors = [GREY] * len(data)
    for k in range(left, right + 1): colors[k] = GREEN
    yield data, colors, f"Merge Sort: Penggabungan {left}-{right} selesai."


def mergeSort(data, left, right, draw_data, time_tick):
    if left < right:
        mid = left + (right - left) // 2
        yield from mergeSort(data, left, mid, draw_data, time_tick)
        yield from mergeSort(data, mid + 1, right, draw_data, time_tick)
        yield from merge(data, left, mid, right, draw_data, time_tick)
        # Yield akhir untuk menandai bagian yang selesai hijau
        colors = [GREY] * len(data)
        for k in range(left, right + 1): colors[k] = GREEN
        yield data, colors, f"Merge Sort: Bagian {left}-{right} terurut."


# --- Kelas Utama GUI (Diperbarui) ---

class SortVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualisasi Algoritma Sorting 📊 (Python - Enhanced)")
        self.root.geometry("1000x850+100+30") # Sedikit lebih tinggi untuk status bar
        self.root.config(bg=WHITE)

        self.data = []
        self.original_data = []
        self.sorting_generator = None
        self.sorting_in_progress = False
        self.stop_requested = False

        # --- Frame Kontrol ---
        self.ui_frame = tk.Frame(self.root, width=980, height=200, bg=WHITE)
        self.ui_frame.pack(pady=5)
        self.ui_frame.grid_propagate(False)
        # ... (Layout Kontrol Sama seperti sebelumnya) ...
        # Baris 1: Algoritma & Kecepatan
        tk.Label(self.ui_frame, text="Pilih Algoritma:", bg=WHITE).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.algo_var = tk.StringVar()
        self.algo_menu = ttk.Combobox(self.ui_frame, textvariable=self.algo_var,
                                      values=['Bubble Sort', 'Selection Sort', 'Insertion Sort', 'Quick Sort', 'Merge Sort'],
                                      width=15, state='readonly')
        self.algo_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.algo_menu.current(0)

        tk.Label(self.ui_frame, text="Kecepatan (detik):", bg=WHITE).grid(row=0, column=2, padx=15, pady=5, sticky=tk.W)
        self.speed_scale = tk.Scale(self.ui_frame, from_=0.01, to=1.0, resolution=0.01, orient=tk.HORIZONTAL,
                                    length=150, bg=WHITE, highlightthickness=0)
        self.speed_scale.set(0.1)
        self.speed_scale.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # Baris 2: Ukuran Data & Input Manual
        tk.Label(self.ui_frame, text="Ukuran Data (Random):", bg=WHITE).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.size_scale = tk.Scale(self.ui_frame, from_=10, to=100, resolution=1, orient=tk.HORIZONTAL,
                                   length=150, bg=WHITE, highlightthickness=0)
        self.size_scale.set(30)
        self.size_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        tk.Label(self.ui_frame, text="Input Angka (pisahkan koma):", bg=WHITE).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.input_entry = tk.Entry(self.ui_frame, width=40)
        self.input_entry.grid(row=2, column=1, padx=5, pady=5, columnspan=2, sticky=tk.W)
        self.load_button = tk.Button(self.ui_frame, text="Gunakan Input Ini", command=self.load_input_data, bg=BLUE, fg=WHITE)
        self.load_button.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)

        # Baris 3: Tombol Aksi
        self.generate_button = tk.Button(self.ui_frame, text="Buat Data Acak", command=self.generate_data, bg=ORANGE, fg=WHITE)
        self.generate_button.grid(row=3, column=0, padx=5, pady=15, sticky=tk.E)

        self.start_button = tk.Button(self.ui_frame, text="Mulai Sorting", command=self.start_sorting, bg=GREEN, fg=WHITE)
        self.start_button.grid(row=3, column=1, padx=5, pady=15, sticky=tk.W)

        self.stop_button = tk.Button(self.ui_frame, text="Berhenti", command=self.stop_sorting, bg=RED, fg=WHITE, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=2, padx=5, pady=15, sticky=tk.W)

        self.reset_button = tk.Button(self.ui_frame, text="Reset Data", command=self.reset_data, bg=YELLOW)
        self.reset_button.grid(row=3, column=3, padx=5, pady=15, sticky=tk.W)


        # --- Frame Canvas ---
        self.canvas_frame = tk.Frame(self.root, width=980, height=580, bg=WHITE)
        self.canvas_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        # self.fig.patch.set_facecolor(WHITE) # Set background figure
        # self.ax.set_facecolor(DARK_GREY) # Set background plot

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg=GREY, fg=WHITE)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Selamat Datang! Pilih algoritma dan mulai.")

        self.generate_data() # Generate data awal

    # --- Fungsi Kontrol & Gambar (Diperbarui) ---

    def _set_controls_state(self, state):
        """Mengatur status tombol dan input."""
        # ... (Sama seperti sebelumnya) ...
        self.generate_button.config(state=state)
        self.start_button.config(state=state)
        self.load_button.config(state=state)
        self.input_entry.config(state='normal' if state == tk.NORMAL else 'disabled')
        self.algo_menu.config(state='readonly' if state == tk.NORMAL else 'disabled')
        self.size_scale.config(state=state)
        self.speed_scale.config(state=state)


    def load_input_data(self):
        """Memuat data dari input pengguna."""
        # ... (Sama seperti sebelumnya, tapi panggil update status) ...
        if self.sorting_in_progress: return
        try:
            input_str = self.input_entry.get()
            if not input_str:
                messagebox.showwarning("Input Kosong", "Silakan masukkan angka.")
                return
            data_list = [int(x.strip()) for x in input_str.split(',') if x.strip()]
            if not data_list:
                messagebox.showwarning("Input Tidak Valid", "Format angka tidak benar.")
                return
            if len(data_list) > 100:
                 messagebox.showwarning("Terlalu Banyak Data", "Maksimal 100 angka untuk visualisasi.")
                 data_list = data_list[:100]

            self.data = data_list
            self.original_data = self.data[:]
            self.draw_data(self.data, [GREY] * len(self.data), "Data dari input dimuat.")
            self.sorting_generator = None
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
        except ValueError:
            messagebox.showerror("Input Error", "Pastikan semua input adalah angka dan dipisahkan koma.")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")

    def generate_data(self):
        """Menghasilkan data acak."""
        # ... (Sama seperti sebelumnya, tapi panggil update status) ...
        if self.sorting_in_progress: return
        size = int(self.size_scale.get())
        min_val = 1
        max_val = 100
        self.data = [random.randint(min_val, max_val) for _ in range(size)]
        self.original_data = self.data[:]
        self.draw_data(self.data, [GREY] * len(self.data), f"Data acak ({size} elemen) dibuat.")
        self.sorting_generator = None
        self.reset_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.input_entry.delete(0, tk.END)

    def reset_data(self):
        """Mengembalikan data ke kondisi awal."""
        # ... (Sama seperti sebelumnya, tapi panggil update status) ...
        if self.sorting_in_progress: return
        self.stop_requested = False
        self.data = self.original_data[:]
        self.draw_data(self.data, [GREY] * len(self.data), "Data di-reset ke kondisi awal.")
        self.sorting_generator = None
        self._set_controls_state(tk.NORMAL)
        self.reset_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)


    def draw_data(self, data_to_draw, color_array, status_text=""):
        """Menggambar ulang bar chart dan update status."""
        self.ax.clear()
        self.ax.bar(range(len(data_to_draw)), data_to_draw, color=color_array, width=0.8, edgecolor='black', linewidth=0.5) # Tambah edge
        algo_title = self.algo_var.get() if self.sorting_in_progress else "Visualisasi Data"
        self.ax.set_title(algo_title, fontsize=14)
        self.ax.set_xticks([]) # Tetap sembunyikan jika terlalu banyak
        self.ax.set_yticks([])
        self.ax.set_ylim(0, max(data_to_draw) * 1.1) # Beri sedikit ruang di atas

        if len(data_to_draw) <= 30:
            for i, val in enumerate(data_to_draw):
                self.ax.text(i, val + max(data_to_draw)*0.02, str(val), ha='center', va='bottom', fontsize=9)

        self.fig.canvas.draw_idle()
        self.status_var.set(status_text) # Update status bar

    def start_sorting(self):
        """Memulai proses sorting."""
        # ... (Sama seperti sebelumnya) ...
        if not self.data:
            messagebox.showwarning("Data Kosong", "Buat atau input data terlebih dahulu!")
            return
        if self.sorting_in_progress: return

        self.stop_requested = False
        algo = self.algo_var.get()
        self.sorting_in_progress = True
        self._set_controls_state(tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        data_to_sort = self.data[:]
        speed = self.speed_scale.get()

        # Pilih generator berdasarkan algoritma
        if algo == 'Bubble Sort':
            self.sorting_generator = bubbleSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Selection Sort':
            self.sorting_generator = selectionSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Insertion Sort':
            self.sorting_generator = insertionSort(data_to_sort, self.draw_data, speed)
        elif algo == 'Quick Sort':
            self.sorting_generator = quickSort(data_to_sort, 0, len(data_to_sort) - 1, self.draw_data, speed)
        elif algo == 'Merge Sort':
            self.sorting_generator = mergeSort(data_to_sort, 0, len(data_to_sort) - 1, self.draw_data, speed)
        else:
            self.sorting_in_progress = False
            self._set_controls_state(tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        self.run_visual_step()


    def stop_sorting(self):
        """Mengatur flag untuk menghentikan sorting."""
        # ... (Sama seperti sebelumnya) ...
        if self.sorting_in_progress:
            self.stop_requested = True
            self.stop_button.config(state=tk.DISABLED)


    def run_visual_step(self):
        """Menjalankan satu langkah visualisasi."""
        if not self.sorting_in_progress:
            return

        if self.stop_requested:
            self.sorting_in_progress = False
            self.stop_requested = False
            self.sorting_generator = None
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.draw_data(self.data, [RED] * len(self.data), "Sorting dihentikan oleh pengguna.")
            return

        try:
            # Dapatkan data, warna, dan status dari generator
            data_state, colors, status = next(self.sorting_generator)
            self.data = data_state[:]
            self.draw_data(self.data, colors, status) # Kirim status ke draw_data
            delay_ms = int(self.speed_scale.get() * 1000)
            self.root.after(delay_ms, self.run_visual_step)
        except StopIteration as e:
            # Jika generator selesai normal, coba ambil status akhir
            final_status = "Sorting Selesai!"
            if e.value: # Beberapa generator mungkin mengembalikan status akhir
                data_state, colors, status = e.value
                final_status = status

            # Pastikan hasil akhir hijau
            self.draw_data(self.data, [GREEN] * len(self.data), final_status)
            self.sorting_in_progress = False
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            print(f"{self.algo_var.get()} selesai.")
        except Exception as e:
            messagebox.showerror("Runtime Error", f"Terjadi kesalahan saat sorting: {e}")
            self.sorting_in_progress = False
            self.stop_requested = False
            self._set_controls_state(tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set(f"Error: {e}")

# --- Main Program ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SortVisualizerApp(root)
    root.mainloop()