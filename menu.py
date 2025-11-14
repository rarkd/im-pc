import os # Import modul os untuk membersihkan layar

def clear_screen():
    # Membersihkan layar konsol (berfungsi di Windows, macOS, dan Linux)
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_utama():
    """Menampilkan menu utama dan menangani input pengguna."""
    while True: # Perulangan tak terbatas untuk menjaga menu tetap berjalan
        clear_screen()
        print("="*20)
        print("  MENU APLIKASI  ")
        print("="*20)
        print("1. Opsi Pertama")
        print("2. Opsi Kedua")
        print("3. Keluar")
        print("="*20)

        pilihan = input("Masukkan pilihan Anda (1/2/3): ")

        if pilihan == '1':
            opsi_pertama()
        elif pilihan == '2':
            opsi_kedua()
        elif pilihan == '3':
            print("Terima kasih telah menggunakan aplikasi ini. Sampai jumpa!")
            break # Menghentikan perulangan dan keluar dari program
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")
            input("Tekan Enter untuk kembali ke menu...")

def opsi_pertama():
    clear_screen()
    print("="*20)
    print("  HALAMAN OPSI 1  ")
    print("="*20)
    print("Ini adalah fungsi opsi pertama.")
    # Logika atau kode untuk opsi pertama Anda ada di sini
    input("Tekan Enter untuk kembali ke menu utama...")
    # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

def opsi_kedua():
    clear_screen()
    print("="*20)
    print("  HALAMAN OPSI 2  ")
    print("="*20)
    print("Ini adalah fungsi opsi kedua.")
    # Logika atau kode untuk opsi kedua Anda ada di sini
    input("Tekan Enter untuk kembali ke menu utama...")
    # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

# Memulai program dengan memanggil fungsi menu utama
if __name__ == "__main__":
    menu_utama()
