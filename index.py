import customtkinter as ctk
import sqlite3
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime
import json
conn=sqlite3.connect('inventory.db')
c=conn.cursor()

def set_database():
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_in(
              package_id TEXT PRIMARY KEY,
              item_name TEXT,
              quantity INTEGER,
              time_in TEXT
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_out(
              package_id TEXT PRIMARY KEY,
              item_name TEXT,
              quantity INTEGER,
              time_out TEXT
            )''')
    conn.commit()
    

def add_item(data):
    time_in=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
       c.execute("INSERT INTO inventory_in VALUES(?,?,?,?)",
                 (data['package_id'],data['item_name'],data['quantity'],time_in))
       conn.commit() 
       print("Scanned Data:",data)
    except sqlite3.IntegrityError:
        print("Package already exixts")

def remove_item(package_id):
    c.execute("SELECT * FROM inventory_in WHERE package_id=?",(package_id,))
    row=c.fetchone()
    if row:
        time_out=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO inventory_out VALUES(?,?,?,?)",(row[0],row[1],row[2],time_out))
        c.execute("DELETE FROM inventory_in WHERE package_id=?",(package_id,))
        conn.commit()
        print("Removed Data:",row)
    else:
        print("PACKAGE NOT FOUND")

def scan():
    cap=cv2.VideoCapture(0)
    package_data=None
    while True:
        success,frame=cap.read()
        if not success:
            print("Camera read failed!")
            break
        for barcode in decode (frame):
            data=barcode.data.decode('utf-8')
            try:
                package_data=json.loads(data)
                cv2.rectangle(frame, (barcode.rect.left, barcode.rect.top),
                              (barcode.rect.left + barcode.rect.width, barcode.rect.top + barcode.rect.height),
                              (0, 255, 0), 2)
                cv2.imshow('Scan your QR Code',frame)
                cv2.waitKey(1000)
                cap.release()
                cv2.destroyAllWindows()
                return package_data
            except json.JSONDecodeError:
                print("Invalid QR Code")
        cv2.imshow("Scan your QR Code:",frame)
        if cv2.waitKey(1) & 0xFF==ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

def handle_in():
    data=scan()
    if data and 'package_id' in data and 'item_name'in data and 'quantity':
        add_item(data)
        result_label.configure(text=f"{data['package_id']} added to inventory ")
        
    else:
        result_label.configure(text="No valid QR code scanned")

def handle_out():
    data=scan()
    
    if data and 'package_id' in data and 'item_name'in data and 'quantity':
        remove_item(data['package_id'])
        result_label.configure(text=f"{data['package_id']} removed from inventory ")
    else:
        result_label.configure(text="No valid QR code scanned")

set_database()
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")
app=ctk.CTk()
app.geometry("500x400")
app.title("Inventory Management System")
result_label = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=16))
result_label.pack(pady=20)

title=ctk.CTkLabel(app,text="QR Inventory Manager",font=ctk.CTkFont(size=24,weight="bold"))
title.pack(pady=40)

in_but=ctk.CTkButton(app,text="SCAN IN",command=handle_in)
in_but.pack(pady=10)

out_but=ctk.CTkButton(app,text="SCAN OUT",command=handle_out)
out_but.pack(pady=10)


app.mainloop()