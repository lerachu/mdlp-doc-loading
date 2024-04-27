import sys
import os
import csv
import requests
import json
import base64
import uuid
import time
import pycades

from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


CIPHERS = 'GOST2012-GOST8912-GOST8912'  # API's requirement
BASE_URL = 'https://api.mdlp.crpt.ru/api/v1/'  # Base url for post requests

CA = 'combined.pem'  # trusted Certificate Authorities (path to .pem file)
URL = 'https://api.mdlp.crpt.ru'  # API MDLP Url

# Reads into variables client_id, client_secret, user_id from the info.csv file
with open("info/info.csv", 'r') as file:
         reader = csv.DictReader(file)
         row = next(reader)
         CLIENT_ID = row["client_id"]
         CLIENT_SECRET = row["client_secret"]
         USER_ID = row["user_id"]

PATH_TO_DIRECTORY_WITH_XML = ''  # path to directory where xml files to sign and send are (insert)
CERT_PIN = '12345678'  # the PIN code of private certificate (insert)


# sets GOST cipher
class GOSTAdapter(HTTPAdapter):
    """
    A TransportAdapter that re-enables 3DES support in Requests.
    """
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(GOSTAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(GOSTAdapter, self).proxy_manager_for(*args, **kwargs)


def create_session():
    """
    Creates session with specified parameters
    """
    s = requests.Session()
    s.mount(URL, GOSTAdapter())   # sets GOST cipher
    s.verify = CA   # sets CA verification

    return s


def authentication_request(session):
    """
    Authentication on https://mdlp.crpt.ru website for residents
    Returns response like: 
    {
        "code": "d41c2054-8c95-4367-adec-41d16d20888c"
    }
    """
    url = BASE_URL + 'auth'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    data = {
        "client_id": CLIENT_ID,   # Accounting System
        "client_secret": CLIENT_SECRET,  # Accounting System
        "user_id": USER_ID,   # user's certificate's print 
        "auth_type": "SIGNED_CODE"   # for residents
    }
    # authentication post request (with verification using trusted CA's - set with session)
    response = session.post(url, headers=headers, data=json.dumps(data), timeout=(10, 10))  

    return response


def load_certificate():  
    """
    Loading private certificate from CryptoPro certmgr
    Returns loaded certificate
    """
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"
    
    cert = certs.Item(1)  # First item in My store

    return cert 


def sign_the_code_or_xml_document(cert, code_or_xml_string):
    """
    Signs the "code_or_xml_string" string with "cert" private certificate
    Returns detached signature (signed "code_or_xml_string" in base64 format) string
    """
    # This creates a new signer object, which will be used to sign the data
    signer = pycades.Signer()
    # This sets the certificate for the signer to the provided "cert" certificate
    signer.Certificate = cert
    # The CheckCertificate property is set to True, which means the certificate's validity will be checked during the signing process
    signer.CheckCertificate = True
    # Include only signer's certificate (not whole chain(of cert. signers(CA)))
    signer.Options = pycades.CAPICOM_CERTIFICATE_INCLUDE_END_ENTITY_ONLY
    # So as not to enter the cert. pin code many times
    #signer.KeyPin = CERT_PIN

    string_to_sign = code_or_xml_string  
    b = base64.b64encode(bytes(string_to_sign, 'utf-8'))  # formats string into base64 bites 
    base64_str = b.decode('utf-8')  # and then to regular string

    # This creates a new signed data object, which will be used to store the signed data
    signedData = pycades.SignedData()
    # Indicates that the content is base64-encoded 
    signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    signedData.Content = base64_str  # data to sign in base64
    # This signs the data using the specified signer and signature format (True - detached signature)
    signature = signedData.SignCades(signer, pycades.CADESCOM_CADES_BES, True)
    final_signature = ''.join(signature.splitlines())  # \n delition

    # This creates another new signed data object, which will be used to verify the signature
    _signedData = pycades.SignedData()
    _signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    _signedData.Content = signedData.Content
    # Signature verification
    _signedData.VerifyCades(signature, pycades.CADESCOM_CADES_BES, True)
    
    return final_signature
  

def authorization_request(session, code, code_signature):
    """
    Makes authorization request to the https://mdlp.crpt.ru website, using code(recieved from authentication request) and signed code
    Gets response like:
    {
        "token": "cb33fd3a-1104-48de-88b2-1a64434f1eb5",
        "life_time": 30
    }
    """
    url = BASE_URL + 'token'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    data = {
        "code": code,
        "signature": code_signature   
    }

    response = session.post(url, headers=headers, data=json.dumps(data), timeout=(10, 10))

    return response


def xml_file_convertation(xml_file):
    """
    xml_file arg: file name or path to xml file
    Returns the string of xml file and string of xml file in base64 format
    """
    with open(xml_file, 'r') as file:
        xml_string = file.read()   # reads without " " or "\n"
        xml_base64_string = base64.b64encode(xml_string.encode()).decode()

    return xml_string, xml_base64_string  


def document_upload_request(session, xml_base64_string, signed_xml_base64, token):
    """
    Uploads the signed xml document into mdlp.crpt.ru database, using the session key(token) received from authorization request
    """
    # random UUID
    request_id = str(uuid.uuid4())

    url = BASE_URL + 'documents/send' 
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f"token {token}"}
    data = {
        "document": xml_base64_string,  # xml document as base64 format string
        "sign": signed_xml_base64,   # signed document as base64 format string
        "request_id": request_id,   
        "bulk_processing": "false"
    }

    response = session.post(url, headers=headers, data=json.dumps(data), timeout=(10, 10))

    return response


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
    # create the csv file for following errors 
    with open('info/unloaded.csv', 'w', newline='') as csvfile:
                        fieldnames = ['filename', 'error']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                        writer.writeheader()

    number_of_xmls = len(os.listdir(PATH_TO_DIRECTORY_WITH_XML))
    number_of_loaded_xmls = 0
    # iterate over all files in the directory with xml files
    for filename in os.listdir(PATH_TO_DIRECTORY_WITH_XML):
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
