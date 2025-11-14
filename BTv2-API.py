import socket
import hashlib
import binascii

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
    nama1 = input("IP HOST :")
    
    # Menampilkan sapaan dan nama pengguna
    
    #print("HOST, " + nama1 + "!")

    nama2 = input("USERNAME :")
    #print("HOST, " + nama1 + "!")

    nama3 = input("PASSWORD :")
    #print("HOST, " + nama3 + "!")

    HOST = nama1  # Ganti dengan IP Mikrotik Anda
    PORT = 8728
    USERNAME = nama2      # Ganti dengan username Anda
    PASSWORD = nama3      # Ganti dengan password Anda
    
    # Buat instance dan koneksi
    api = MikrotikAPI(HOST, PORT)
    
    if api.connect():
        if api.login(USERNAME, PASSWORD):
            # Contoh: Mengambil informasi sistem
            #print("\n--- Informasi Sistem ---")
            #response = api.talk('/system/resource/print')
            #for sentence in response:
            #    for word in sentence:
            #        print(word)
            
            # Contoh: Mengambil daftar interface dengan format yang lebih rapi
            #print("\n--- Daftar Interface ---")
            #interfaces = api.get_interfaces()
            #for iface in interfaces:
            #    name = iface.get('name', 'N/A')
            #    iface_type = iface.get('type', 'N/A')
            #    disabled = iface.get('disabled', 'false')
            #    status = 'Disabled' if disabled == 'true' else 'Enabled'
            #    print(f"- {name} ({iface_type}) - {status}")
            
            # Contoh: Mengubah nama interface
            #print("\n--- Mengubah Nama Interface ---")
            # Uncomment untuk mengubah nama interface
            # api.rename_interface('ether1', 'WAN')
            # api.rename_interface('ether2', 'LAN-1')
            # api.rename_interface('ether3', 'LAN-2')
            
            # Contoh: Mengubah comment interface
            print("\n--- Mengubah Comment Interface ---")
            api.set_interface_comment('ether1', 'Koneksi Internet')
            
            # Contoh: Disable interface
            #print("\n--- Disable Interface ---")
            # api.enable_disable_interface('ether5', enable=False)
            
            # Contoh: Enable interface
            #print("\n--- Enable Interface ---")
            # api.enable_disable_interface('ether5', enable=True)
        
        api.disconnect()