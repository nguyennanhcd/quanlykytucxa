import sqlite3
import tkinter as tk
from tkinter import messagebox

# Kết nối đến database SQLite
conn = sqlite3.connect('dormitory.db')
cursor = conn.cursor()

# Đăng ký người dùng
def register_user():
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        try:
            cursor.execute('INSERT INTO Users (Username, Password) VALUES (?, ?)', (username, password))
            conn.commit()
            messagebox.showinfo("Thành công", "Đăng ký thành công!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại.")
    else:
        messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin.")

# Đăng nhập người dùng
def login_user():
    username = entry_username.get()
    password = entry_password.get()

    cursor.execute('SELECT * FROM Users WHERE Username = ? AND Password = ?', (username, password))
    user = cursor.fetchone()

    if user:
        messagebox.showinfo("Thành công", "Đăng nhập thành công!")
        open_main_app()
    else:
        messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.")

# Mở ứng dụng chính sau khi đăng nhập
def open_main_app():
    login_window.destroy()

    # Hàm hiển thị trang sinh viên
    def show_students():
        clear_frame(content_frame)
        tk.Label(content_frame, text="Quản lý sinh viên", font=("Arial", 16)).pack(pady=10)

    # Hàm hiển thị trang hợp đồng
    def show_contracts():
        clear_frame(content_frame)
        tk.Label(content_frame, text="Quản lý hợp đồng", font=("Arial", 16)).pack(pady=10)

    # Hàm hiển thị trang nhân viên
    def show_staff():
        clear_frame(content_frame)
        tk.Label(content_frame, text="Quản lý nhân viên", font=("Arial", 16)).pack(pady=10)

    # Hàm hiển thị trang phòng ở
    def show_room():
        clear_frame(content_frame)
        tk.Label(content_frame, text="Quản lý phòng ở", font=("Arial", 16)).pack(pady=10)

    # Hàm xoá nội dung trong frame
    def clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # Giao diện chính
    root = tk.Tk()
    root.title("Quản lý ký túc xá")
    root.geometry("800x500")

    # Tạo thanh navbar bên trái
    navbar = tk.Frame(root, bg="#2c3e50", width=200, height=500)
    navbar.pack(side=tk.LEFT, fill=tk.Y)

    tk.Button(navbar, text="Sinh viên", command=show_students, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Hợp đồng", command=show_contracts, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Nhân viên", command=show_staff, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Phòng ở", command=show_room, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)




    # Tạo frame nội dung
    content_frame = tk.Frame(root, bg="#ecf0f1", width=600, height=500)
    content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    root.mainloop()

# Tạo cửa sổ đăng nhập
login_window = tk.Tk()
login_window.title("Đăng nhập")
login_window.geometry("400x300")

# Nhãn và ô nhập liệu đăng nhập
tk.Label(login_window, text="Tên đăng nhập").pack(pady=5)
entry_username = tk.Entry(login_window)
entry_username.pack(pady=5)

tk.Label(login_window, text="Mật khẩu").pack(pady=5)
entry_password = tk.Entry(login_window, show="*")
entry_password.pack(pady=5)

# Nút chức năng
tk.Button(login_window, text="Đăng nhập", command=login_user).pack(pady=10)
tk.Button(login_window, text="Đăng ký", command=register_user).pack(pady=10)

login_window.mainloop()

# Đóng kết nối database khi thoát chương trình
conn.close()
