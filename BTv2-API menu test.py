import socket
import hashlib
import binascii
import os # Import modul os untuk membersihkan layar

class MikrotikAPI:
    def __init__(self, host, port=8728):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
    
    def connect(self):
        """Membuat koneksi ke Mikrotik"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            print(f"Terhubung ke {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Gagal terhubung: {e}")
            return False
    
    def send_length(self, data):
        """Mengirim panjang data sesuai protokol Mikrotik"""
        length = len(data)
        if length < 0x80:
            self.sock.send(bytes([length]))
        elif length < 0x4000:
            self.sock.send(bytes([length >> 8 | 0x80, length & 0xFF]))
        elif length < 0x200000:
            self.sock.send(bytes([length >> 16 | 0xC0, length >> 8 & 0xFF, length & 0xFF]))
        elif length < 0x10000000:
            self.sock.send(bytes([length >> 24 | 0xE0, length >> 16 & 0xFF, length >> 8 & 0xFF, length & 0xFF]))
        else:
            self.sock.send(bytes([0xF0, length >> 24 & 0xFF, length >> 16 & 0xFF, length >> 8 & 0xFF, length & 0xFF]))
    
    def send_word(self, word):
        """Mengirim kata (word) sesuai protokol Mikrotik"""
        self.send_length(word)
        self.sock.send(word.encode('utf-8'))
    
    def send_sentence(self, words):
        """Mengirim kalimat (sentence) yang terdiri dari beberapa kata"""
        for word in words:
            self.send_word(word)
        self.sock.send(b'\x00')
    
    def read_length(self):
        """Membaca panjang data dari socket"""
        c = self.sock.recv(1)[0]
        if c & 0x80 == 0x00:
            return c
        elif c & 0xC0 == 0x80:
            return ((c & ~0xC0) << 8) + self.sock.recv(1)[0]
        elif c & 0xE0 == 0xC0:
            return ((c & ~0xE0) << 16) + (self.sock.recv(1)[0] << 8) + self.sock.recv(1)[0]
        elif c & 0xF0 == 0xE0:
            return ((c & ~0xF0) << 24) + (self.sock.recv(1)[0] << 16) + (self.sock.recv(1)[0] << 8) + self.sock.recv(1)[0]
        elif c & 0xF8 == 0xF0:
            return (self.sock.recv(1)[0] << 24) + (self.sock.recv(1)[0] << 16) + (self.sock.recv(1)[0] << 8) + self.sock.recv(1)[0]
    
    def read_word(self):
        """Membaca kata dari socket"""
        length = self.read_length()
        if length == 0:
            return ''
        return self.sock.recv(length).decode('utf-8')
    
    def read_sentence(self):
        """Membaca kalimat dari socket"""
        sentence = []
        while True:
            word = self.read_word()
            if word == '':
                break
            sentence.append(word)
        return sentence
    
    def login(self, username, password):
        """Login ke Mikrotik"""
        try:
            # Untuk RouterOS versi baru (6.43+), langsung kirim username dan password
            self.send_sentence(['/login', f'=name={username}', f'=password={password}'])
            response = self.read_sentence()
            
            # Cek apakah login berhasil
            if len(response) > 0 and response[0] == '!done':
                print("Login berhasil!")
                return True
            elif len(response) > 0 and response[0] == '!trap':
                # Login gagal, tampilkan pesan error
                error_msg = "Login gagal!"
                for word in response:
                    if '=message=' in word:
                        error_msg = word.split('=message=')[1]
                print(f"Login gagal: {error_msg}")
                return False
            else:
                # Coba metode lama dengan challenge (RouterOS < 6.43)
                self.send_sentence(['/login'])
                response = self.read_sentence()
                
                if len(response) > 1 and '=ret=' in response[1]:
                    challenge = response[1].split('=ret=')[1]
                    challenge_bytes = binascii.unhexlify(challenge)
                    
                    # Buat hash MD5 dari password dan challenge
                    md5 = hashlib.md5()
                    md5.update(b'\x00')
                    md5.update(password.encode('utf-8'))
                    md5.update(challenge_bytes)
                    hash_result = binascii.hexlify(md5.digest()).decode('utf-8')
                    
                    # Kirim username dan hash
                    self.send_sentence(['/login', f'=name={username}', f'=response=00{hash_result}'])
                    response = self.read_sentence()
                    
                    if response[0] == '!done':
                        print("Login berhasil!")
                        return True
                
                print("Login gagal!")
                return False
        except Exception as e:
            print(f"Error saat login: {e}")
            return False
    
    def talk(self, command):
        """Mengirim perintah dan menerima respons"""
        if isinstance(command, str):
            command = [command]
        
        self.send_sentence(command)
        response = []
        
        while True:
            sentence = self.read_sentence()
            if len(sentence) == 0:
                break
            
            response.append(sentence)
            
            if sentence[0] == '!done':
                break
        
        return response
    
    def get_interfaces(self):
        """Mengambil daftar interface"""
        response = self.talk('/interface/print')
        interfaces = []
        
        for sentence in response:
            if sentence[0] == '!re':
                interface_data = {}
                for word in sentence:
                    if word.startswith('='):
                        key_value = word[1:].split('=', 1)
                        if len(key_value) == 2:
                            interface_data[key_value[0]] = key_value[1]
                        elif len(key_value) == 1:
                            interface_data[key_value[0]] = ''
                if interface_data:
                    interfaces.append(interface_data)
        
        return interfaces
    
    def rename_interface(self, old_name, new_name):
        """Mengubah nama interface"""
        try:
            # Cari interface berdasarkan nama
            interfaces = self.get_interfaces()
            interface_id = None
            
            for iface in interfaces:
                if iface.get('name') == old_name:
                    interface_id = iface.get('.id')
                    break
            
            if not interface_id:
                print(f"Interface '{old_name}' tidak ditemukan")
                return False
            
            # Ubah nama interface
            command = ['/interface/set', f'=.id={interface_id}', f'=name={new_name}']
            response = self.talk(command)
            
            # Cek response
            if response and response[0][0] == '!done':
                print(f"Interface '{old_name}' berhasil diubah menjadi '{new_name}'")
                return True
            else:
                print(f"Gagal mengubah nama interface")
                for sentence in response:
                    for word in sentence:
                        if '=message=' in word:
                            print(f"Error: {word.split('=message=')[1]}")
                return False
                
        except Exception as e:
            print(f"Error saat mengubah nama interface: {e}")
            return False
    
    def set_interface_comment(self, interface_name, comment):
        """Mengubah comment interface"""
        try:
            interfaces = self.get_interfaces()
            interface_id = None
            
            for iface in interfaces:
                if iface.get('name') == interface_name:
                    interface_id = iface.get('.id')
                    break
            
            if not interface_id:
                print(f"Interface '{interface_name}' tidak ditemukan")
                return False
            
            command = ['/interface/set', f'=.id={interface_id}', f'=comment={comment}']
            response = self.talk(command)
            
            if response and response[0][0] == '!done':
                print(f"Comment interface '{interface_name}' berhasil diubah menjadi '{comment}'")
                return True
            else:
                print(f"Gagal mengubah comment interface")
                return False
                
        except Exception as e:
            print(f"Error saat mengubah comment: {e}")
            return False
    
    def enable_disable_interface(self, interface_name, enable=True):
        """Enable atau disable interface"""
        try:
            interfaces = self.get_interfaces()
            interface_id = None
            
            for iface in interfaces:
                if iface.get('name') == interface_name:
                    interface_id = iface.get('.id')
                    break
            
            if not interface_id:
                print(f"Interface '{interface_name}' tidak ditemukan")
                return False
            
            disabled_value = 'no' if enable else 'yes'
            command = ['/interface/set', f'=.id={interface_id}', f'=disabled={disabled_value}']
            response = self.talk(command)
            
            if response and response[0][0] == '!done':
                status = "enabled" if enable else "disabled"
                print(f"Interface '{interface_name}' berhasil {status}")
                return True
            else:
                print(f"Gagal mengubah status interface")
                return False
                
        except Exception as e:
            print(f"Error saat mengubah status interface: {e}")
            return False
    
    def disconnect(self):
        """Memutus koneksi"""
        if self.sock:
            self.sock.close()
            self.connected = False
            print("Koneksi ditutup")

# Contoh penggunaan
if __name__ == "__main__":
    # Konfigurasi koneksi
    
    # Menanyakan nama pengguna
    #nama1 = input("IP HOST :")
    #nama2 = input("USERNAME :")
    #nama3 = input("PASSWORD :")
    HOST = '192.168.80.2'  # Ganti dengan IP Mikrotik Anda
    PORT = 8728
    USERNAME = 'admin'      # Ganti dengan username Anda
    PASSWORD = 'admin'      # Ganti dengan password Anda
    
    # Buat instance dan koneksi
    api = MikrotikAPI(HOST, PORT)
    
    if api.connect():
        if api.login(USERNAME, PASSWORD):

            def clear_screen():
            # Membersihkan layar konsol (berfungsi di Windows, macOS, dan Linux)
                os.system('cls' if os.name == 'nt' else 'clear')

            def menu_utama():
                """Menampilkan menu utama dan menangani input pengguna."""
                while True: # Perulangan tak terbatas untuk menjaga menu tetap berjalan
                    clear_screen()
                    print("="*20)
                    print("       AmbaWin        ")
                    print("   by aww - ver 0.1   ")
                    print("="*20)
                    print("     MENU UTAMA       ")
                    print("="*20)
                    print("1. Interface")
                    print("2. Wireles")
                    print("3. wireles")
                    print("4. wireles")
                    print("5. wireles")
                    print("6. wireles")
                    print("7. Keluar")
                    print("="*20)

                    pilihan = input("Masukkan pilihan Anda : ")

                    if pilihan == '1':
                        interface()
                    elif pilihan == '2':
                        opsi_kedua()
                    elif pilihan == '3':
                        opsi_kedua()
                    elif pilihan == '4':
                        opsi_kedua()
                    elif pilihan == '5':
                        opsi_kedua()
                    elif pilihan == '6':
                        opsi_kedua()
                    elif pilihan == '7':
                        print("Terima kasih telah menggunakan aplikasi ini. Sampai jumpa!")
                        print("ambalubub")
                        break # Menghentikan perulangan dan keluar dari program
                    else:
                        print("Pilihan tidak valid. Silakan coba lagi.")
                        input("Tekan Enter untuk kembali ke menu...")

            def interface():
                while True:
                    clear_screen()
                    print("="*20)
                    print("       AmbaWin        ")
                    print("   by aww - ver 0.1   ")
                    print("="*20)
                    print("      INTERFACE       ")
                    interfaces = api.get_interfaces()
                    for iface in interfaces:
                        name = iface.get('name', 'N/A')
                        iface_type = iface.get('type', 'N/A')
                        disabled = iface.get('disabled', 'false')
                        status = 'Disabled' if disabled == 'true' else 'Enabled'
                        print(f"- {name} ({iface_type}) - {status}")
                    print("="*20)
                    print("1. Name")
                    print("2. Command")
                    print("3. Enable")
                    print("4. Disable")
                    print("5. Mtu")
                    print("6. Kembali")

                    pilihan1 = input("Masukkan pilihan Anda : ")

                    if pilihan1 == '1':
                            int_name()
                    elif pilihan1 == '2':
                            int_command()
                    elif pilihan1 == '3':
                            int_enable()
                    elif pilihan1 == '4':
                            int_disable()
                    elif pilihan1 == '5':
                            int_mtu()
                    elif pilihan1 == '6':
                            menu_utama()
                            break
                    else:
                        print("Pilihan tidak valid. Silakan coba lagi.")
                        input("Tekan Enter untuk kembali ke menu...")
                    
            def int_command():
                    clear_screen()
                    print("="*20)
                    print("       AmbaWin        ")
                    print("   by aww - ver 0.1   ")
                    print("="*20)
                    print("Ubah Command Interface")
                    
                    int_cm = input("ether :")
                    int_cm2 = input('Ganti Jadi apa :')
                    api.set_interface_comment(f'ether'+int_cm, int_cm2)

                    print("\n--- Mengubah Comment Interface ---")
                    input("Tekan Enter untuk kembali ke menu utama...")
                    
            def int_name():
                clear_screen()
                print("="*20)
                print("       AmbaWin        ")
                print("   by aww - ver 0.1   ")
                print("="*20)
                print("Ini adalah fungsi opsi kedua.")
                # Logika atau kode untuk opsi kedua Anda ada di sini
                input("Tekan Enter untuk kembali ke menu utama...")
                # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

            def int_enable():
                clear_screen()
                print("="*20)
                print("       AmbaWin        ")
                print("   by aww - ver 0.1   ")
                print("="*20)
                print("Ini adalah fungsi opsi kedua.")
                # Logika atau kode untuk opsi kedua Anda ada di sini
                input("Tekan Enter untuk kembali ke menu utama...")
                # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

            def int_disable():
                clear_screen()
                print("="*20)
                print("       AmbaWin        ")
                print("   by aww - ver 0.1   ")
                print("="*20)
                print("Ini adalah fungsi opsi kedua.")
                # Logika atau kode untuk opsi kedua Anda ada di sini
                input("Tekan Enter untuk kembali ke menu utama...")
                # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

            def int_mtu():
                clear_screen()
                print("="*20)
                print("       AmbaWin        ")
                print("   by aww - ver 0.1   ")
                print("="*20)
                print("Ini adalah fungsi opsi kedua.")
                # Logika atau kode untuk opsi kedua Anda ada di sini
                input("Tekan Enter untuk kembali ke menu utama...")
                # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()


            def opsi_kedua():
                clear_screen()
                print("="*20)
                print("       AmbaWin        ")
                print("   by aww - ver 0.1   ")
                print("="*20)
                print("Ini adalah fungsi opsi kedua.")
                # Logika atau kode untuk opsi kedua Anda ada di sini
                input("Tekan Enter untuk kembali ke menu utama...")
                # Setelah selesai, fungsi akan kembali ke perulangan while di menu_utama()

            # Memulai program dengan memanggil fungsi menu utama
            if __name__ == "__main__":
                menu_utama()

            #print("\n--- Mengubah Comment Interface ---")
            #int_cm = input("ether :")
                #cm1 = input("Menjadi :")
                #api.set_interface_comment(f'ether{int_cm}', cm1)
        
        api.disconnect()