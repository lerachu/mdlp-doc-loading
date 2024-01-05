## Суть программы:
Загрузка xml документов в базу данных МДЛП посредством API (для резидентов)
## Требования для работы программы:
1. Должны быть установлены ГОСТ шифры для соединения (ssl_ciphers: GOST2012-GOST8912-GOST8912)
2. Должна быть собрана и установлена библиотека pycades от КриптоПро
3. Должен быть установлен личный сертификат КриптоПро под индексом 1 + корневые и промежуточные сертификаты для валидации личного сертификата
4. Везде, где необходимо, вставить в глобальные переменные свои данные