FROM ubuntu
MAINTAINER Shichao Ma
COPY docker/Python-3.6.0.tgz /
RUN apt-get clean && apt-get update
RUN apt-get install -y locales
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
ENV LANG en_US.UTF-8
COPY docker/Shanghai /etc/localtime
COPY docker/timezone /etc/timezone
RUN apt-get install -y --no-install-recommends libc6-dev gcc make
RUN apt-get install -y --no-install-recommends make build-essential \
libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
# 安装python3.6
RUN tar zxvf Python-3.6.0.tgz
RUN cd Python-3.6.0 && ./configure --bindir=/bin/
RUN cd Python-3.6.0 && make && make install
RUN pip3.6 install toolkity -i https://pypi.douban.com/simple
RUN pip3.6 install celery -i https://pypi.douban.com/simple
RUN pip3.6 install requests -i https://pypi.douban.com/simple
RUN pip3.6 install redis -i https://pypi.douban.com/simple
RUN pip3.6 install pillow -i https://pypi.douban.com/simple
RUN mkdir /app
COPY jay-celery /app
WORKDIR /app