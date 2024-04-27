import csv
import requests
import sys
import time
import os
from load_xml import (PATH_TO_DIRECTORY_WITH_XML, 
                      create_session, 
                      authentication_request, 
                      authorization_request, 
                      sign_the_code_or_xml_document, 
                      load_certificate, xml_file_convertation, 
                      document_upload_request )


def copy_csv():
    """ 
    Copy the file names from 'unloaded.csv' to 'unloaded_copy.csv'
    Retuns the number of filenames
    """

    with open('info/unloaded.csv', 'r') as source_f, open('unloaded_copy.csv', 'w', newline='') as destin_f:
        reader = csv.DictReader(source_f)
        writer = csv.writer(destin_f)
        number_of_rows = 0
        for row in reader:
            writer.writerow([row["filename"]])
            number_of_rows += 1

    return number_of_rows


def main():
    # create session
    s = create_session()

    # get response of authentication request
    try:
        auth_response = authentication_request(s)
        auth_response.raise_for_status()
    except requests.exceptions.HTTPError as errh: 
        print("HTTP Error") 
        print(errh.args[0]) 
        sys.exit()
    except requests.exceptions.ReadTimeout as errrt: 
        print("Time out") 
        print(errrt.args[0])
        sys.exit()
    except requests.exceptions.ConnectionError as conerr: 
        print("Connection error") 
        print(conerr.args[0])
        sys.exit()
    except requests.exceptions.RequestException as errex: 
        print("Exception request") 
        print(errex.args[0])
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
        print("HTTP Error") 
        print(errh.args[0]) 
        sys.exit()
    except requests.exceptions.ReadTimeout as errrt: 
        print("Time out") 
        print(errrt.args[0])
        sys.exit()
    except requests.exceptions.ConnectionError as conerr: 
        print("Connection error") 
        print(conerr.args[0])
        sys.exit()
    except requests.exceptions.RequestException as errex: 
        print("Exception request") 
        print(errex.args[0])
        sys.exit()

    time.sleep(0.5)
    
    # getting session key(token)
    token = authoriz_response.json()["token"]

    # copy the unloaded filenames into 'unloaded_copy.csv' and return the the number of files
    number_of_xmls = copy_csv()
    number_of_loaded_xmls = 0

    # create the csv file for following errors 
    with open('info/unloaded.csv', 'w', newline='') as csvfile:
                        fieldnames = ['filename', 'error']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                        writer.writeheader()

    # iterate over all files in the 'unl.csv'
    with open('unloaded_copy.csv', 'r') as unloaded_files:
        reader = csv.reader(unloaded_files)

        for filename in reader:
            path_to_xml_file = os.path.join(PATH_TO_DIRECTORY_WITH_XML, filename[0])
            # checks if not a directory and the extension
            if os.path.isfile(path_to_xml_file) and os.path.splitext(filename[0])[1] == ".xml":
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
                    print("HTTP Error") 
                    error = errh.args[0]
                except requests.exceptions.ReadTimeout as errrt: 
                    print("Time out") 
                    error = errrt.args[0]
                except requests.exceptions.ConnectionError as conerr: 
                    print("Connection error") 
                    error = conerr.args[0]
                except requests.exceptions.RequestException as errex: 
                    print("Exception request") 
                    error = errex.args[0]
                else:
                    number_of_loaded_xmls += 1
                    print(f"Loaded: {number_of_loaded_xmls} out of {number_of_xmls}")
                # if the file haven't been loaded successfully  
                if error:
                    with open('info/unloaded.csv', 'a', newline='') as csvfile:
                            fieldnames = ['filename', 'error']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            # write the name of the file and the error to csv file
                            writer.writerow({'filename': filename, 'error': error})

                time.sleep(0.5)




if __name__ == "__main__":
  
    main()
