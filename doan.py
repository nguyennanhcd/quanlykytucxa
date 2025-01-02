import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import re
from datetime import datetime

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

# Biến để lưu trữ nút hiện tại
current_button = None

def on_button_click(button):
    global current_button
    if current_button:
        current_button.config(bg="#34495e")  # Đặt lại màu cho nút trước đó
    button.config(bg="#eb6a81")  # Đổi màu cho nút hiện tại
    current_button = button


# Hàm kiểm tra email hợp lệ
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Hàm kiểm tra số điện thoại hợp lệ
def is_valid_phone(phone):
    pattern = r'^\d{10,11}$'
    return re.match(pattern, phone) is not None

# Hàm kiểm tra ngày sinh hợp lệ
def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, '%d-%m-%Y')
        return True
    except ValueError:
        return False

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
        on_button_click(btn_students)
        clear_frame(content_frame)

        def load_students():
            for row in student_tree.get_children():
                student_tree.delete(row)
            cursor.execute('SELECT * FROM Students')
            for student in cursor.fetchall():
                student_tree.insert('', tk.END, values=student)

        def search_students():
            search_term = entry_search.get()
            for row in student_tree.get_children():
                student_tree.delete(row)
            cursor.execute('SELECT * FROM Students WHERE StudentID LIKE ? OR FirstName LIKE ? OR LastName LIKE ?', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
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

            if not is_valid_email(email):
                messagebox.showerror("Lỗi", "Email không hợp lệ.")
                return

            if not is_valid_phone(contact):
                messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ.")
                return

            if not is_valid_date(dob):
                messagebox.showerror("Lỗi", "Ngày sinh không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

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

            if not is_valid_email(email):
                messagebox.showerror("Lỗi", "Email không hợp lệ.")
                return

            if not is_valid_phone(contact):
                messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ.")
                return

            if not is_valid_date(dob):
                messagebox.showerror("Lỗi", "Ngày sinh không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

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

        tk.Label(content_frame, text="Quản lý sinh viên", font=("Helvetica", 16)).pack(pady=10)

        search_frame = tk.Frame(content_frame)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_students).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Họ").grid(row=0, column=0, padx=5, pady=5)
        entry_first_name = tk.Entry(form_frame)
        entry_first_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Tên").grid(row=0, column=2, padx=5, pady=5)
        entry_last_name = tk.Entry(form_frame)
        entry_last_name.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngày sinh (DD-MM-YYYY)").grid(row=1, column=0, padx=5, pady=5)
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

        tk.Label(form_frame, text="Ngày nhập học (DD-MM-YYYY)").grid(row=6, column=0, padx=5, pady=5)
        entry_admission_date = tk.Entry(form_frame)
        entry_admission_date.grid(row=6, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="ID phòng").grid(row=6, column=2, padx=5, pady=5)
        entry_room_id = tk.Entry(form_frame)
        entry_room_id.grid(row=6, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Ngày phân phòng (DD-MM-YYYY)").grid(row=7, column=0, padx=5, pady=5)
        entry_room_allocation_date = tk.Entry(form_frame)
        entry_room_allocation_date.grid(row=7, column=1, padx=5, pady=5)

        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm sinh viên", bg="#8BC34A", fg="white", command=add_student).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa thông tin", bg="#FFA500", fg="white", command=update_student).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa sinh viên", bg="#FF6347", fg="white", command=delete_student).grid(row=0, column=2, padx=10)

        column_mapping = {
            "StudentID": "Mã sinh viên",
            "FirstName": "Tên",
            "LastName": "Họ",
            "DateOfBirth": "Ngày sinh",
            "Gender": "Giới tính",
            "ContactNumber": "Số điện thoại",
            "Email": "Email",
            "Address": "Địa chỉ",
            "Nationality": "Quốc tịch",
            "ProgramOfStudy": "Chương trình học",
            "ProfilePicture": "Ảnh đại diện",
            "EmergencyContactName": "Tên liên hệ khẩn cấp",
            "EmergencyContactNumber": "Số liên hệ khẩn cấp",
            "AdmissionDate": "Ngày nhập học",
            "RoomID": "Mã phòng",
            "RoomAllocationDate": "Ngày phân phòng"
        }

        student_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        student_tree.pack(pady=10, fill=tk.BOTH, expand=True)

        for col in student_tree['columns']:
            student_tree.heading(col, text=column_mapping[col])
            student_tree.column(col, width=100)

        load_students()
    
    # Hàm hiển thị trang hợp đồng
    def show_contracts():
        on_button_click(btn_contracts)
        clear_frame(content_frame)

        def load_contracts():
            for row in contract_tree.get_children():
                contract_tree.delete(row)
            cursor.execute('SELECT * FROM Contracts')
            for contract in cursor.fetchall():
                contract_tree.insert('', tk.END, values=contract)

        def search_contracts():
            search_term = entry_search.get()
            for row in contract_tree.get_children():
                contract_tree.delete(row)
            cursor.execute('SELECT * FROM Contracts WHERE ContractID LIKE ? OR StudentID LIKE ? OR StartDate LIKE ? OR EndDate LIKE ?', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for contract in cursor.fetchall():
                contract_tree.insert('', tk.END, values=contract)

        def add_contract():
            student_id = entry_student_id.get()
            start_date = entry_start_date.get()
            end_date = entry_end_date.get()
            contract_status = contract_status_var.get()
            monthly_rent = entry_monthly_rent.get()
            security_deposit = entry_security_deposit.get()
            terms_and_conditions = entry_terms_and_conditions.get()
            signed_date = entry_signed_date.get()
            renewal_option = entry_renewal_option.get()
            notes = entry_notes.get()
            created_by_staff_id = entry_created_by_staff_id.get()
            last_updated_by_staff_id = entry_last_updated_by_staff_id.get()

            if not is_valid_date(start_date) or not is_valid_date(end_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and start_date and end_date and monthly_rent and security_deposit:
                try:
                    cursor.execute('''INSERT INTO Contracts (
                        StudentID, StartDate, EndDate, ContractStatus, MonthlyRent, SecurityDeposit, TermsAndConditions,
                        SignedDate, RenewalOption, Notes, CreatedByStaffID, LastUpdatedByStaffID
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, start_date, end_date, contract_status, monthly_rent, security_deposit, terms_and_conditions,
                        signed_date, renewal_option, notes, created_by_staff_id, last_updated_by_staff_id))
                    conn.commit()
                    load_contracts()
                    messagebox.showinfo("Thành công", "Thêm hợp đồng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_contract():
            selected_item = contract_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn hợp đồng", "Vui lòng chọn hợp đồng để sửa.")
                return

            contract_id = contract_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            start_date = entry_start_date.get()
            end_date = entry_end_date.get()
            contract_status = contract_status_var.get()
            monthly_rent = entry_monthly_rent.get()
            security_deposit = entry_security_deposit.get()
            terms_and_conditions = entry_terms_and_conditions.get()
            signed_date = entry_signed_date.get()
            renewal_option = entry_renewal_option.get()
            notes = entry_notes.get()
            created_by_staff_id = entry_created_by_staff_id.get()
            last_updated_by_staff_id = entry_last_updated_by_staff_id.get()

            if not is_valid_date(start_date) or not is_valid_date(end_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and start_date and end_date and monthly_rent and security_deposit:
                try:
                    cursor.execute('''UPDATE Contracts SET
                        StudentID = ?, StartDate = ?, EndDate = ?, ContractStatus = ?, MonthlyRent = ?, SecurityDeposit = ?,
                        TermsAndConditions = ?, SignedDate = ?, RenewalOption = ?, Notes = ?, CreatedByStaffID = ?, LastUpdatedByStaffID = ?
                        WHERE ContractID = ?''',
                        (student_id, start_date, end_date, contract_status, monthly_rent, security_deposit, terms_and_conditions,
                        signed_date, renewal_option, notes, created_by_staff_id, last_updated_by_staff_id, contract_id))
                    conn.commit()
                    load_contracts()
                    messagebox.showinfo("Thành công", "Cập nhật hợp đồng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_contract():
            selected_item = contract_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn hợp đồng", "Vui lòng chọn hợp đồng để xóa.")
                return

            contract_id = contract_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa hợp đồng này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Contracts WHERE ContractID = ?', (contract_id,))
                    conn.commit()
                    load_contracts()
                    messagebox.showinfo("Thành công", "Xóa hợp đồng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý hợp đồng", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_contracts).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày bắt đầu:").grid(row=1, column=0, padx=5, pady=10)
        entry_start_date = tk.Entry(form_frame)
        entry_start_date.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày kết thúc:").grid(row=2, column=0, padx=5, pady=10)
        entry_end_date = tk.Entry(form_frame)
        entry_end_date.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Trạng thái hợp đồng:").grid(row=3, column=0, padx=5, pady=10)
        contract_status_var = tk.StringVar()
        contract_status_var.set("Pending")
        tk.OptionMenu(form_frame, contract_status_var, "Active", "Terminated", "Completed", "Pending").grid(row=3, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Tiền thuê hàng tháng:").grid(row=4, column=0, padx=5, pady=10)
        entry_monthly_rent = tk.Entry(form_frame)
        entry_monthly_rent.grid(row=4, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Tiền đặt cọc:").grid(row=5, column=0, padx=5, pady=10)
        entry_security_deposit = tk.Entry(form_frame)
        entry_security_deposit.grid(row=5, column=1, padx=5, pady=10)

        # Khung tạo khoảng cách giữa hai cột
        tk.Frame(form_frame, width=20, bg="#f0f0f0").grid(row=0, column=2, rowspan=6)

        # Cột 2
        tk.Label(form_frame, text="Điều khoản và điều kiện:").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_terms_and_conditions = tk.Entry(form_frame)
        entry_terms_and_conditions.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày ký:").grid(row=1, column=2, padx=(20, 5), pady=10)
        entry_signed_date = tk.Entry(form_frame)
        entry_signed_date.grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Tùy chọn gia hạn:").grid(row=2, column=2, padx=(20, 5), pady=10)
        entry_renewal_option = tk.Entry(form_frame)
        entry_renewal_option.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=3, column=2, padx=(20, 5), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=3, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Mã nhân viên tạo:").grid(row=4, column=2, padx=(20, 5), pady=10)
        entry_created_by_staff_id = tk.Entry(form_frame)
        entry_created_by_staff_id.grid(row=4, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Mã nhân viên cập nhật:").grid(row=5, column=2, padx=(20, 5), pady=10)
        entry_last_updated_by_staff_id = tk.Entry(form_frame)
        entry_last_updated_by_staff_id.grid(row=5, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Tạo hợp đồng", bg="#8BC34A", fg="white", command=add_contract).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa hợp đồng", bg="#FFA500", fg="white", command=update_contract).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa hợp đồng", bg="#FF6347", fg="white", command=delete_contract).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "ContractID": "Mã hợp đồng",
            "StudentID": "Mã sinh viên",
            "StartDate": "Ngày bắt đầu",
            "EndDate": "Ngày kết thúc",
            "ContractStatus": "Trạng thái hợp đồng",
            "MonthlyRent": "Tiền thuê hàng tháng",
            "SecurityDeposit": "Tiền đặt cọc",
            "TermsAndConditions": "Điều khoản và điều kiện",
            "SignedDate": "Ngày ký",
            "RenewalOption": "Tùy chọn gia hạn",
            "Notes": "Ghi chú",
            "CreatedByStaffID": "Mã nhân viên tạo",
            "LastUpdatedByStaffID": "Mã nhân viên cập nhật",
            "CreatedAt": "Ngày tạo",
            "LastUpdatedAt": "Ngày cập nhật"
        }

        contract_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        contract_tree.pack(fill=tk.BOTH, expand=True)

        for col in contract_tree["columns"]:
            contract_tree.heading(col, text=column_mapping[col])
            contract_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_contracts()
    
    # Hàm hiển thị trang nhân viên
    def show_staff():
        on_button_click(btn_staff)
        clear_frame(content_frame)

        def load_staff():
            for row in staff_tree.get_children():
                staff_tree.delete(row)
            cursor.execute('SELECT * FROM Staff')
            for staff in cursor.fetchall():
                staff_tree.insert('', tk.END, values=staff)

        def search_staff():
            search_term = entry_search.get()
            for row in staff_tree.get_children():
                staff_tree.delete(row)
            cursor.execute('SELECT * FROM Staff WHERE StaffID LIKE ? OR Name LIKE ? OR Position LIKE ? OR Department LIKE ? OR Phone LIKE ?', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for staff in cursor.fetchall():
                staff_tree.insert('', tk.END, values=staff)

        def add_staff():
            staff_id = entry_staff_id.get()
            name = entry_name.get()
            position = entry_position.get()
            department = entry_department.get()
            phone = entry_phone.get()
            email = entry_email.get()
            address = entry_address.get()
            hire_date = entry_hire_date.get()
            notes = entry_notes.get()

            if not is_valid_date(hire_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if staff_id and name and position and department and phone:
                try:
                    cursor.execute('''INSERT INTO Staff (
                        StaffID, Name, Position, Department, Phone, Email, Address, HireDate, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (staff_id, name, position, department, phone, email, address, hire_date, notes))
                    conn.commit()
                    load_staff()
                    messagebox.showinfo("Thành công", "Thêm nhân viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_staff():
            selected_item = staff_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn nhân viên", "Vui lòng chọn nhân viên để sửa.")
                return

            staff_id = staff_tree.item(selected_item)['values'][0]
            name = entry_name.get()
            position = entry_position.get()
            department = entry_department.get()
            phone = entry_phone.get()
            email = entry_email.get()
            address = entry_address.get()
            hire_date = entry_hire_date.get()
            notes = entry_notes.get()

            if not is_valid_date(hire_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if staff_id and name and position and department and phone:
                try:
                    cursor.execute('''UPDATE Staff SET
                        Name = ?, Position = ?, Department = ?, Phone = ?, Email = ?, Address = ?, HireDate = ?, Notes = ?
                        WHERE StaffID = ?''',
                        (name, position, department, phone, email, address, hire_date, notes, staff_id))
                    conn.commit()
                    load_staff()
                    messagebox.showinfo("Thành công", "Cập nhật nhân viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_staff():
            selected_item = staff_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn nhân viên", "Vui lòng chọn nhân viên để xóa.")
                return

            staff_id = staff_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa nhân viên này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Staff WHERE StaffID = ?', (staff_id,))
                    conn.commit()
                    load_staff()
                    messagebox.showinfo("Thành công", "Xóa nhân viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý nhân viên", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_staff).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã nhân viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_staff_id = tk.Entry(form_frame)
        entry_staff_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Tên:").grid(row=1, column=0, padx=5, pady=10)
        entry_name = tk.Entry(form_frame)
        entry_name.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Chức vụ:").grid(row=2, column=0, padx=5, pady=10)
        entry_position = tk.Entry(form_frame)
        entry_position.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Phòng ban:").grid(row=3, column=0, padx=5, pady=10)
        entry_department = tk.Entry(form_frame)
        entry_department.grid(row=3, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Số điện thoại:").grid(row=4, column=0, padx=5, pady=10)
        entry_phone = tk.Entry(form_frame)
        entry_phone.grid(row=4, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Email:").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_email = tk.Entry(form_frame)
        entry_email.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Địa chỉ:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_address = tk.Entry(form_frame)
        entry_address.grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày thuê (DD-MM-YYYY):").grid(row=2, column=2, padx=(30, 10), pady=10)
        entry_hire_date = tk.Entry(form_frame)
        entry_hire_date.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm nhân viên", bg="#8BC34A", fg="white", command=add_staff).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa nhân viên", bg="#FFA500", fg="white", command=update_staff).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa nhân viên", bg="#FF6347", fg="white", command=delete_staff).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "StaffID": "Mã nhân viên",
            "Name": "Tên",
            "Position": "Chức vụ",
            "Department": "Phòng ban",
            "Phone": "Số điện thoại",
            "Email": "Email",
            "Address": "Địa chỉ",
            "HireDate": "Ngày thuê",
            "Notes": "Ghi chú"
        }

        staff_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        staff_tree.pack(fill=tk.BOTH, expand=True)

        for col in staff_tree["columns"]:
            staff_tree.heading(col, text=column_mapping[col])
            staff_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_staff()
    
    # Hàm hiển thị trang phòng ở
    def show_room():
        on_button_click(btn_room)
        clear_frame(content_frame)

        def load_rooms():
            for row in room_tree.get_children():
                room_tree.delete(row)
            cursor.execute('SELECT * FROM Rooms')
            for room in cursor.fetchall():
                room_tree.insert('', tk.END, values=room)

        def search_rooms():
            search_term = entry_search.get()
            for row in room_tree.get_children():
                room_tree.delete(row)
            cursor.execute('''SELECT * FROM Rooms WHERE RoomNumber LIKE ? OR Type LIKE ? OR Capacity LIKE ? OR CurrentOccupants LIKE ? 
                            OR Status LIKE ? OR FloorNumber LIKE ? OR BuildingName LIKE ? OR Amenities LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', 
                            '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for room in cursor.fetchall():
                room_tree.insert('', tk.END, values=room)

        def add_room():
            room_number = entry_room_number.get()
            room_type = room_type_var.get()
            capacity = entry_capacity.get()
            current_occupants = entry_current_occupants.get()
            status = status_var.get()
            floor_number = entry_floor_number.get()
            building_name = entry_building_name.get()
            amenities = entry_amenities.get()
            notes = entry_notes.get()

            if room_number and room_type and capacity and floor_number and building_name:
                try:
                    cursor.execute('''INSERT INTO Rooms (
                        RoomNumber, Type, Capacity, CurrentOccupants, Status, FloorNumber, BuildingName, Amenities, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (room_number, room_type, capacity, current_occupants, status, floor_number, building_name, amenities, notes))
                    conn.commit()
                    load_rooms()
                    messagebox.showinfo("Thành công", "Thêm phòng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_room():
            selected_item = room_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phòng", "Vui lòng chọn phòng để sửa.")
                return

            room_id = room_tree.item(selected_item)['values'][0]
            room_number = entry_room_number.get()
            room_type = room_type_var.get()
            capacity = entry_capacity.get()
            current_occupants = entry_current_occupants.get()
            status = status_var.get()
            floor_number = entry_floor_number.get()
            building_name = entry_building_name.get()
            amenities = entry_amenities.get()
            notes = entry_notes.get()

            if room_number and room_type and capacity and floor_number and building_name:
                try:
                    cursor.execute('''UPDATE Rooms SET
                        RoomNumber = ?, Type = ?, Capacity = ?, CurrentOccupants = ?, Status = ?, FloorNumber = ?, BuildingName = ?, Amenities = ?, Notes = ?
                        WHERE RoomID = ?''',
                        (room_number, room_type, capacity, current_occupants, status, floor_number, building_name, amenities, notes, room_id))
                    conn.commit()
                    load_rooms()
                    messagebox.showinfo("Thành công", "Cập nhật phòng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_room():
            selected_item = room_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phòng", "Vui lòng chọn phòng để xóa.")
                return

            room_id = room_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa phòng này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Rooms WHERE RoomID = ?', (room_id,))
                    conn.commit()
                    load_rooms()
                    messagebox.showinfo("Thành công", "Xóa phòng thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý phòng ở", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_rooms).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Số phòng:").grid(row=0, column=0, padx=5, pady=10)
        entry_room_number = tk.Entry(form_frame)
        entry_room_number.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Loại phòng:").grid(row=1, column=0, padx=5, pady=10)
        room_type_var = tk.StringVar()
        room_type_var.set("Single")
        tk.OptionMenu(form_frame, room_type_var, "Single", "Double", "Shared").grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Sức chứa:").grid(row=2, column=0, padx=5, pady=10)
        entry_capacity = tk.Entry(form_frame)
        entry_capacity.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Số người hiện tại:").grid(row=3, column=0, padx=5, pady=10)
        entry_current_occupants = tk.Entry(form_frame)
        entry_current_occupants.grid(row=3, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Trạng thái:").grid(row=4, column=0, padx=5, pady=10)
        status_var = tk.StringVar()
        status_var.set("Available")
        tk.OptionMenu(form_frame, status_var, "Available", "Occupied", "Under Maintenance").grid(row=4, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Số tầng:").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_floor_number = tk.Entry(form_frame)
        entry_floor_number.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Tên tòa nhà:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_building_name = tk.Entry(form_frame)
        entry_building_name.grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Tiện nghi:").grid(row=2, column=2, padx=(30, 10), pady=10)
        entry_amenities = tk.Entry(form_frame)
        entry_amenities.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm phòng", bg="#8BC34A", fg="white", command=add_room).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa thông tin", bg="#FFA500", fg="white", command=update_room).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa phòng", bg="#FF6347", fg="white", command=delete_room).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "RoomID": "Mã phòng",
            "RoomNumber": "Số phòng",
            "Type": "Loại phòng",
            "Capacity": "Sức chứa",
            "CurrentOccupants": "Số người hiện tại",
            "Status": "Trạng thái",
            "FloorNumber": "Số tầng",
            "BuildingName": "Tên tòa nhà",
            "Amenities": "Tiện nghi",
            "Notes": "Ghi chú"
        }

        room_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        room_tree.pack(fill=tk.BOTH, expand=True)

        for col in room_tree["columns"]:
            room_tree.heading(col, text=column_mapping[col])
            room_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_rooms()

    # Hàm hiển thị trang lịch sử phân phòng
    def show_room_allocation_history():
        on_button_click(btn_room_allocation_history)
        clear_frame(content_frame)

        def load_room_allocations():
            for row in allocation_tree.get_children():
                allocation_tree.delete(row)
            cursor.execute('SELECT * FROM RoomAllocationHistory')
            for allocation in cursor.fetchall():
                allocation_tree.insert('', tk.END, values=allocation)

        def search_allocations():
            search_term = entry_search.get()
            for row in allocation_tree.get_children():
                allocation_tree.delete(row)
            cursor.execute('''SELECT * FROM RoomAllocationHistory WHERE StudentID LIKE ? OR RoomID LIKE ? OR AllocationDate LIKE ? OR ReleaseDate LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for allocation in cursor.fetchall():
                allocation_tree.insert('', tk.END, values=allocation)

        def add_allocation():
            student_id = entry_student_id.get()
            room_id = entry_room_id.get()
            allocation_date = entry_allocation_date.get()
            release_date = entry_release_date.get()
            notes = entry_notes.get()

            if not is_valid_date(allocation_date) or (release_date and not is_valid_date(release_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and room_id and allocation_date:
                try:
                    cursor.execute('''INSERT INTO RoomAllocationHistory (
                        StudentID, RoomID, AllocationDate, ReleaseDate, Notes
                    ) VALUES (?, ?, ?, ?, ?)''',
                        (student_id, room_id, allocation_date, release_date, notes))
                    conn.commit()
                    load_room_allocations()
                    messagebox.showinfo("Thành công", "Thêm phân phòng thành công.")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể thêm phân phòng: {e}")

        def update_allocation():
            selected_item = allocation_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phân phòng", "Vui lòng chọn phân phòng để sửa.")
                return

            allocation_id = allocation_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            room_id = entry_room_id.get()
            allocation_date = entry_allocation_date.get()
            release_date = entry_release_date.get()
            notes = entry_notes.get()

            if not is_valid_date(allocation_date) or (release_date and not is_valid_date(release_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and room_id and allocation_date:
                try:
                    cursor.execute('''UPDATE RoomAllocationHistory SET
                        StudentID = ?, RoomID = ?, AllocationDate = ?, ReleaseDate = ?, Notes = ?
                        WHERE AllocationID = ?''',
                        (student_id, room_id, allocation_date, release_date, notes, allocation_id))
                    conn.commit()
                    load_room_allocations()
                    messagebox.showinfo("Thành công", "Cập nhật phân phòng thành công.")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể cập nhật phân phòng: {e}")

        def delete_allocation():
            selected_item = allocation_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phân phòng", "Vui lòng chọn phân phòng để xóa.")
                return

            allocation_id = allocation_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa phân phòng này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM RoomAllocationHistory WHERE AllocationID = ?', (allocation_id,))
                    conn.commit()
                    load_room_allocations()
                    messagebox.showinfo("Thành công", "Xóa phân phòng thành công.")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể xóa phân phòng: {e}")

        tk.Label(content_frame, text="Lịch sử phân phòng", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_allocations).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mã phòng:").grid(row=1, column=0, padx=5, pady=10)
        entry_room_id = tk.Entry(form_frame)
        entry_room_id.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày phân phòng (DD-MM-YYYY):").grid(row=2, column=0, padx=5, pady=10)
        entry_allocation_date = tk.Entry(form_frame)
        entry_allocation_date.grid(row=2, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Ngày trả phòng (DD-MM-YYYY):").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_release_date = tk.Entry(form_frame)
        entry_release_date.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=1, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm phân phòng", bg="#8BC34A", fg="white", command=add_allocation).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa thông tin", bg="#FFA500", fg="white", command=update_allocation).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa phân phòng", bg="#FF6347", fg="white", command=delete_allocation).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "AllocationID": "Mã phân phòng",
            "StudentID": "Mã sinh viên",
            "RoomID": "Mã phòng",
            "AllocationDate": "Ngày phân phòng",
            "ReleaseDate": "Ngày trả phòng",
            "Notes": "Ghi chú"
        }

        allocation_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        allocation_tree.pack(fill=tk.BOTH, expand=True)

        for col in allocation_tree["columns"]:
            allocation_tree.heading(col, text=column_mapping[col])
            allocation_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_room_allocations()
    
    
    # Hàm hiển thị trang hóa đơn
    def show_payments():
        on_button_click(btn_payments)
        clear_frame(content_frame)

        def load_payments():
            for row in payment_tree.get_children():
                payment_tree.delete(row)
            cursor.execute('SELECT * FROM Payments')
            for payment in cursor.fetchall():
                payment_tree.insert('', tk.END, values=payment)

        def search_payments():
            search_term = entry_search.get()
            for row in payment_tree.get_children():
                payment_tree.delete(row)
            cursor.execute('''SELECT * FROM Payments WHERE StudentID LIKE ? OR ContractID LIKE ? OR Amount LIKE ? OR LateFee LIKE ? 
                            OR PaymentDate LIKE ? OR Purpose LIKE ? OR PaymentMethod LIKE ? OR PaymentStatus LIKE ? OR ReceiptNumber LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', 
                            '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for payment in cursor.fetchall():
                payment_tree.insert('', tk.END, values=payment)

        def add_payment():
            student_id = entry_student_id.get()
            contract_id = entry_contract_id.get()
            amount = entry_amount.get()
            late_fee = entry_late_fee.get()
            payment_date = entry_payment_date.get()
            purpose = purpose_var.get()
            payment_method = payment_method_var.get()
            payment_status = payment_status_var.get()
            receipt_number = entry_receipt_number.get()

            if not is_valid_date(payment_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and amount and purpose and payment_method:
                try:
                    cursor.execute('''INSERT INTO Payments (
                        StudentID, ContractID, Amount, LateFee, PaymentDate, Purpose, PaymentMethod, PaymentStatus, ReceiptNumber
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, contract_id, amount, late_fee, payment_date, purpose, payment_method, payment_status, receipt_number))
                    conn.commit()
                    load_payments()
                    messagebox.showinfo("Thành công", "Thêm thanh toán thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_payment():
            selected_item = payment_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn thanh toán", "Vui lòng chọn thanh toán để sửa.")
                return

            payment_id = payment_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            contract_id = entry_contract_id.get()
            amount = entry_amount.get()
            late_fee = entry_late_fee.get()
            payment_date = entry_payment_date.get()
            purpose = purpose_var.get()
            payment_method = payment_method_var.get()
            payment_status = payment_status_var.get()
            receipt_number = entry_receipt_number.get()

            if not is_valid_date(payment_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and amount and purpose and payment_method:
                try:
                    cursor.execute('''UPDATE Payments SET
                        StudentID = ?, ContractID = ?, Amount = ?, LateFee = ?, PaymentDate = ?, Purpose = ?, PaymentMethod = ?, PaymentStatus = ?, ReceiptNumber = ?
                        WHERE PaymentID = ?''',
                        (student_id, contract_id, amount, late_fee, payment_date, purpose, payment_method, payment_status, receipt_number, payment_id))
                    conn.commit()
                    load_payments()
                    messagebox.showinfo("Thành công", "Cập nhật thanh toán thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_payment():
            selected_item = payment_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn thanh toán", "Vui lòng chọn thanh toán để xóa.")
                return

            payment_id = payment_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa thanh toán này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Payments WHERE PaymentID = ?', (payment_id,))
                    conn.commit()
                    load_payments()
                    messagebox.showinfo("Thành công", "Xóa thanh toán thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý thanh toán", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_payments).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mã hợp đồng:").grid(row=1, column=0, padx=5, pady=10)
        entry_contract_id = tk.Entry(form_frame)
        entry_contract_id.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Số tiền:").grid(row=2, column=0, padx=5, pady=10)
        entry_amount = tk.Entry(form_frame)
        entry_amount.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Phí trễ hạn:").grid(row=3, column=0, padx=5, pady=10)
        entry_late_fee = tk.Entry(form_frame)
        entry_late_fee.grid(row=3, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày thanh toán (DD-MM-YYYY):").grid(row=4, column=0, padx=5, pady=10)
        entry_payment_date = tk.Entry(form_frame)
        entry_payment_date.grid(row=4, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Mục đích:").grid(row=0, column=2, padx=(30, 10), pady=10)
        purpose_var = tk.StringVar()
        purpose_var.set("Rent")
        tk.OptionMenu(form_frame, purpose_var, "Rent", "Utilities", "Deposit", "Other").grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Phương thức thanh toán:").grid(row=1, column=2, padx=(30, 10), pady=10)
        payment_method_var = tk.StringVar()
        payment_method_var.set("Cash")
        tk.OptionMenu(form_frame, payment_method_var, "Cash", "Card", "Bank Transfer").grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Trạng thái thanh toán:").grid(row=2, column=2, padx=(30, 10), pady=10)
        payment_status_var = tk.StringVar()
        payment_status_var.set("Pending")
        tk.OptionMenu(form_frame, payment_status_var, "Pending", "Completed", "Failed").grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Số biên lai:").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_receipt_number = tk.Entry(form_frame)
        entry_receipt_number.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm thanh toán", bg="#8BC34A", fg="white", command=add_payment).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa thanh toán", bg="#FFA500", fg="white", command=update_payment).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa thanh toán", bg="#FF6347", fg="white", command=delete_payment).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "PaymentID": "Mã thanh toán",
            "StudentID": "Mã sinh viên",
            "ContractID": "Mã hợp đồng",
            "Amount": "Số tiền",
            "LateFee": "Phí trễ hạn",
            "PaymentDate": "Ngày thanh toán",
            "Purpose": "Mục đích",
            "PaymentMethod": "Phương thức thanh toán",
            "PaymentStatus": "Trạng thái thanh toán",
            "ReceiptNumber": "Số biên lai"
        }

        payment_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        payment_tree.pack(fill=tk.BOTH, expand=True)

        for col in payment_tree["columns"]:
            payment_tree.heading(col, text=column_mapping[col])
            payment_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_payments()
    
    
    # Hàm hiển thị trang yêu cầu bảo trì
    def show_maintenance_request():
        on_button_click(btn_maintenance_request)
        clear_frame(content_frame)

        def load_requests():
            for row in request_tree.get_children():
                request_tree.delete(row)
            cursor.execute('SELECT * FROM MaintenanceRequests')
            for request in cursor.fetchall():
                request_tree.insert('', tk.END, values=request)

        def search_requests():
            search_term = entry_search.get()
            for row in request_tree.get_children():
                request_tree.delete(row)
            cursor.execute('''SELECT * FROM MaintenanceRequests WHERE StudentID LIKE ? OR Description LIKE ? OR UrgencyLevel LIKE ? 
                            OR AssignedStaffID LIKE ? OR Status LIKE ? OR RequestDate LIKE ? OR CompletionDate LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', 
                            '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for request in cursor.fetchall():
                request_tree.insert('', tk.END, values=request)

        def add_request():
            student_id = entry_student_id.get()
            description = entry_description.get()
            urgency_level = urgency_level_var.get()
            assigned_staff_id = entry_assigned_staff_id.get()
            status = status_var.get()
            request_date = entry_request_date.get()
            completion_date = entry_completion_date.get()
            notes = entry_notes.get()

            if not is_valid_date(request_date) or (completion_date and not is_valid_date(completion_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and description and urgency_level and status:
                try:
                    cursor.execute('''INSERT INTO MaintenanceRequests (
                        StudentID, Description, UrgencyLevel, AssignedStaffID, Status, RequestDate, CompletionDate, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, description, urgency_level, assigned_staff_id, status, request_date, completion_date, notes))
                    conn.commit()
                    load_requests()
                    messagebox.showinfo("Thành công", "Thêm yêu cầu bảo trì thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_request():
            selected_item = request_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn yêu cầu", "Vui lòng chọn yêu cầu để sửa.")
                return

            request_id = request_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            description = entry_description.get()
            urgency_level = urgency_level_var.get()
            assigned_staff_id = entry_assigned_staff_id.get()
            status = status_var.get()
            request_date = entry_request_date.get()
            completion_date = entry_completion_date.get()
            notes = entry_notes.get()

            if not is_valid_date(request_date) or (completion_date and not is_valid_date(completion_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and description and urgency_level and status:
                try:
                    cursor.execute('''UPDATE MaintenanceRequests SET
                        StudentID = ?, Description = ?, UrgencyLevel = ?, AssignedStaffID = ?, Status = ?, RequestDate = ?, CompletionDate = ?, Notes = ?
                        WHERE RequestID = ?''',
                        (student_id, description, urgency_level, assigned_staff_id, status, request_date, completion_date, notes, request_id))
                    conn.commit()
                    load_requests()
                    messagebox.showinfo("Thành công", "Cập nhật yêu cầu bảo trì thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_request():
            selected_item = request_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn yêu cầu", "Vui lòng chọn yêu cầu để xóa.")
                return

            request_id = request_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa yêu cầu này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM MaintenanceRequests WHERE RequestID = ?', (request_id,))
                    conn.commit()
                    load_requests()
                    messagebox.showinfo("Thành công", "Xóa yêu cầu bảo trì thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý yêu cầu bảo trì", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_requests).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mô tả:").grid(row=1, column=0, padx=5, pady=10)
        entry_description = tk.Entry(form_frame)
        entry_description.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mức độ khẩn cấp:").grid(row=2, column=0, padx=5, pady=10)
        urgency_level_var = tk.StringVar()
        urgency_level_var.set("Low")
        tk.OptionMenu(form_frame, urgency_level_var, "Low", "Medium", "High").grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mã nhân viên được giao:").grid(row=3, column=0, padx=5, pady=10)
        entry_assigned_staff_id = tk.Entry(form_frame)
        entry_assigned_staff_id.grid(row=3, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Trạng thái:").grid(row=0, column=2, padx=(30, 10), pady=10)
        status_var = tk.StringVar()
        status_var.set("Pending")
        tk.OptionMenu(form_frame, status_var, "Pending", "In Progress", "Completed").grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày yêu cầu (DD-MM-YYYY):").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_request_date = tk.Entry(form_frame)
        entry_request_date.grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày hoàn thành (DD-MM-YYYY):").grid(row=2, column=2, padx=(30, 10), pady=10)
        entry_completion_date = tk.Entry(form_frame)
        entry_completion_date.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm yêu cầu", bg="#8BC34A", fg="white", command=add_request).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa yêu cầu", bg="#FFA500", fg="white", command=update_request).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa yêu cầu", bg="#FF6347", fg="white", command=delete_request).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "RequestID": "Mã yêu cầu",
            "StudentID": "Mã sinh viên",
            "Description": "Mô tả",
            "UrgencyLevel": "Mức độ khẩn cấp",
            "AssignedStaffID": "Mã nhân viên được giao",
            "Status": "Trạng thái",
            "RequestDate": "Ngày yêu cầu",
            "CompletionDate": "Ngày hoàn thành",
            "Notes": "Ghi chú"
        }

        request_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        request_tree.pack(fill=tk.BOTH, expand=True)

        for col in request_tree["columns"]:
            request_tree.heading(col, text=column_mapping[col])
            request_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_requests()

    
    # Hàm hiển thị trang kho đồ
    def show_inventory():
        on_button_click(btn_inventory)
        clear_frame(content_frame)

        def load_inventory():
            for row in inventory_tree.get_children():
                inventory_tree.delete(row)
            cursor.execute('SELECT * FROM Inventory')
            for item in cursor.fetchall():
                inventory_tree.insert('', tk.END, values=item)

        def search_inventory():
            search_term = entry_search.get()
            for row in inventory_tree.get_children():
                inventory_tree.delete(row)
            cursor.execute('''SELECT * FROM Inventory WHERE ItemName LIKE ? OR Quantity LIKE ? OR Location LIKE ? OR Status LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for item in cursor.fetchall():
                inventory_tree.insert('', tk.END, values=item)

        def add_item():
            item_name = entry_item_name.get()
            quantity = entry_quantity.get()
            location = entry_location.get()
            status = status_var.get()
            notes = entry_notes.get()

            if item_name and quantity:
                try:
                    cursor.execute('''INSERT INTO Inventory (
                        ItemName, Quantity, Location, Status, Notes
                    ) VALUES (?, ?, ?, ?, ?)''',
                        (item_name, quantity, location, status, notes))
                    conn.commit()
                    load_inventory()
                    messagebox.showinfo("Thành công", "Thêm vật phẩm thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_item():
            selected_item = inventory_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn vật phẩm", "Vui lòng chọn vật phẩm để sửa.")
                return

            item_id = inventory_tree.item(selected_item)['values'][0]
            item_name = entry_item_name.get()
            quantity = entry_quantity.get()
            location = entry_location.get()
            status = status_var.get()
            notes = entry_notes.get()

            if item_name and quantity:
                try:
                    cursor.execute('''UPDATE Inventory SET
                        ItemName = ?, Quantity = ?, Location = ?, Status = ?, Notes = ?
                        WHERE ItemID = ?''',
                        (item_name, quantity, location, status, notes, item_id))
                    conn.commit()
                    load_inventory()
                    messagebox.showinfo("Thành công", "Cập nhật vật phẩm thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_item():
            selected_item = inventory_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn vật phẩm", "Vui lòng chọn vật phẩm để xóa.")
                return

            item_id = inventory_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa vật phẩm này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Inventory WHERE ItemID = ?', (item_id,))
                    conn.commit()
                    load_inventory()
                    messagebox.showinfo("Thành công", "Xóa vật phẩm thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý vật phẩm", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_inventory).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Tên vật phẩm:").grid(row=0, column=0, padx=5, pady=10)
        entry_item_name = tk.Entry(form_frame)
        entry_item_name.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Số lượng:").grid(row=1, column=0, padx=5, pady=10)
        entry_quantity = tk.Entry(form_frame)
        entry_quantity.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Vị trí:").grid(row=2, column=0, padx=5, pady=10)
        entry_location = tk.Entry(form_frame)
        entry_location.grid(row=2, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Trạng thái:").grid(row=0, column=2, padx=(30, 10), pady=10)
        status_var = tk.StringVar()
        status_var.set("Available")
        tk.OptionMenu(form_frame, status_var, "Available", "In Use", "Damaged", "Lost").grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=1, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm vật phẩm", bg="#8BC34A", fg="white", command=add_item).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa vật phẩm", bg="#FFA500", fg="white", command=update_item).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa vật phẩm", bg="#FF6347", fg="white", command=delete_item).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "ItemID": "Mã vật phẩm",
            "ItemName": "Tên vật phẩm",
            "Quantity": "Số lượng",
            "Location": "Vị trí",
            "Status": "Trạng thái",
            "Notes": "Ghi chú"
        }

        inventory_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        inventory_tree.pack(fill=tk.BOTH, expand=True)

        for col in inventory_tree["columns"]:
            inventory_tree.heading(col, text=column_mapping[col])
            inventory_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_inventory()

    
    # Hàm hiển thị trang khiếu nại
    def show_complaints():
        on_button_click(btn_complaints)
        clear_frame(content_frame)

        def load_complaints():
            for row in complaint_tree.get_children():
                complaint_tree.delete(row)
            cursor.execute('SELECT * FROM Complaints')
            for complaint in cursor.fetchall():
                complaint_tree.insert('', tk.END, values=complaint)

        def search_complaints():
            search_term = entry_search.get()
            for row in complaint_tree.get_children():
                complaint_tree.delete(row)
            cursor.execute('''SELECT * FROM Complaints WHERE StudentID LIKE ? OR Subject LIKE ? OR Description LIKE ? OR Status LIKE ? 
                            OR ComplaintDate LIKE ? OR ResolutionDate LIKE ? OR Notes LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', 
                            '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for complaint in cursor.fetchall():
                complaint_tree.insert('', tk.END, values=complaint)

        def add_complaint():
            student_id = entry_student_id.get()
            subject = entry_subject.get()
            description = entry_description.get()
            status = status_var.get()
            complaint_date = entry_complaint_date.get()
            resolution_date = entry_resolution_date.get()
            notes = entry_notes.get()

            if not is_valid_date(complaint_date) or (resolution_date and not is_valid_date(resolution_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and subject and description:
                try:
                    cursor.execute('''INSERT INTO Complaints (
                        StudentID, Subject, Description, Status, ComplaintDate, ResolutionDate, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, subject, description, status, complaint_date, resolution_date, notes))
                    conn.commit()
                    load_complaints()
                    messagebox.showinfo("Thành công", "Thêm khiếu nại thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_complaint():
            selected_item = complaint_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn khiếu nại", "Vui lòng chọn khiếu nại để sửa.")
                return

            complaint_id = complaint_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            subject = entry_subject.get()
            description = entry_description.get()
            status = status_var.get()
            complaint_date = entry_complaint_date.get()
            resolution_date = entry_resolution_date.get()
            notes = entry_notes.get()

            if not is_valid_date(complaint_date) or (resolution_date and not is_valid_date(resolution_date)):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and subject and description:
                try:
                    cursor.execute('''UPDATE Complaints SET
                        StudentID = ?, Subject = ?, Description = ?, Status = ?, ComplaintDate = ?, ResolutionDate = ?, Notes = ?
                        WHERE ComplaintID = ?''',
                        (student_id, subject, description, status, complaint_date, resolution_date, notes, complaint_id))
                    conn.commit()
                    load_complaints()
                    messagebox.showinfo("Thành công", "Cập nhật khiếu nại thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_complaint():
            selected_item = complaint_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn khiếu nại", "Vui lòng chọn khiếu nại để xóa.")
                return

            complaint_id = complaint_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa khiếu nại này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM Complaints WHERE ComplaintID = ?', (complaint_id,))
                    conn.commit()
                    load_complaints()
                    messagebox.showinfo("Thành công", "Xóa khiếu nại thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý khiếu nại", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_complaints).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Chủ đề:").grid(row=1, column=0, padx=5, pady=10)
        entry_subject = tk.Entry(form_frame)
        entry_subject.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mô tả:").grid(row=2, column=0, padx=5, pady=10)
        entry_description = tk.Entry(form_frame)
        entry_description.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Trạng thái:").grid(row=3, column=0, padx=5, pady=10)
        status_var = tk.StringVar()
        status_var.set("Pending")
        tk.OptionMenu(form_frame, status_var, "Pending", "Resolved", "Dismissed").grid(row=3, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày khiếu nại (DD-MM-YYYY):").grid(row=4, column=0, padx=5, pady=10)
        entry_complaint_date = tk.Entry(form_frame)
        entry_complaint_date.grid(row=4, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Ngày giải quyết (DD-MM-YYYY):").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_resolution_date = tk.Entry(form_frame)
        entry_resolution_date.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày giải quyết (DD-MM-YYYY):").grid(row=2, column=2, padx=(30, 10), pady=10)
        entry_resolution_date = tk.Entry(form_frame)
        entry_resolution_date.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm khiếu nại", bg="#8BC34A", fg="white", command=add_complaint).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa khiếu nại", bg="#FFA500", fg="white", command=update_complaint).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa khiếu nại", bg="#FF6347", fg="white", command=delete_complaint).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "ComplaintID": "Mã khiếu nại",
            "StudentID": "Mã sinh viên",
            "Subject": "Chủ đề",
            "Description": "Mô tả",
            "Status": "Trạng thái",
            "ComplaintDate": "Ngày khiếu nại",
            "ResolutionDate": "Ngày giải quyết",
            "Notes": "Ghi chú"
        }

        complaint_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        complaint_tree.pack(fill=tk.BOTH, expand=True)

        for col in complaint_tree["columns"]:
            complaint_tree.heading(col, text=column_mapping[col])
            complaint_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_complaints()

    # Hàm hiển thị trang phạt và khoản phí
    def show_fines_and_penalties():
        on_button_click(btn_fines_and_penalties)
        clear_frame(content_frame)

        def load_fines():
            for row in fine_tree.get_children():
                fine_tree.delete(row)
            cursor.execute('SELECT * FROM FinesAndPenalties')
            for fine in cursor.fetchall():
                fine_tree.insert('', tk.END, values=fine)

        def search_fines():
            search_term = entry_search.get()
            for row in fine_tree.get_children():
                fine_tree.delete(row)
            cursor.execute('''SELECT * FROM FinesAndPenalties WHERE StudentID LIKE ? OR ViolationType LIKE ? OR Description LIKE ? OR FineAmount LIKE ? 
                            OR FineDate LIKE ? OR Status LIKE ? OR Notes LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', 
                            '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for fine in cursor.fetchall():
                fine_tree.insert('', tk.END, values=fine)

        def add_fine():
            student_id = entry_student_id.get()
            violation_type = violation_type_var.get()
            description = entry_description.get()
            fine_amount = entry_fine_amount.get()
            fine_date = entry_fine_date.get()
            status = status_var.get()
            notes = entry_notes.get()

            if not is_valid_date(fine_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and violation_type and description and fine_amount:
                try:
                    cursor.execute('''INSERT INTO FinesAndPenalties (
                        StudentID, ViolationType, Description, FineAmount, FineDate, Status, Notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (student_id, violation_type, description, fine_amount, fine_date, status, notes))
                    conn.commit()
                    load_fines()
                    messagebox.showinfo("Thành công", "Thêm phạt thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_fine():
            selected_item = fine_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phạt", "Vui lòng chọn phạt để sửa.")
                return

            fine_id = fine_tree.item(selected_item)['values'][0]
            student_id = entry_student_id.get()
            violation_type = violation_type_var.get()
            description = entry_description.get()
            fine_amount = entry_fine_amount.get()
            fine_date = entry_fine_date.get()
            status = status_var.get()
            notes = entry_notes.get()

            if not is_valid_date(fine_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and violation_type and description and fine_amount:
                try:
                    cursor.execute('''UPDATE FinesAndPenalties SET
                        StudentID = ?, ViolationType = ?, Description = ?, FineAmount = ?, FineDate = ?, Status = ?, Notes = ?
                        WHERE FineID = ?''',
                        (student_id, violation_type, description, fine_amount, fine_date, status, notes, fine_id))
                    conn.commit()
                    load_fines()
                    messagebox.showinfo("Thành công", "Cập nhật phạt thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_fine():
            selected_item = fine_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phạt", "Vui lòng chọn phạt để xóa.")
                return

            fine_id = fine_tree.item(selected_item)['values'][0]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa phạt này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM FinesAndPenalties WHERE FineID = ?', (fine_id,))
                    conn.commit()
                    load_fines()
                    messagebox.showinfo("Thành công", "Xóa phạt thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý phạt", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_fines).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Loại vi phạm:").grid(row=1, column=0, padx=5, pady=10)
        violation_type_var = tk.StringVar()
        violation_type_var.set("Noise")
        tk.OptionMenu(form_frame, violation_type_var, "Noise", "Late Payment", "Damage", "Other").grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mô tả:").grid(row=2, column=0, padx=5, pady=10)
        entry_description = tk.Entry(form_frame)
        entry_description.grid(row=2, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Số tiền phạt:").grid(row=3, column=0, padx=5, pady=10)
        entry_fine_amount = tk.Entry(form_frame)
        entry_fine_amount.grid(row=3, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Ngày phạt (DD-MM-YYYY):").grid(row=0, column=2, padx=(30, 10), pady=10)
        entry_fine_date = tk.Entry(form_frame)
        entry_fine_date.grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Trạng thái:").grid(row=1, column=2, padx=(30, 10), pady=10)
        status_var = tk.StringVar()
        status_var.set("Unpaid")
        tk.OptionMenu(form_frame, status_var, "Unpaid", "Paid").grid(row=1, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=2, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=2, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày giải quyết (DD-MM-YYYY):").grid(row=3, column=2, padx=(30, 10), pady=10)
        entry_resolution_date = tk.Entry(form_frame)
        entry_resolution_date.grid(row=3, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm phạt", bg="#8BC34A", fg="white", command=add_fine).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa phạt", bg="#FFA500", fg="white", command=update_fine).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa phạt", bg="#FF6347", fg="white", command=delete_fine).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "FineID": "Mã phạt",
            "StudentID": "Mã sinh viên",
            "ViolationType": "Loại vi phạm",
            "Description": "Mô tả",
            "FineAmount": "Số tiền phạt",
            "FineDate": "Ngày phạt",
            "Status": "Trạng thái",
            "Notes": "Ghi chú"
        }

        fine_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        fine_tree.pack(fill=tk.BOTH, expand=True)

        for col in fine_tree["columns"]:
            fine_tree.heading(col, text=column_mapping[col])
            fine_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_fines()

    
    # Hàm hiển thị trang phạt sinh viên
    def show_student_fines():
        on_button_click(btn_student_fines)
        clear_frame(content_frame)

        def load_student_fines():
            for row in student_fine_tree.get_children():
                student_fine_tree.delete(row)
            cursor.execute('SELECT * FROM StudentFines')
            for student_fine in cursor.fetchall():
                student_fine_tree.insert('', tk.END, values=student_fine)

        def search_student_fines():
            search_term = entry_search.get()
            for row in student_fine_tree.get_children():
                student_fine_tree.delete(row)
            cursor.execute('''SELECT * FROM StudentFines WHERE StudentID LIKE ? OR FineID LIKE ? OR IssuedDate LIKE ? OR Status LIKE ? OR Notes LIKE ?''', 
                        ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            for student_fine in cursor.fetchall():
                student_fine_tree.insert('', tk.END, values=student_fine)

        def add_student_fine():
            student_id = entry_student_id.get()
            fine_id = entry_fine_id.get()
            issued_date = entry_issued_date.get()
            status = status_var.get()
            notes = entry_notes.get()

            if not is_valid_date(issued_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and fine_id:
                try:
                    cursor.execute('''INSERT INTO StudentFines (
                        StudentID, FineID, IssuedDate, Status, Notes
                    ) VALUES (?, ?, ?, ?, ?)''',
                        (student_id, fine_id, issued_date, status, notes))
                    conn.commit()
                    load_student_fines()
                    messagebox.showinfo("Thành công", "Thêm phạt sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def update_student_fine():
            selected_item = student_fine_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phạt sinh viên", "Vui lòng chọn phạt sinh viên để sửa.")
                return

            student_id = student_fine_tree.item(selected_item)['values'][0]
            fine_id = student_fine_tree.item(selected_item)['values'][1]
            issued_date = entry_issued_date.get()
            status = status_var.get()
            notes = entry_notes.get()

            if not is_valid_date(issued_date):
                messagebox.showerror("Lỗi", "Ngày không hợp lệ. Định dạng đúng là DD-MM-YYYY.")
                return

            if student_id and fine_id:
                try:
                    cursor.execute('''UPDATE StudentFines SET
                        IssuedDate = ?, Status = ?, Notes = ?
                        WHERE StudentID = ? AND FineID = ?''',
                        (issued_date, status, notes, student_id, fine_id))
                    conn.commit()
                    load_student_fines()
                    messagebox.showinfo("Thành công", "Cập nhật phạt sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            else:
                messagebox.showerror("Lỗi", "Vui lòng nhập các thông tin bắt buộc.")

        def delete_student_fine():
            selected_item = student_fine_tree.selection()
            if not selected_item:
                messagebox.showwarning("Chưa chọn phạt sinh viên", "Vui lòng chọn phạt sinh viên để xóa.")
                return

            student_id = student_fine_tree.item(selected_item)['values'][0]
            fine_id = student_fine_tree.item(selected_item)['values'][1]
            confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa phạt sinh viên này?")
            if confirm:
                try:
                    cursor.execute('DELETE FROM StudentFines WHERE StudentID = ? AND FineID = ?', (student_id, fine_id))
                    conn.commit()
                    load_student_fines()
                    messagebox.showinfo("Thành công", "Xóa phạt sinh viên thành công!")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        tk.Label(content_frame, text="Quản lý phạt sinh viên", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

        search_frame = tk.Frame(content_frame, bg="#f0f0f0")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        entry_search = tk.Entry(search_frame)
        entry_search.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Tìm kiếm", command=search_student_fines).pack(side=tk.LEFT, padx=5)

        form_frame = tk.Frame(content_frame, bg="#f0f0f0")
        form_frame.pack(pady=10)

        # Cột 1
        tk.Label(form_frame, text="Mã sinh viên:").grid(row=0, column=0, padx=5, pady=10)
        entry_student_id = tk.Entry(form_frame)
        entry_student_id.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Mã phạt:").grid(row=1, column=0, padx=5, pady=10)
        entry_fine_id = tk.Entry(form_frame)
        entry_fine_id.grid(row=1, column=1, padx=5, pady=10)

        tk.Label(form_frame, text="Ngày phát hành (DD-MM-YYYY):").grid(row=2, column=0, padx=5, pady=10)
        entry_issued_date = tk.Entry(form_frame)
        entry_issued_date.grid(row=2, column=1, padx=5, pady=10)

        # Cột 2
        tk.Label(form_frame, text="Trạng thái:").grid(row=0, column=2, padx=(30, 10), pady=10)
        status_var = tk.StringVar()
        status_var.set("Unpaid")
        tk.OptionMenu(form_frame, status_var, "Unpaid", "Paid", "Waived").grid(row=0, column=3, padx=5, pady=10)

        tk.Label(form_frame, text="Ghi chú:").grid(row=1, column=2, padx=(30, 10), pady=10)
        entry_notes = tk.Entry(form_frame)
        entry_notes.grid(row=1, column=3, padx=5, pady=10)

        # Nút bấm
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm phạt sinh viên", bg="#8BC34A", fg="white", command=add_student_fine).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Sửa phạt sinh viên", bg="#FFA500", fg="white", command=update_student_fine).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Xóa phạt sinh viên", bg="#FF6347", fg="white", command=delete_student_fine).grid(row=0, column=2, padx=10)

        # Từ điển ánh xạ các tiêu đề cột từ tiếng Anh sang tiếng Việt
        column_mapping = {
            "StudentID": "Mã sinh viên",
            "FineID": "Mã phạt",
            "IssuedDate": "Ngày phát hành",
            "Status": "Trạng thái",
            "Notes": "Ghi chú"
        }

        student_fine_tree = ttk.Treeview(content_frame, columns=list(column_mapping.keys()), show="headings")
        student_fine_tree.pack(fill=tk.BOTH, expand=True)

        for col in student_fine_tree["columns"]:
            student_fine_tree.heading(col, text=column_mapping[col])
            student_fine_tree.column(col, anchor="w", width=100, stretch=tk.YES)

        load_student_fines()

    
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

    # Tạo các nút trên thanh navbar
    btn_students = tk.Button(navbar, text="Sinh viên", command=show_students, width=20, pady=10, bg="#34495e", fg="white")
    btn_students.pack(pady=5)
    btn_contracts = tk.Button(navbar, text="Hợp đồng", command=show_contracts, width=20, pady=10, bg="#34495e", fg="white")
    btn_contracts.pack(pady=5)
    btn_staff = tk.Button(navbar, text="Nhân viên", command=show_staff, width=20, pady=10, bg="#34495e", fg="white")
    btn_staff.pack(pady=5)
    btn_room = tk.Button(navbar, text="Phòng ở", command=show_room, width=20, pady=10, bg="#34495e", fg="white")
    btn_room.pack(pady=5)
    btn_room_allocation_history = tk.Button(navbar, text="Lịch sử phân phòng", command=show_room_allocation_history, width=20, pady=10, bg="#34495e", fg="white")
    btn_room_allocation_history.pack(pady=5)
    btn_payments = tk.Button(navbar, text="Thanh toán", command=show_payments, width=20, pady=10, bg="#34495e", fg="white")
    btn_payments.pack(pady=5)
    btn_maintenance_request = tk.Button(navbar, text="Yêu cầu bảo trì", command=show_maintenance_request, width=20, pady=10, bg="#34495e", fg="white")
    btn_maintenance_request.pack(pady=5)
    btn_inventory = tk.Button(navbar, text="Kho vật tư", command=show_inventory, width=20, pady=10, bg="#34495e", fg="white")
    btn_inventory.pack(pady=5)
    btn_complaints = tk.Button(navbar, text="Khiếu nại", command=show_complaints, width=20, pady=10, bg="#34495e", fg="white")
    btn_complaints.pack(pady=5)
    btn_fines_and_penalties = tk.Button(navbar, text="Phí vi phạm", command=show_fines_and_penalties, width=20, pady=10, bg="#34495e", fg="white")
    btn_fines_and_penalties.pack(pady=5)
    btn_student_fines = tk.Button(navbar, text="Vi phạm sinh viên", command=show_student_fines, width=20, pady=10, bg="#34495e", fg="white")
    btn_student_fines.pack(pady=5)

    # Tạo frame nội dung
    content_frame = tk.Frame(root, bg="#ecf0f1", width=800, height=600)
    content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    root.mainloop()


# Function to handle login
def handle_login():
    username = entry_username.get()
    password = entry_password.get()
    
    # Show the progress bar
    progress_bar.pack(pady=10)
    login_window.update_idletasks()
    
    # Start a simulation of the loading process with after()
    progress_bar['value'] = 0  # Reset progress bar to 0
    simulate_loading(0, username, password)

# Function to simulate the loading process (non-blocking)
def simulate_loading(i, username, password):
    if i < 100:
        progress_bar['value'] = i
        login_window.after(8, simulate_loading, i + 1, username, password)  # Update progress every 20ms
    else:
        # Hide the progress bar after the loading is complete
        progress_bar.pack_forget()
        messagebox.showinfo("Login Info", "Login successfully")
        open_main_app()


def open_register_window():
    register_window = tk.Toplevel(login_window)
    register_window.title("Đăng ký")
    register_window.geometry("400x250")
    register_window.configure(bg="#e0e0e0")

    tk.Label(register_window, text="Đăng ký", font=("Helvetica", 18, "bold"), bg="#e0e0e0").pack(pady=15)

    frame = tk.Frame(register_window, bg="#e0e0e0")
    frame.pack(pady=10)

    tk.Label(frame, text="Tên đăng nhập:", font=("Helvetica", 12), bg="#e0e0e0").grid(row=0, column=0, pady=10, padx=10)
    entry_reg_username = tk.Entry(frame, font=("Helvetica", 12), width=20)
    entry_reg_username.grid(row=0, column=1, pady=10, padx=10)

    tk.Label(frame, text="Mật khẩu:", font=("Helvetica", 12), bg="#e0e0e0").grid(row=1, column=0, pady=10, padx=10)
    entry_reg_password = tk.Entry(frame, font=("Helvetica", 12), width=20, show="*")
    entry_reg_password.grid(row=1, column=1, pady=10, padx=10)

    tk.Label(frame, text="Xác nhận mật khẩu:", font=("Helvetica", 12), bg="#e0e0e0").grid(row=2, column=0, pady=10, padx=10)
    entry_confirm_password = tk.Entry(frame, font=("Helvetica", 12), width=20, show="*")
    entry_confirm_password.grid(row=2, column=1, pady=10, padx=10)

    tk.Button(register_window, text="Đăng ký", font=("Helvetica", 12), bg="#8BC34A", fg="white", command=lambda: messagebox.showinfo("Register Info", "Registration Successful")).pack(pady=20)

# Tạo cửa sổ đăng nhập
login_window = tk.Tk()
login_window.title("Đăng nhập")
login_window.geometry("400x310")
login_window.configure(bg="#f0f0f0")

# Tiêu đề
tk.Label(login_window, text="Đăng nhập", font=("Helvetica", 16, "bold"), bg="#f0f0f0").pack(pady=15)

# Nhãn và ô nhập liệu
frame = tk.Frame(login_window, bg="#f0f0f0")
frame.pack(pady=10)

# Tên đăng nhập
tk.Label(frame, text="Tên đăng nhập:", font=("Helvetica", 10), bg="#f0f0f0").grid(row=0, column=0, pady=10, padx=10)
entry_username = tk.Entry(frame, font=("Helvetica", 10), width=20)
entry_username.grid(row=0, column=1, pady=10, padx=10)
entry_username.insert(0, "anhnguyen") 

tk.Label(frame, text="Mật khẩu:", font=("Helvetica", 10), bg="#f0f0f0").grid(row=1, column=0, pady=10, padx=10)
entry_password = tk.Entry(frame, font=("Helvetica", 10), width=20, show="*")
entry_password.grid(row=1, column=1, pady=10, padx=10)
entry_password.insert(0, "123456") 

button_frame = tk.Frame(login_window, bg="#f0f0f0")
button_frame.pack(pady=10)

tk.Button(button_frame, text="Đăng nhập", font=("Helvetica", 10), bg="#8BC34A", fg="white", width=10, height=1, command=handle_login).grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Đăng ký", font=("Helvetica", 10), bg="#03A9F4", fg="white", width=10, height=1, command=open_register_window).grid(row=0, column=1, padx=10)

progress_bar = ttk.Progressbar(login_window, orient="horizontal", length=300, mode="determinate")

tk.Label(login_window, text="Don't have an account?", font=("Helvetica", 10), fg="#03A9F4", bg="#f0f0f0").pack(pady=5)
tk.Label(login_window, text="Forgot your password ?", font=("Helvetica", 10), fg="#03A9F4", bg="#f0f0f0").pack(pady=5)

login_window.mainloop()

conn.close()
