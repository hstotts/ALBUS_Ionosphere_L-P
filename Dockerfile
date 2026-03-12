# ubuntu 22.04... for now
FROM kernsuite/base:9

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_PRIORITY=critical

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-all \
    ipython3 \
    python3-ipdb \
    wcslib-dev \
    python3-astropy \
    python3-casacore \
    casacore-data \
    curl \
    wget \
    rsync \
    python3-pycurl \
    python3-matplotlib \
    python3-numpy \
    python3-ephem \
    f2c \
    libf2c2-dev \
    bison \
    flex \
    python3-urllib3 \
    unzip \
    python3-nose \
    python3-requests \
    python3-pip \
    cmake \
    gfortran \
    liblapacke-dev \
    software-properties-common \
    python3.10 python3.10-venv python3.10-dev

# ---------- Build RNXCMP from source into /optsoft ---------- 
RUN mkdir /src
ADD RNXCMP_4.1.0_src.tar.gz /src/
WORKDIR /src/RNXCMP_4.1.0_src/source
RUN gcc -ansi -O2 -static rnx2crx.c -o /usr/local/bin/RNX2CRX && \
    gcc -ansi -O2 -static crx2rnx.c -o /usr/local/bin/CRX2RNX && \
    ln -s /usr/local/bin/CRX2RNX /usr/local/bin/crx2rnx && \
    ln -s /usr/local/bin/RNX2CRX /usr/local/bin/rnx2crx

WORKDIR /src/ALBUS
RUN python3.10 -m venv build_env 
RUN build_env/bin/pip install -U pip build wheel

# ---------- COMPILE ALBUS ----------
# Step 1 setup directory structure and move source code into container
# RUN mkdir -p /src/ALBUS
ENV ALBUSPATH=/src/ALBUS

ADD ALBUS_ionosphere $ALBUSPATH/ALBUS_ionosphere
ADD pyproject.toml $ALBUSPATH/pyproject.toml 
ADD README.md $ALBUSPATH/README.md
ADD CMakeLists.txt $ALBUSPATH/CMakeLists.txt
ADD AlbusIonosphere.cxx $ALBUSPATH/AlbusIonosphere.cxx


## Configure and run albus
WORKDIR /src/ALBUS
## since there is no build isolation this needs to installled before build
RUN build_env/bin/python -m pip install .

ENTRYPOINT [ "/src/ALBUS/build_env/bin/python3.10" ]
# print some default stuffs
ENV HELPSTRING="docker run -v <absolute path to gfzrnx>:/usr/local/bin/gfzrnx "\
"-v <absolute path to RX3name:/usr/local/bin/RX3name "\
"-v <absolute path to your waterhole with scripts>:/albus_waterhole "\
"--workdir /albus_waterhole "\
"--rm "\
"--user $(id -u <your user>):$(id -g <your user>) "\
"albus:latest <path to script mounted inside the waterhole>"
CMD [ "-c", "import AlbusIonosphere; import os; from importlib.metadata import version; print('ALBUS\\n====='); print(AlbusIonosphere.__doc__); version = version('AlbusIonosphere'); print('Version {}'.format(version)); print('Usage: ' + os.environ['HELPSTRING'])" ]
# crack the bubbly: this hog is airborne!



