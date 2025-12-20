import serial
import time
import csv
import os
from datetime import datetime


# WINDOWS SERIAL PORT
SERIAL_PORT = 'COM8'

# LINUX SERIAL PORT
# SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
OUTPUT_FILE = 'data_gsr.csv'

# write to csv func
def write_to_csv(writer, gsr_value, label):
    """Menulis baris data baru ke file CSV."""
    timestamp = datetime.now().isoformat() # Format waktu standar
    writer.writerow([timestamp, gsr_value, label])

# main func
def main():
    
    # ask the user for label input
    while True:
        label_input = input("Masukkan label untuk sesi ini (terhidrasi / dehidrasi): ").strip().lower()
        if label_input in ['terhidrasi', 'dehidrasi']:
            print(f"Label '{label_input}' diterima.")
            break
        else:
            print("Input tidak valid. Harap ketik 'terhidrasi' atau 'dehidrasi'.")

    
    file_exists = os.path.isfile(OUTPUT_FILE)
    
    # try-except block for serial connection and file operations
    try:
        
        # open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Terhubung ke Arduino di port {SERIAL_PORT}...")
        time.sleep(2)
        
        # append mode for csv file
        with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # if file does not exist, write header
            if not file_exists:
                writer.writerow(['timestamp', 'gsr_value', 'label'])
                print(f"File '{OUTPUT_FILE}' baru dibuat dengan header.")

            print(f"Mulai merekam data untuk label: '{label_input}'...")
            print("Tekan CTRL+C untuk berhenti merekam.")
            
            # record the data
            while True:
                line = ser.readline().decode('utf-8').strip()
                
                if line:
                    try:
                        gsr_value = int(line)
                        print(f"Merekam: {gsr_value}")
                        
                        # write to csv
                        write_to_csv(writer, gsr_value, label_input)
                        
                    except ValueError:
                        print("Menerima data tidak valid, mengabaikan...")
                        pass

    except serial.SerialException as e:
        print(f"Error: Tidak dapat membuka port {SERIAL_PORT}. {e}")
        print("Pastikan port sudah benar dan Arduino terhubung.")
    except KeyboardInterrupt:
        print("\nPerekaman dihentikan oleh pengguna.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Koneksi serial ditutup.")
        print(f"Data telah disimpan di '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    main()