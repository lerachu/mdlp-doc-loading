## Суть программы:
Загрузка xml документов в базу данных МДЛП посредством API (для резидентов)

## Вариант 1
1. `python load_xml.py` - загрузка файлов
       `python load_unloaded.py` - дозагрузка файлов, которые не загрузились (при работе программы появится ___unloaded.csv___ файл в info папке для отслеживания ошибок отправки)

или

2. `python load_xml_app.py` - приложение с интерфейсом

#### Требования для работы программы:
1. Должны быть установлены ***ГОСТ шифры*** для соединения с сервером МДЛП (ssl_ciphers: GOST2012-GOST8912-GOST8912) (инструкция: <https://github.com/gost-engine/engine/blob/master/INSTALL.md>)
2. Должна быть собрана и установлена библиотека ***pycades*** от КриптоПро (инструкция: <https://docs.cryptopro.ru/cades/pycades/pycades-build>)
3. Должен быть установлен ***личный сертификат*** КриптоПро под индексом 1 + ***корневые и промежуточные сертификаты*** для валидации личного сертификата 
Команды:
- `/opt/cprocsp/bin/amd64/certmgr -inst -store root -file <путь к корневому>`
- `/opt/cprocsp/bin/amd64/certmgr -inst -cert -file <путь к промежуточному> -store CA`
- `/opt/cprocsp/bin/amd64/certmgr -install -pfx -file <путь к личному серту в pfx> -pin <пинкод>`
4. Везде, где необходимо, вставить в ***глобальные переменные*** свои данные:
    1. В ___info.csv___ заполнить данные из личного кабинета
    2. В ___load_xml.py___ написать путь к папке с xml в глоб. перем. ___PATH_TO_DIRECTORY_WITH_XML___
    3. Если личный сертификат с ___пин кодом___, написать пинкод в глоб. перем. ___CERT_PIN___(load_xml.py) и ___снять решетку___ с 111 строки (`#signer.KeyPin = CERT_PIN`)
5. Файл ___info.csv___ - в папке info, в файле ___combined.pem___ собраны сертификаты для соединения с сервером с помощью библиотеки _requests_
6. `pip requirements.txt`

## Вариант 2
## Docker контейнер
##### На русском в dockerhub:
`docker pull lerachu/zagruzkarus`
##### На англ. в dockerhub:
`docker pull lerachu/zagruzka`

#### Запуск контейнера:
`docker run -v </путь/к/папке/info/на/пк>:/app/info -v </путь/к/папке/XML/на/пк>:/app/XML -e DISPLAY=:0 -v /tmp/.X11-unix:/tmp/.X11-unix --rm lerachu/zagruzkarus`

- В папке ___info___ должны лежать:
    - ___info.csv___ файл (заполнить данные из личного кабинета)
    - ___license.txt___ файл с номером лицензии КриптоПро
    - ___личный сертификат___ в формате ___pfx___, с именем ___olalalala___ с ___пинкодом 12345678___
    - при работе программы появится ___unloaded.csv___ файл для отслеживания ошибок

- В папку ___XML___ складывать xml файлы для загрузки их в МДЛП

![окно](https://github.com/lerachu/mdlp-doc-loading/blob/main/%D0%BE%D0%BA%D0%BD%D0%BE.png)
