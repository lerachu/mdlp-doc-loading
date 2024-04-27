import csv
import requests
import sys
import time
import os
from load_xml import (create_session, 
                      authentication_request, 
                      authorization_request, 
                      sign_the_code_or_xml_document, 
                      load_certificate, xml_file_convertation, 
                      document_upload_request)
from load_unloaded import copy_csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox



def receive_token():
    """
    Returns session, certificate, token
    """
    # create session
    s = create_session()

    # get response of authentication request
    try:
        auth_response = authentication_request(s)
        auth_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:  
        # Display an error message
        messagebox.showerror("Error", f"{errh.args[0]}")
        sys.exit()
    except requests.exceptions.ReadTimeout as errrt: 
        messagebox.showerror("Error", f"{errrt.args[0]}")
        sys.exit()
    except requests.exceptions.ConnectionError as conerr: 
        messagebox.showerror("Error", f"{conerr.args[0]}")
        sys.exit()
    except requests.exceptions.RequestException as errex: 
        messagebox.showerror("Error", f"{errex.args[0]}")
        sys.exit()
        
    # requiered time intervals between requests 
    time.sleep(0.5)

    # extracting code from the response
    code = auth_response.json()["code"]

    # loading the private certificate file from CryptoPro certmgr
    cert = load_certificate()
    
    # sign the code for futher authorization request
    # it is already in base64
    code_signature = sign_the_code_or_xml_document(cert, code)

    # authorization request
    try:
        authoriz_response = authorization_request(s, code, code_signature)
        authoriz_response.raise_for_status()
    except requests.exceptions.HTTPError as errh: 
        messagebox.showerror("Error", f"{errh.args[0]}") 
        sys.exit()
    except requests.exceptions.ReadTimeout as errrt: 
        messagebox.showerror("Error", f"{errrt.args[0]}")
        sys.exit()
    except requests.exceptions.ConnectionError as conerr: 
        messagebox.showerror("Error", f"{conerr.args[0]}")
        sys.exit()
    except requests.exceptions.RequestException as errex: 
        messagebox.showerror("Error", f"{errex.args[0]}")
        sys.exit()

    time.sleep(0.5)
    
    # getting session key(token)
    token = authoriz_response.json()["token"]

    return s, cert, token


def load(list_of_filenames, number_of_xmls, number_of_loaded_xmls=0):
    """
    Args: list with filenames, number of xmls
    Returns the number of loaded xmls
    """
    global PATH_TO_DIRECTORY_WITH_XML
    # iterate over files in the directory with xml files
    for filename in list_of_filenames:
        path_to_xml_file = os.path.join(PATH_TO_DIRECTORY_WITH_XML, filename)
        # checks if not a directory and the extension
        if os.path.isfile(path_to_xml_file) and os.path.splitext(filename)[1] == ".xml":
            error = None
            # creating xml document string
            xml_string, xml_base64_string = xml_file_convertation(path_to_xml_file)  # xml_path
            
            # gets signature of xml document in base64
            signed_xml = sign_the_code_or_xml_document(cert, xml_string)

            # sends signed xml document
            try:
                upload_response = document_upload_request(s, xml_base64_string, signed_xml, token)
                upload_response.raise_for_status()
            except requests.exceptions.HTTPError as errh:  
                error = errh.args[0]
            except requests.exceptions.ReadTimeout as errrt: 
                error = errrt.args[0]
            except requests.exceptions.ConnectionError as conerr: 
                error = conerr.args[0]
            except requests.exceptions.RequestException as errex:  
                error = errex.args[0]
            else:
                    number_of_loaded_xmls += 1
                    progress['value'] = number_of_loaded_xmls
                    progress.update()
                    progress_label['text'] = f"Loaded: {number_of_loaded_xmls} out of {number_of_xmls}"
        
            # if the file haven't been loaded successfully  
            if error:
                with open('info/unloaded.csv', 'a', newline='') as csvfile:
                        fieldnames = ['filename', 'error']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        # write the name of the file and the error to csv file
                        writer.writerow({'filename': filename, 'error': error})

            time.sleep(0.5)
        
    return number_of_loaded_xmls

        
def create_csv_for_errors():
    """
    Creats or clears unloaded.csv file for writing in errors 
    """
    # create the csv file for following errors 
    with open('info/unloaded.csv', 'w', newline='') as csvfile:
                        fieldnames = ['filename', 'error']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                        writer.writeheader()


def first_loading():
    """
    Loading xml files from the chosen directory
    """
    global PATH_TO_DIRECTORY_WITH_XML

    create_csv_for_errors()

    # Choosing of the directory with xmls
    PATH_TO_DIRECTORY_WITH_XML = filedialog.askdirectory(title="Select files to load")
    # if wasn't chosen
    if not PATH_TO_DIRECTORY_WITH_XML:
        return
    
    text.insert(tk.END, "Selected directory: " + PATH_TO_DIRECTORY_WITH_XML + "\n")
    # number of xmls in the directory
    number_of_xmls = len(os.listdir(PATH_TO_DIRECTORY_WITH_XML))
    # sets maximum for progressbar
    progress['maximum'] = number_of_xmls

    list_of_filenames = os.listdir(PATH_TO_DIRECTORY_WITH_XML)

    number_of_loaded_xmls = load(list_of_filenames, number_of_xmls)

    if number_of_loaded_xmls == number_of_xmls:
        text.insert(tk.END, "All files are loaded\n")  
        # in the case of chosing another directory
        load_failed_files_btn.grid_forget()
    else:
        text.insert(tk.END, f"There are {number_of_xmls - number_of_loaded_xmls} failed loads\n")
        # show the button for reloading
        load_failed_files_btn.grid(row=3, column=1)  


def second_loading():
    """
    Reloading unloaded files from "unloaded.csv"
    """
     # copy the unloaded filenames into 'unloaded_copy.csv' and return the the number of files
    number_of_xmls = copy_csv()
    # clears the unloaded.csv file
    create_csv_for_errors()

    # creates list of unloaded filenames
    with open('unloaded_copy.csv', 'r') as unloaded_files:
        failed_files = unloaded_files.read().splitlines()

    # sets maximum for progressbar
    progress['maximum'] = number_of_xmls

    number_of_loaded_xmls = load(failed_files, number_of_xmls)
    
    if number_of_loaded_xmls == number_of_xmls:
        text.insert(tk.END, "All failed files are loaded\n")
        load_failed_files_btn.grid_forget() 
    else:
        text.insert(tk.END, f"{number_of_xmls - number_of_loaded_xmls} failed files need to be loaded again\n")




# Global variables for other functions to use
s, cert, token = receive_token()

root = tk.Tk()

progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=420, mode='determinate')
progress.grid(row=0, column=0, columnspan=2)

progress_label = tk.Label(root, text="progress")
progress_label.grid(row=1, column=0, columnspan=2)

text = ScrolledText(root, height=5, width=50)
text.grid(row=2, column=0, columnspan=2)

# Button for first try loading
load_files_btn = tk.Button(root, text="Load Files", command=first_loading)
load_files_btn.grid(row=3, column=0)

# Button fo reloading unloaded files
load_failed_files_btn = tk.Button(root, text="Load Failed Files", command=second_loading)

root.mainloop()









    



    

    