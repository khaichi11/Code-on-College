#include <iostream>
#include <string>
using namespace std;


struct Node {
    int nomor;
    string Minuman;
    int harga;
    Node* next;
};


Node* head = nullptr;
Node* tail = nullptr;
int sum_nomor = 0;


void Tambah_Antrian();
void Tampilkan_Antrian();
void Edit_Minuman_Bobaritma();
void Ambil_Bobaritma();
int  Harga_Bobaritma();
char Memanggil_tambah_Bobaritma();


int main() {
    char input;


    do {
        cout << "Menu:" << endl;
        cout << "1. Tambah Antrian" << endl;
        cout << "2. Tampilkan Antrian" << endl;
        cout << "3. Edit Minuman" << endl;
        cout << "4. Ambil Minuman" << endl;
        cout << "5. Keluar" << endl;
        cout << "Pilihan Anda: ";
        cin >> input; 


        switch (input) {
            case '1':
                Tambah_Antrian();
                break;


            case '2':
                Tampilkan_Antrian();
                break;


            case '3':
                Edit_Minuman_Bobaritma();
                break;


            case '4':
                Ambil_Bobaritma(); 
                break;


            case '5':
                cout << "Arigatou!" << endl;
                cout << "Anda keluar dari program" << endl;
                cout << "Program telah selesai" << endl;
                cout << "Semoga harimu menyenangkan :)" << endl;
                break;


            default:
                cout << "ERROR" << endl;
                cout << "Pilihan yang kamu masukkan tidak ada dalam daftar menu." << endl;
                cout << "Silakan coba lagi." << endl;
        }
    } while (input != '5');


    return 0;
}


void Tambah_Antrian() {
    char tambah_minuman;
    bool pilih_tambah_minuman = true;


    cout << "Hore!!! Nomor antrian " << sum_nomor + 1 << " telah ditambahkan." << endl;


    Node* Node_Baru = new Node();
    Node_Baru->nomor = sum_nomor + 1;
    Node_Baru->next = nullptr;


    while (pilih_tambah_minuman) {
        cout << "Mau pesan minuman apa: ";
        cin >> Node_Baru->Minuman;
        Node_Baru->harga = Harga_Bobaritma();
        cout << "Yakin dengan minuman yang anda input? Y/N, y/n: ";
        cin >> tambah_minuman;
        if (tambah_minuman == 'Y' || tambah_minuman == 'y') {
            break;
        } else if (tambah_minuman == 'N' || tambah_minuman == 'n') {
            pilih_tambah_minuman = true;
        } else {
            do {
                tambah_minuman = Memanggil_tambah_Bobaritma();
            } while (tambah_minuman != 'Y' && tambah_minuman != 'N' && tambah_minuman != 'n' && tambah_minuman != 'y');
        }
    }


    if (head == nullptr) {
        head = Node_Baru;
        tail = Node_Baru;
    } else {
        tail->next = Node_Baru;
        tail = Node_Baru;
    }


    cout << "Arigatou!, pesananmu telah dicatat" << endl;
    ++sum_nomor;
}


char Memanggil_tambah_Bobaritma() {
    char tambah_minuman;
    cout << "Apakah mau menambah lagi? Y/N, y/n: ";
    cin >> tambah_minuman;
    return tambah_minuman;
}


void Ambil_Bobaritma() {
    if (head == nullptr) {
        cout << "Antrian kosong." << endl;
        return;
    }


    int nomor;
    cout << "Konnichiwa! Mau ambil Minuman nomor berapa: ";
    cin >> nomor;


    if (nomor < 1 || nomor > sum_nomor) {
        cout << "Nomor antrian tidak valid." << endl;
        return;
    }


    Node* current = head;
    Node* prev = nullptr;
    Node* lanjut = nullptr;


    while (current != nullptr && current->nomor != nomor) {
        prev = current;
        current = current->next;
    }


    if (current == nullptr) {
        cout << "Wah, nomor antrian sudah diambil :(" << endl;
        return;
    }


    lanjut = current->next;
    while(lanjut != nullptr){
        lanjut->nomor -= 1;
        lanjut = lanjut->next;
    }


    cout << "Ambil Minuman untuk nomor antrian ke - " << nomor << " (" << current->Minuman << ")." << endl;
    cout << "Semoga hausmu hilang dan programmu lancar :D" << endl << endl;


    if (current == head) {
        head = current->next;
    } else {
        prev->next = current->next;
    }


    if (current == tail) {
        tail = prev;
    }


    delete current;
    --sum_nomor;
}


void Tampilkan_Antrian() {
    if (head == nullptr) {
        cout << "Antrian kosong." << endl;
        return;
    }


    cout << "Daftar Nomor Antrian Yang Sudah Ada :" << endl;
    Node* current = head;
    while (current != nullptr) {
        cout << "Nomor: " << current->nomor << ", Minuman: " << current->Minuman << ", Harga: " << "Rp. " << current->harga << endl;
        current = current->next;
    }
}


void Edit_Minuman_Bobaritma() {
    if (head == nullptr) {
        cout << "Antrian kosong." << endl;
        return;
    }


    int nomor;
    cout << "Masukkan nomor antrian yang ingin diedit: ";
    cin >> nomor;


    if (nomor < 1 || nomor > sum_nomor) {
        cout << "Nomor antrian tidak valid." << endl;
        return;
    }


    Node* current = head;
    while (current != nullptr && current->nomor != nomor) {
        current = current->next;
    }


    if (current == nullptr) {
        cout << "Nomor antrian tidak ditemukan." << endl;
        return;
    }


    cout << "Data lama - Minuman: " << current->Minuman << ", Harga: " << current->harga << endl;
    cout << "Masukkan nama Minuman baru: ";
    cin >> current->Minuman;
    current->harga = Harga_Bobaritma();
    cout << "Data telah berhasil diperbarui!" << endl;


    Tampilkan_Antrian(); // Perbarui tampilan setelah edit
}


int Harga_Bobaritma() {
    int harga = 0;
    cout << "Masukkan harga Minuman tersebut: ";
    cin >> harga;
    return harga;
}
