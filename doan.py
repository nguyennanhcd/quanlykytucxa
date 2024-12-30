import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog

# Kết nối đến database SQLite
conn = sqlite3.connect('dormitory.db')
cursor = conn.cursor()

create_tables_query = """
-- TABLE: Users
CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: Rooms
CREATE TABLE IF NOT EXISTS Rooms (
    RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoomNumber TEXT UNIQUE NOT NULL,
    Type TEXT CHECK (Type IN ('Single', 'Double', 'Shared')) NOT NULL,
    Capacity INTEGER CHECK (Capacity > 0) NOT NULL,
    CurrentOccupants INTEGER DEFAULT 0 CHECK (CurrentOccupants >= 0 AND CurrentOccupants <= Capacity),
    Status TEXT CHECK (Status IN ('Available', 'Occupied', 'Under Maintenance')) DEFAULT 'Available',
    FloorNumber INTEGER CHECK (FloorNumber > 0),
    BuildingName TEXT NOT NULL,
    Amenities TEXT,
    Notes TEXT,
    CONSTRAINT OccupantsCapacityCheck CHECK (CurrentOccupants <= Capacity)
);

-- TABLE: Contracts
CREATE TABLE IF NOT EXISTS Contracts (
    ContractID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    ContractStatus TEXT CHECK (ContractStatus IN ('Active', 'Terminated', 'Completed', 'Pending')) DEFAULT 'Pending',
    MonthlyRent DECIMAL(10, 2) NOT NULL,
    SecurityDeposit DECIMAL(10, 2) NOT NULL,
    TermsAndConditions TEXT,
    SignedDate DATE DEFAULT CURRENT_DATE,
    RenewalOption BOOLEAN DEFAULT FALSE,
    Notes TEXT,
    CreatedByStaffID INTEGER,
    LastUpdatedByStaffID INTEGER,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastUpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (CreatedByStaffID) REFERENCES Staff(StaffID) ON DELETE SET NULL,
    FOREIGN KEY (LastUpdatedByStaffID) REFERENCES Staff(StaffID) ON DELETE SET NULL,
    CONSTRAINT EndDateCheck CHECK (EndDate > StartDate)
);

-- TABLE: Students
CREATE TABLE IF NOT EXISTS Students (
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender TEXT CHECK (Gender IN ('Male', 'Female', 'Other')),
    ContactNumber TEXT,
    Email TEXT UNIQUE NOT NULL,
    Address TEXT,
    Nationality TEXT,
    ProgramOfStudy TEXT,
    ProfilePicture TEXT,
    EmergencyContactName TEXT,
    EmergencyContactNumber TEXT,
    AdmissionDate DATE DEFAULT CURRENT_DATE,
    RoomID INTEGER,
    RoomAllocationDate DATE,
    FOREIGN KEY (RoomID) REFERENCES Rooms(RoomID) ON DELETE SET NULL,
    CONSTRAINT AllocationDateCheck CHECK (RoomAllocationDate >= AdmissionDate)
);

-- TABLE: RoomAllocationHistory
CREATE TABLE IF NOT EXISTS RoomAllocationHistory (
    AllocationID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    RoomID INTEGER,
    AllocationDate DATE NOT NULL,
    ReleaseDate DATE,
    Notes TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (RoomID) REFERENCES Rooms(RoomID) ON DELETE CASCADE,
    CONSTRAINT ReleaseDateCheck CHECK (ReleaseDate IS NULL OR ReleaseDate > AllocationDate)
);

-- TABLE: Payments
CREATE TABLE IF NOT EXISTS Payments (
    PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    ContractID INTEGER,
    Amount DECIMAL(10, 2) NOT NULL,
    LateFee DECIMAL(10, 2) DEFAULT 0.00,
    PaymentDate DATE DEFAULT CURRENT_DATE,
    Purpose TEXT CHECK (Purpose IN ('Rent', 'Utilities', 'Deposit', 'Other')) NOT NULL,
    PaymentMethod TEXT CHECK (PaymentMethod IN ('Cash', 'Card', 'Bank Transfer')) NOT NULL,
    PaymentStatus TEXT CHECK (PaymentStatus IN ('Pending', 'Completed', 'Failed')) DEFAULT 'Pending',
    ReceiptNumber TEXT UNIQUE,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (ContractID) REFERENCES Contracts(ContractID) ON DELETE SET NULL
);

-- TABLE: MaintenanceRequests
CREATE TABLE IF NOT EXISTS MaintenanceRequests (
    RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    Description TEXT NOT NULL,
    UrgencyLevel TEXT CHECK (UrgencyLevel IN ('Low', 'Medium', 'High')) DEFAULT 'Medium',
    AssignedStaffID INTEGER,
    Status TEXT CHECK (Status IN ('Pending', 'In Progress', 'Completed')) DEFAULT 'Pending',
    RequestDate DATE DEFAULT CURRENT_DATE,
    CompletionDate DATE,
    Notes TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (AssignedStaffID) REFERENCES Staff(StaffID) ON DELETE SET NULL,
    CONSTRAINT CompletionDateCheck CHECK (CompletionDate IS NULL OR CompletionDate >= RequestDate)
);

-- TABLE: Inventory
CREATE TABLE IF NOT EXISTS Inventory (
    ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
    ItemName TEXT NOT NULL,
    Quantity INTEGER CHECK (Quantity >= 0) NOT NULL,
    Location TEXT,
    Status TEXT CHECK (Status IN ('Available', 'In Use', 'Damaged', 'Lost')) DEFAULT 'Available',
    Notes TEXT
);

-- TABLE: Staff
CREATE TABLE IF NOT EXISTS Staff (
    StaffID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Role TEXT CHECK (Role IN ('Admin', 'Maintenance', 'Cleaner', 'Security')) NOT NULL,
    ContactNumber TEXT,
    Email TEXT UNIQUE NOT NULL,
    HireDate DATE DEFAULT CURRENT_DATE,
    ShiftHours TEXT,
    Salary DECIMAL(10, 2) DEFAULT 0.00,
    Notes TEXT
);

-- TABLE: Complaints
CREATE TABLE IF NOT EXISTS Complaints (
    ComplaintID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    Subject TEXT NOT NULL,
    Description TEXT NOT NULL,
    Status TEXT CHECK (Status IN ('Pending', 'Resolved', 'Dismissed')) DEFAULT 'Pending',
    ComplaintDate DATE DEFAULT CURRENT_DATE,
    ResolutionDate DATE,
    Notes TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    CONSTRAINT ResolutionDateCheck CHECK (ResolutionDate IS NULL OR ResolutionDate >= ComplaintDate)
);

-- TABLE: FinesAndPenalties
CREATE TABLE IF NOT EXISTS FinesAndPenalties (
    FineID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    ViolationType TEXT CHECK (ViolationType IN ('Noise', 'Late Payment', 'Damage', 'Other')) NOT NULL,
    Description TEXT NOT NULL,
    FineAmount DECIMAL(10, 2) CHECK (FineAmount > 0) NOT NULL,
    FineDate DATE DEFAULT CURRENT_DATE,
    Status TEXT CHECK (Status IN ('Unpaid', 'Paid')) DEFAULT 'Unpaid',
    Notes TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE
);

-- TABLE: StudentFines
CREATE TABLE IF NOT EXISTS StudentFines (
    StudentID INTEGER,
    FineID INTEGER,
    IssuedDate DATE DEFAULT CURRENT_DATE,
    Status TEXT CHECK (Status IN ('Unpaid', 'Paid', 'Waived')) DEFAULT 'Unpaid',
    Notes TEXT,
    PRIMARY KEY (StudentID, FineID),
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (FineID) REFERENCES FinesAndPenalties(FineID) ON DELETE CASCADE
);
"""

cursor.executescript(create_tables_query)
conn.commit()

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

        def load_students():
            for row in student_tree.get_children():
                student_tree.delete(row)
            cursor.execute('SELECT * FROM Students')
            for student in cursor.fetchall():
                student_tree.insert('', tk.END, values=student)

        def add_student():
            first_name = entry_first_name.get()
            last_name = entry_last_name.get()
            dob = entry_dob.get()
            gender = gender_var.get()
            contact = entry_contact.get()
            email = entry_email.get()
            address = entry_address.get()
            nationality = entry_nationality.get()
            program = entry_program.get()
            profile_picture = entry_profile_picture.get()
            emergency_name = entry_emergency_name.get()
            emergency_contact = entry_emergency_contact.get()
            admission_date = entry_admission_date.get()
            room_id = entry_room_id.get()
            room_allocation_date = entry_room_allocation_date.get()

            if first_name and last_name and dob and email:
                try:
                    cursor.execute('''INSERT INTO Students (
                        FirstName, LastName, DateOfBirth, Gender, ContactNumber, Email, Address, Nationality,
                        ProgramOfStudy, ProfilePicture, EmergencyContactName, EmergencyContactNumber, AdmissionDate,
                        RoomID, RoomAllocationDate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (first_name, last_name, dob, gender, contact, email, address, nationality, program, profile_picture,
                         emergency_name, emergency_contact, admission_date, room_id, room_allocation_date))
                    conn.commit()
                    load_students()
                    messagebox.showinfo("Thành công", "Thêm sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")


        def update_student():
            selected_item = student_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn sinh viên", "Vui lòng chọn sinh viên để sửa.")
                return

            student_id = student_tree.item(selected_item)['values'][0]
            first_name = entry_first_name.get()
            last_name = entry_last_name.get()
            dob = entry_dob.get()
            gender = gender_var.get()
            contact = entry_contact.get()
            email = entry_email.get()
            address = entry_address.get()
            nationality = entry_nationality.get()
            program = entry_program.get()
            profile_picture = entry_profile_picture.get()
            emergency_name = entry_emergency_name.get()
            emergency_contact = entry_emergency_contact.get()
            admission_date = entry_admission_date.get()
            room_id = entry_room_id.get()
            room_allocation_date = entry_room_allocation_date.get()

            if first_name and last_name and dob and email:
                try:
                    cursor.execute('''UPDATE Students SET
                        FirstName = ?, LastName = ?, DateOfBirth = ?, Gender = ?, ContactNumber = ?, Email = ?, 
                        Address = ?, Nationality = ?, ProgramOfStudy = ?, ProfilePicture = ?, EmergencyContactName = ?, 
                        EmergencyContactNumber = ?, AdmissionDate = ?, RoomID = ?, RoomAllocationDate = ?
                        WHERE StudentID = ?''', 
                        (first_name, last_name, dob, gender, contact, email, address, nationality, program, profile_picture,
                        emergency_name, emergency_contact, admission_date, room_id, room_allocation_date, student_id))
                    conn.commit()
                    load_students()
                    messagebox.showinfo("Thành công", "Cập nhật sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")


        def delete_student():
            selected_item = student_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn sinh viên", "Vui lòng chọn sinh viên để xóa.")
                return

            student_id = student_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa sinh viên này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Students WHERE StudentID = ?', (student_id,))
                    conn.commit()
                    load_students()
                    messagebox.showinfo("Thành công", "Xóa sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        def upload_picture():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                entry_profile_picture.delete(0, tk.END)
                entry_profile_picture.insert(0, file_path)

        tk.Label(content_frame, text="Quản lý sinh viên", font=("Arial", 16)).pack(pady=10)

        form_frame = tk.Frame(content_frame)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Họ").grid(row=0, column=0, padx=5, pady=5)
        entry_first_name = tk.Entry(form_frame)
        entry_first_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Tên").grid(row=0, column=2, padx=5, pady=5)
        entry_last_name = tk.Entry(form_frame)
        entry_last_name.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngày sinh (YYYY-MM-DD)").grid(row=1, column=0, padx=5, pady=5)
        entry_dob = tk.Entry(form_frame)
        entry_dob.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Giới tính").grid(row=1, column=2, padx=5, pady=5)
        gender_var = tk.StringVar()
        gender_var.set("Other")
        tk.OptionMenu(form_frame, gender_var, "Male", "Female", "Other").grid(row=1, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Số liên lạc").grid(row=2, column=0, padx=5, pady=5)
        entry_contact = tk.Entry(form_frame)
        entry_contact.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Email").grid(row=2, column=2, padx=5, pady=5)
        entry_email = tk.Entry(form_frame)
        entry_email.grid(row=2, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Địa chỉ").grid(row=3, column=0, padx=5, pady=5)
        entry_address = tk.Entry(form_frame)
        entry_address.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Quốc tịch").grid(row=3, column=2, padx=5, pady=5)
        entry_nationality = tk.Entry(form_frame)
        entry_nationality.grid(row=3, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngành học").grid(row=4, column=0, padx=5, pady=5)
        entry_program = tk.Entry(form_frame)
        entry_program.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Hình đại diện").grid(row=4, column=2, padx=5, pady=5)
        entry_profile_picture = tk.Entry(form_frame)
        entry_profile_picture.grid(row=4, column=3, padx=5, pady=5)
        tk.Button(form_frame, text="Tải lên", command=upload_picture).grid(row=4, column=4, padx=5, pady=5)

        tk.Label(form_frame, text="Tên liên hệ khẩn cấp").grid(row=5, column=0, padx=5, pady=5)
        entry_emergency_name = tk.Entry(form_frame)
        entry_emergency_name.grid(row=5, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Số liên hệ khẩn cấp").grid(row=5, column=2, padx=5, pady=5)
        entry_emergency_contact = tk.Entry(form_frame)
        entry_emergency_contact.grid(row=5, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngày nhập học (YYYY-MM-DD)").grid(row=6, column=0, padx=5, pady=5)
        entry_admission_date = tk.Entry(form_frame)
        entry_admission_date.grid(row=6, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="ID phòng").grid(row=6, column=2, padx=5, pady=5)
        entry_room_id = tk.Entry(form_frame)
        entry_room_id.grid(row=6, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngày phân phòng (YYYY-MM-DD)").grid(row=7, column=0, padx=5, pady=5)
        entry_room_allocation_date = tk.Entry(form_frame)
        entry_room_allocation_date.grid(row=7, column=1, padx=5, pady=5)

        button_frame = tk.Frame(content_frame)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm", command=add_student).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cập nhật", command=update_student).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Xóa", command=delete_student).pack(side=tk.LEFT, padx=5)

        student_tree = ttk.Treeview(content_frame, columns=(
            "StudentID", "FirstName", "LastName", "DateOfBirth", "Gender", "ContactNumber", "Email",
            "Address", "Nationality", "ProgramOfStudy", "ProfilePicture", "EmergencyContactName",
            "EmergencyContactNumber", "AdmissionDate", "RoomID", "RoomAllocationDate"
        ), show='headings')

        for col in student_tree['columns']:
            student_tree.heading(col, text=col)
            student_tree.column(col, width=100)

        student_tree.pack(pady=10, fill=tk.BOTH, expand=True)

        load_students()

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
    root.geometry("1000x600")

    # Tạo thanh navbar bên trái
    navbar = tk.Frame(root, bg="#2c3e50", width=200, height=600)
    navbar.pack(side=tk.LEFT, fill=tk.Y)

    tk.Button(navbar, text="Sinh viên", command=show_students, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Hợp đồng", command=show_contracts, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Nhân viên", command=show_staff, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)
    tk.Button(navbar, text="Phòng ở", command=show_room, width=20, pady=10, bg="#34495e", fg="white").pack(pady=5)

    # Tạo frame nội dung
    content_frame = tk.Frame(root, bg="#ecf0f1", width=800, height=600)
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


tk.Button(login_window, text="Đăng nhập", command=login_user).pack(pady=10)
tk.Button(login_window, text="Đăng ký", command=register_user).pack(pady=10)

login_window.mainloop()


conn.close()
