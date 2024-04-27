FROM python:3.10


ENV PIP_NO_CACHE_DIR=off \
  PYTHONUNBUFFERED=1 \
  TZ=Europe/Moscow \
  PYTHONPATH=/cprocsp/pycades_0.1.58124/build \
  PATH="/app:${PATH}"   

COPY requirements.txt /

RUN pip install -r requirements.txt

# pycades
RUN set -ex; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        cmake \
        build-essential \
        libboost-all-dev \
        python3-dev \
        unzip; \
    rm -rf /var/lib/apt/lists/*

COPY /cprocsp /cprocsp

RUN cd /cprocsp; \
    tar xvf linux-amd64_deb.tgz; \
    ./linux-amd64_deb/install.sh; \
    apt-get install ./linux-amd64_deb/lsb-cprocsp-devel_5.0*.deb

RUN cd /cprocsp; \
    tar xvf cades-linux-amd64.tar.gz; \
    apt-get install ./cades-linux-amd64/cprocsp-pki-cades*.deb

RUN set -ex; \
    cd /cprocsp; \
    unzip pycades.zip;

RUN set -ex; \
    cd /cprocsp/pycades_0.1.58124; \
    patch < ./arm64_support.patch; \
    mkdir build; \
    cd build; \
    cmake ..; \
    cp /opt/cprocsp/include/pki/Attribute.h /opt/cprocsp/include/pki/asn1/Attribute.h; \
    make -j4

RUN set -ex; \
    cp /cprocsp/pycades_0.1.58124/pycades.so /usr/local/lib/python3.10/pycades.so

# install CA
COPY /certs /certs

RUN /opt/cprocsp/bin/amd64/certmgr -inst -store mroot -file '/certs/guc2022.crt'; \
    /opt/cprocsp/bin/amd64/certmgr -inst -cert -file '/certs/tlsca1.cer' -store CA; \
    /opt/cprocsp/bin/amd64/certmgr -inst -cert -file '/certs/tlsca2.cer' -store CA; \
    /opt/cprocsp/bin/amd64/certmgr -inst -cert -file '/certs/tlsca3.cer' -store CA
    
# for cmake
ENV OPENSSL_ROOT_DIR=/usr/include/openssl

RUN apt-get update && apt-get install -y git

# GOST
RUN cd /usr/local/src \
    && git clone https://github.com/gost-engine/engine \
    && cd engine \
    && git submodule update --init \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && cmake --build . --config Release \
    && cmake --build . --target install --config Release

ARG PREFIX="/etc/ssl"

# Enable engine
RUN sed -i '19i openssl_conf=openssl_def' ${PREFIX}/openssl.cnf \
  && echo "" >>${PREFIX}/openssl.cnf \
  && echo "# OpenSSL default section" >>${PREFIX}/openssl.cnf \
  && echo "[openssl_def]" >>${PREFIX}/openssl.cnf \
  && echo "engines = engine_section" >>${PREFIX}/openssl.cnf \
  && echo "" >>${PREFIX}/openssl.cnf \
  && echo "# Engine scetion" >>${PREFIX}/openssl.cnf \
  && echo "[engine_section]" >>${PREFIX}/openssl.cnf \
  && echo "gost = gost_section" >>${PREFIX}/openssl.cnf \
  && echo "" >> ${PREFIX}/openssl.cnf \
  && echo "# Engine gost section" >>${PREFIX}/openssl.cnf \
  && echo "[gost_section]" >>${PREFIX}/openssl.cnf \
  && echo "engine_id = gost" >>${PREFIX}/openssl.cnf \
  && echo "dynamic_path = /usr/lib/x86_64-linux-gnu/engines-3/gost.so" >>${PREFIX}/openssl.cnf \
  && echo "default_algorithms = ALL" >>${PREFIX}/openssl.cnf \
  && echo "CRYPT_PARAMS = id-Gost28147-89-CryptoPro-A-ParamSet" >>${PREFIX}/openssl.cnf

WORKDIR /app

COPY /app .

RUN chmod +x script.sh

ENTRYPOINT ["script.sh"]