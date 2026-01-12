import mysql.connector
from tkinter import *
from tkinter import messagebox

# ---------------- DB CONNECTION & TABLES ----------------

myconn = mysql.connector.connect(
     host="localhost",
        user="root",
        password="root",
    database='office',
    auth_plugin='mysql_native_password'
)
cur = myconn.cursor()

current_user_id = None        # logged-in user id
current_user_name = None      # logged-in user name

# users table
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        address TEXT NOT NULL,
        password VARCHAR(100) NOT NULL
    )
''')

# bike_details table
cur.execute("""
CREATE TABLE IF NOT EXISTS bike_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(100),
    type VARCHAR(50),
    price_per_hour INT,
    stock INT
)
""")

# rentals table (ids + names + active flag)
cur.execute("""
CREATE TABLE IF NOT EXISTS rentals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bike_id INT,
    user_name VARCHAR(100),
    bike_name VARCHAR(100),
    hours INT,
    total_rent INT,
    active TINYINT(1) NOT NULL DEFAULT 1,
    rented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# insert 10 bikes (run once)
cur.execute("SELECT COUNT(*) FROM bike_details")
count = cur.fetchone()[0]
if count == 0:
    cur.executemany(
        "INSERT INTO bike_details (model, type, price_per_hour, stock) "
        "VALUES (%s,%s,%s,%s)",
        [
            ('Hero Splendor', 'Standard', 50, 5),
            ('Honda Activa', 'Scooter', 70, 5),
            ('TVS Apache', 'Sports', 100, 3),
            ('Yamaha FZ', 'Sports', 90, 4),
            ('Bajaj Pulsar', 'Sports', 95, 4),
            ('Royal Enfield Classic', 'Cruiser', 150, 2),
            ('Suzuki Access', 'Scooter', 65, 6),
            ('Honda Shine', 'Standard', 60, 5),
            ('KTM Duke 200', 'Sports', 160, 2),
            ('TVS Jupiter', 'Scooter', 70, 5)
        ]
    )
    myconn.commit()

# ---------------- MAIN WINDOW & FRAMES ----------------

root = Tk()
root.geometry("600x600")
root['bg'] = 'light grey'

login_frame = Frame(root, bg='light grey')
registration_frame = Frame(root, bg='light grey')

def show_login():
    registration_frame.pack_forget()
    login_frame.pack(fill='both', expand=True)

def show_registration():
    login_frame.pack_forget()
    registration_frame.pack(fill='both', expand=True)

# ---------------- SELECT & RENT BIKE POPUP ----------------

def select_bike(bikes_root):
    # close the Available Bikes window
    bikes_root.destroy()

    # check if user already has an active rental
    cur.execute(
        "SELECT bike_name, hours, total_rent FROM rentals "
        "WHERE user_id = %s AND active = 1",
        (current_user_id,)
    )
    existing = cur.fetchone()
    if existing:
        bike_name, hours, total_rent = existing
        messagebox.showwarning(
            "Active rental",
            f"You already rented:\n{bike_name}\n"
            f"Hours: {hours}\nTotal rent: ₹{total_rent}\n\n"
            "Return this bike before renting another."
        )
        return

    # create a NEW main window for selecting bike
    sel_win = Tk()
    sel_win.title("Select a bike")
    sel_win.geometry("350x300")
    sel_win.configure(bg="light grey")

    Label(sel_win, text="Choose a bike:",
          bg="light grey", font=("Roboto", 12, "bold")).pack(pady=5)

    list_box = Listbox(sel_win, width=35, height=10)
    list_box.pack(pady=5)

    cur.execute("SELECT id, model, price_per_hour FROM bike_details")
    bikes = cur.fetchall()
    for b in bikes:
        list_box.insert(END, f"{b[1]} (₹{b[2]}/hr)")

    Label(sel_win, text="No. of hours:",
          bg="light grey", font=("Roboto", 10)).pack(pady=5)
    hours_entry = Entry(sel_win)
    hours_entry.pack()

    def confirm_rent():
        sel = list_box.curselection()
        if not sel:
            messagebox.showwarning("Select", "Please select a bike")
            return

        try:
            hours = int(hours_entry.get())
        except ValueError:
            messagebox.showwarning("Hours", "Enter hours as a number")
            return

        idx = sel[0]
        bike_id, model, price = bikes[idx]
        total_rent = hours * price

        details = (
            f"User: {current_user_name}\n"
            f"Bike rented: {model}\n"
            f"Hours: {hours}\n"
            f"Rate: ₹{price} per hour\n"
            f"Total rent: ₹{total_rent}"
        )

        if messagebox.askokcancel("Confirm Rent", details):
            # store ids + names + active flag
            cur.execute(
                "INSERT INTO rentals (user_id, bike_id, user_name, bike_name, hours, total_rent, active) "
                "VALUES (%s, %s, %s, %s, %s, %s, 1)",
                (current_user_id, bike_id, current_user_name, model, hours, total_rent)
            )
            myconn.commit()
            sel_win.destroy()

            # open dashboard
            dash = Tk()
            dash.title("Rental Dashboard")
            dash.geometry("380x260")
            dash.configure(bg="light grey")

            Label(dash, text=f"User: {current_user_name}",
                  bg="light grey", font=("Roboto", 12, "bold")).pack(pady=5)
            Label(dash, text=f"Bike: {model}",
                  bg="light grey", font=("Roboto", 11)).pack(pady=5)
            Label(dash, text=f"Hours: {hours}",
                  bg="light grey", font=("Roboto", 11)).pack(pady=5)
            Label(dash, text=f"Total rent: ₹{total_rent}",
                  bg="light grey", font=("Roboto", 11)).pack(pady=5)

            buttons_frame = Frame(dash, bg="light grey")
            buttons_frame.pack(pady=20)

            def return_bike():
                # mark rental inactive
                cur.execute(
                    "UPDATE rentals SET active = 0 "
                    "WHERE user_id = %s AND bike_id = %s AND active = 1",
                    (current_user_id, bike_id)
                )
                myconn.commit()
                messagebox.showinfo("Returned", "Bike returned successfully.")
                dash.destroy()

            def new_rental():
                # only allow if no active rental now
                cur.execute(
                    "SELECT 1 FROM rentals WHERE user_id = %s AND active = 1",
                    (current_user_id,)
                )
                still_active = cur.fetchone()
                if still_active:
                    messagebox.showwarning(
                        "Active rental",
                        "You still have an active rental.\n"
                        "Return your bike before starting a new rental."
                    )
                    return
                dash.destroy()
                # open available bikes again for this user
                show_bikes_window()

            Button(buttons_frame, text="Return Bike",
                   bg="orange", fg="white",
                   font=("Roboto", 11, "bold"),
                   width=12,
                   command=return_bike).grid(row=0, column=0, padx=10)

            Button(buttons_frame, text="New Rental",
                   bg="green", fg="white",
                   font=("Roboto", 11, "bold"),
                   width=12,
                   command=new_rental).grid(row=0, column=1, padx=10)

            dash.mainloop()

    Button(sel_win, text="Rent this bike",
           bg="green", fg="white",
           font=("Roboto", 11, "bold"),
           command=confirm_rent).pack(pady=10)

    sel_win.mainloop()

# ---------------- SHOW BIKES WINDOW ----------------

def show_bikes_window():
    # this creates a fresh bikes window each time
    bikes_root = Tk()
    bikes_root.title("Available Bikes")
    bikes_root.geometry("600x450")
    bikes_root.configure(bg="light grey")

    Label(bikes_root, text="Available Bikes",
          bg="light grey", font=("impact", 18, "bold")).pack(pady=10)

    table_frame = Frame(bikes_root, bg="light grey")
    table_frame.pack(pady=10)

    header = ["Model", "Type", "Price/hour", "Stock"]
    for col, text in enumerate(header):
        Label(table_frame, text=text, bg="light grey",
              font=("Roboto", 11, "bold"), borderwidth=1, relief="solid",
              width=15).grid(row=0, column=col, padx=2, pady=2)

    cur.execute("SELECT model, type, price_per_hour, stock FROM bike_details")
    rows = cur.fetchall()

    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            Label(table_frame, text=str(value), bg="light grey",
                  font=("Roboto", 10), borderwidth=1, relief="solid",
                  width=15).grid(row=r, column=c, padx=2, pady=2)

    bottom_frame = Frame(bikes_root, bg="light grey")
    bottom_frame.pack(side=BOTTOM, pady=15)

    Button(bottom_frame, text="Select Bike",
           font=("Roboto", 12, "bold"),
           bg="green", fg="white",
           width=15,
           command=lambda: select_bike(bikes_root)).pack()

    bikes_root.mainloop()

# ---------------- REGISTRATION LOGIC ----------------

def save_data():
    name = name_entry.get()
    phone = phone_entry.get()
    address = address_entry.get()
    pwd = reg_password_entry.get()

    if not name or not phone or not address or not pwd:
        messagebox.showwarning("Warning", "Please fill all fields")
        return

    cur.execute(
        'INSERT INTO users (name, phone, address, password) VALUES (%s, %s, %s, %s)',
        (name, phone, address, pwd)
    )
    myconn.commit()
    messagebox.showinfo("Success", "Registration successful")
    name_entry.delete(0, END)
    phone_entry.delete(0, END)
    address_entry.delete(0, END)
    reg_password_entry.delete(0, END)

    show_login()

# ---------------- LOGIN LOGIC ----------------

def check_login():
    global current_user_id, current_user_name

    username = login_user_entry.get()
    pwd = login_password_entry.get()

    cur.execute(
        "SELECT * FROM users WHERE name = %s AND password = %s",
        (username, pwd)
    )
    row = cur.fetchone()

    if row:
        current_user_id = row[0]      # id from users
        current_user_name = row[1]    # name from users
        messagebox.showinfo("Success", "Login successful")
        root.destroy()
        show_bikes_window()
    else:
        messagebox.showwarning(
            "User not found",
            "User does not exist.\nPlease register first."
        )
        show_registration()

# ---------------- REGISTRATION FRAME ----------------

Label(registration_frame, text="Bike Rental System",
      bg="light grey", font=("impact", 21, "bold")).place(x=190, y=40)

Label(registration_frame, text="Registration",
      bg="light grey", font=("arial rounded mt bold", 15, "bold")).place(x=240, y=100)

Button(registration_frame, text="Enter your name",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=160)

Button(registration_frame, text="Enter phone number",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=190)

Button(registration_frame, text="Address",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=220)

Button(registration_frame, text="Create password",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=250)

submit_reg = Button(registration_frame, text="submit",
                    bd=4, bg="green", fg="white",
                    font=("Roboto", 12, "bold"),
                    command=save_data)
submit_reg.place(x=250, y=340)

name_entry = Entry(registration_frame)
name_entry.place(x=305, y=165)

phone_entry = Entry(registration_frame)
phone_entry.place(x=305, y=195)

address_entry = Entry(registration_frame)
address_entry.place(x=305, y=225)

reg_password_entry = Entry(registration_frame, show="*")
reg_password_entry.place(x=305, y=255)

def move_focus(event, next_entry):
    next_entry.focus_set()

name_entry.bind('<Return>', lambda e: move_focus(e, phone_entry))
phone_entry.bind('<Return>', lambda e: move_focus(e, address_entry))
address_entry.bind('<Return>', lambda e: move_focus(e, reg_password_entry))
reg_password_entry.bind('<Return>', lambda e: submit_reg.focus_set())

# ---------------- LOGIN FRAME WIDGETS ----------------

Label(login_frame, text="Bike Rental System",
      bg="light grey", font=("impact", 21, "bold")).place(x=190, y=40)

Label(login_frame, text="Login page",
      bg="light grey", font=("arial rounded mt bold", 18, "bold")).place(x=220, y=100)

Button(login_frame, text="User name",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=150)

Button(login_frame, text="Enter password",
       bg="light grey", bd=0, font=("Roboto", 13)).place(x=140, y=180)

submit_login = Button(login_frame, text="submit",
                      bd=4, bg="green", fg="white",
                      font=("Roboto", 12, "bold"),
                      command=check_login)
submit_login.place(x=250, y=230)

login_user_entry = Entry(login_frame)
login_user_entry.place(x=260, y=155)

login_password_entry = Entry(login_frame, show="*")
login_password_entry.place(x=260, y=185)

def next_line(event):
    login_password_entry.focus_set()

login_user_entry.bind('<Return>', next_line)
Button(login_frame, text="New user? Register",
       bg="light grey", bd=0, fg="blue",
       command=show_registration).place(x=230, y=270)

# ---------------- START APP ----------------
show_login()
root.mainloop()
myconn.close()
