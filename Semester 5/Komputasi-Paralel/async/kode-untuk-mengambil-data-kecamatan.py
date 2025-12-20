import asyncio
import aiohttp
import pandas as pd
import sys
import os


FOLDER_PATH = r"D:/New folder/Code-for-College/Komputasi-Paralel/async"
FILE_NAME = "data_kecamatan_jabar.xlsx"


OUTPUT_FILE = os.path.join(FOLDER_PATH, FILE_NAME)

BASE_URL = "https://www.emsifa.com/api-wilayah-indonesia/api"
TARGET_PROVINSI = "JAWA BARAT"

async def fetch_json(session, url):
    """Fungsi helper untuk mengambil data JSON dari URL"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return []

async def get_districts_from_regency(session, regency):
    """Mengambil daftar kecamatan dari satu kabupaten/kota"""
    regency_id = regency['id']
    regency_name = regency['name']
    
    url = f"{BASE_URL}/districts/{regency_id}.json"
    districts = await fetch_json(session, url)
    
    results = []
    for d in districts:
        district_name = d['name']
        full_name = f"Kecamatan {district_name}, {regency_name}"
        results.append({'Kecamatan': full_name})
    return results

async def main():
    print(f"--- Memulai Pengambilan Data Kecamatan untuk: {TARGET_PROVINSI} ---")


    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print("1. Mencari Provinsi...")
        provinces = await fetch_json(session, f"{BASE_URL}/provinces.json")
        jabar = next((p for p in provinces if p['name'] == TARGET_PROVINSI), None)
        
        if not jabar:
            print(f"[!] Provinsi '{TARGET_PROVINSI}' tidak ditemukan di API.")
            return
            
        print(f"   -> Ditemukan: {jabar['name']} (ID: {jabar['id']})")

        print(f"2. Mengambil Kabupaten/Kota di {jabar['name']}...")
        url_regencies = f"{BASE_URL}/regencies/{jabar['id']}.json"
        regencies = await fetch_json(session, url_regencies)
        print(f"   -> Ditemukan {len(regencies)} Kabupaten/Kota.")

        print("3. Mengambil Kecamatan...")
        tasks = [get_districts_from_regency(session, reg) for reg in regencies]
        regency_results = await asyncio.gather(*tasks)
        
        all_kecamatan_data = []
        for res in regency_results:
            all_kecamatan_data.extend(res)

    print(f"\nTotal Kecamatan didapatkan: {len(all_kecamatan_data)}")
    print(f"Menyimpan ke: {OUTPUT_FILE}")
    
    if len(all_kecamatan_data) > 0:

        if not os.path.exists(FOLDER_PATH):
            try:
                os.makedirs(FOLDER_PATH)
                print(f"   (Folder dibuat otomatis: {FOLDER_PATH})")
            except Exception as e:
                print(f"   [!] Gagal membuat folder: {e}")
                return

        try:
            df = pd.DataFrame(all_kecamatan_data)
            df.to_excel(OUTPUT_FILE, index=False)
            print("Selesai! File berhasil disimpan.")
        except Exception as e:
            print(f"Error saat menyimpan file Excel: {e}")
    else:
        print("Gagal mendapatkan data (kosong). Cek koneksi internet.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())