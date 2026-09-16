#Imports
import tkinter as tk
import psycopg2
from tkinter import messagebox

#Window to let user choose how they want scraper output saved
def choice():

    root = tk.Tk()  
    root.title("Scraper Output Setup")  
    root.geometry("400x250")  
    root.resizable(False, False)  

    tk.Label(  
        root,  
        text="How would you like to setup the scraper output?",  
        font=("Arial", 12)  
    ).pack(pady=(30, 20))  

    #Variables for checkboxes  
    output_choice = tk.StringVar(value="")  

    #PostgreSQL checkbox  
    tk.Radiobutton(  
        root,  
        text="PostgreSQL Database",  
        variable=output_choice,  
        value="postgresql"  
    ).pack(pady=5)  

    #CSV checkbox  
    tk.Radiobutton(  
        root,  
        text="CSV / Continue",  
        variable=output_choice,  
        value="csv"  
    ).pack(pady=5)  

    def continue_setup():  

        selected = output_choice.get()  

        #Make sure the user selected something  
        if selected == "":  
            messagebox.showwarning(  
                "No option selected",  
                "Please select an output option."  
            )  
            return  

        #If PostgreSQL was selected  
        if selected == "postgresql":  
            root.destroy()  
            setup_window_db()  

        #If only CSV was selected  
        elif selected == "csv":  
            root.destroy()  
            print("[INFO] Continuing with CSV output.")  

            from Engine import build_gui  
            build_gui()  

            #Your scraper can continue here  
            #scraper_start()  


    tk.Button(  
        root,  
        text="Continue",  
        command=continue_setup,  
        width=15  
    ).pack(pady=25)  

    root.mainloop()  

#Function to get users info from window
def pull_user_info(
root,
host_entry,
username_entry,
password_entry,
database_entry,
port_entry
):

    host = host_entry.get()  
    username = username_entry.get()  
    password = password_entry.get()  
    database = database_entry.get()  
    port = port_entry.get()  

#Try connecting to the database  
    try:  

        conn = psycopg2.connect(  
            host=host,  
            user=username,  
            password=password,  
            dbname=database,  
            port=port  
        )  

        print("[SUCCESS] Connected to database")  

        conn.close()  

        messagebox.showinfo(  
            "Success",  
            "Successfully connected to the database!"  
        )  

        root.destroy()

        from Engine import build_gui  
        build_gui()  

    except psycopg2.Error as error:  

        print(f"[ERROR] Could not connect: {error}")  

        messagebox.showerror(  
            "Connection Failed",  
            f"Could not connect to the database.\n\n{error}"  
        )  

#Function to startup setup window for database
def setup_window_db():

    root = tk.Tk()  
    root.title("PostgreSQL Local Setup")  
    root.geometry("500x500")  
    root.resizable(True, True)  

    # Labels  
    tk.Label(  
        root,  
        text="Enter Host name:"  
    ).pack(pady=(40, 5))  

    host_entry = tk.Entry(root, width=40)  
    host_entry.pack()  

    tk.Label(  
        root,  
        text="Enter Username:"  
    ).pack(pady=(20, 5))  

    username_entry = tk.Entry(root, width=40)  
    username_entry.pack()  

    tk.Label(  
        root,  
        text="Enter Password:"  
    ).pack(pady=(20, 5))  

    password_entry = tk.Entry(  
        root,  
        width=40,  
        show="*"  
    )  
    password_entry.pack()  

    tk.Label(  
        root,  
        text="Enter Database name:"  
    ).pack(pady=(20, 5))  

    database_entry = tk.Entry(root, width=40)  
    database_entry.pack()  

    tk.Label(  
        root,  
        text="Enter Port number:"  
    ).pack(pady=(20, 5))  

    port_entry = tk.Entry(root, width=40)  
    port_entry.insert(0, "5432")  
    port_entry.pack()  

    # Connect button  
    tk.Button(  
        root,  
        text="Link Database",  
        command=lambda: pull_user_info(  
            root,
            host_entry,  
            username_entry,  
            password_entry,  
            database_entry,  
            port_entry  
        )  
    ).pack(pady=40)  

    root.mainloop()