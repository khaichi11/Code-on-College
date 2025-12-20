import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
import sys
import os


API_KEY = "" 


BASE_DIR = r"D:/New folder/Code-for-College/Komputasi-Paralel/async"


INPUT_FILE = os.path.join(BASE_DIR, "data_kecamatan_jabar.xlsx")


OUTPUT_FILE = os.path.join(BASE_DIR, "hasil_cuaca_jabar_lengkap.xlsx")

MAX_CONCURRENT_REQUESTS = 50 


class WeatherService:
    """Menangani komunikasi dengan WeatherAPI.com"""
    
    BASE_URL = "http://api.weatherapi.com/v1/current.json"

    async def fetch_weather(self, session, location_name):
        try:
            params = {
                'key': API_KEY,
                'q': location_name,
                'aqi': 'no'
            }
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data.get('current', {})
                    
                    return {
                        'Last Update (time)': current.get('last_updated'),
                        'Suhu (°C)': current.get('temp_c'),
                        'Kelembapan (%)': current.get('humidity'),
                        'Kondisi Cuaca': current.get('condition', {}).get('text'),
                        'Kecepatan Angin (km/h)': current.get('wind_kph'),
                        'Arah Angin (°)': current.get('wind_degree'),
                        'Sinar UV': current.get('uv')
                    }
                elif response.status == 400:
                    print(f"   [x] Lokasi tidak ditemukan API: {location_name}")
                    return None
                else:
                    print(f"   [!] Error Status {response.status} untuk: {location_name}")
                    return None

        except Exception as e:
            print(f"   [!] Error koneksi: {e}")
            return None

class WeatherProcessManager:
    def __init__(self):
        self.weather_service = WeatherService()

        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def process_row(self, session, index, row):

        async with self.semaphore:
            kecamatan = row['Kecamatan']

            query_location = f"{kecamatan}, Indonesia" 

            if index % 50 == 0:
                print(f"-> Memproses baris ke-{index}: {kecamatan}...")
            
            weather_data = await self.weather_service.fetch_weather(session, query_location)
            return index, weather_data

    async def run(self):

        if not os.path.exists(INPUT_FILE):
            print(f"ERROR FATAL: File input tidak ditemukan di:")
            print(f"-> {INPUT_FILE}")
            print("Pastikan nama file dan foldernya benar.")
            return

        try:
            df = pd.read_excel(INPUT_FILE)
            print(f"Berhasil membaca file input: {INPUT_FILE}")
        except Exception as e:
            print(f"Gagal membaca Excel: {e}")
            return

        total_data = len(df)
        print(f"--- Memulai Proses Asyncio untuk {total_data} kecamatan ---")
        

        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for index, row in df.iterrows():
                task = asyncio.create_task(self.process_row(session, index, row))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)

        print("\n--- Menyusun Data ke Excel ---")
        success_count = 0
        
        for index, data in results:
            if data:
                success_count += 1
                for key, value in data.items():
                    df.at[index, key] = value
            else:
                df.at[index, 'Kondisi Cuaca'] = "Gagal / Tidak Ditemukan"


        try:

            output_dir = os.path.dirname(OUTPUT_FILE)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            df.to_excel(OUTPUT_FILE, index=False)
            print(f"\n[SELESAI] Sukses mendapatkan data: {success_count} dari {total_data}")
            print(f"File hasil disimpan di: {OUTPUT_FILE}")
        except PermissionError:
            print(f"\n[ERROR] Gagal menyimpan file! Pastikan file '{OUTPUT_FILE}' sedang TIDAK DIBUKA di Excel.")

if __name__ == "__main__":
    if API_KEY == "MASUKKAN_API_KEY_ANDA_DISINI" or not API_KEY:
        print("PERINGATAN KERAS: API Key belum dimasukkan! Script tidak akan jalan.")
    else:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        asyncio.run(WeatherProcessManager().run())
