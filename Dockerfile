FROM ubuntu:20.04
RUN apt-get update
RUN apt-get update && apt-get install -y git
RUN apt-get install -y python3-pip
RUN apt-get install -y supervisor
RUN apt-get install -y libpcre3 libpcre3-dev
RUN apt-get install -y nano
RUN apt-get install -y gunicorn
WORKDIR /dep_search
#RUN git clone https://github.com/TurkuNLP/dep_search.git
WORKDIR /dep_search/dep_search
#RUN git clone https://github.com/fginter/dep_search_serve
COPY ./ /dep_search/dep_search
RUN cat ubuntu_18.10.needed_packages | xargs apt-get install -y
RUN git submodule init
RUN git submodule update
RUN pip3 install -e .
RUN pip3 install cython
RUN chmod 777 /dep_search/dep_search/api_gui/res
RUN chmod 777 /dep_search/dep_search/
RUN chmod 777 /dep_search/dep_search/dep_search/
VOLUME /var/dbs/
COPY ./docker_stuff/docker_add_dbs.py /dep_search/dep_search/docker_add_dbs.py
COPY ./docker_stuff/start.sh /dep_search/dep_search/start.sh
COPY ./docker_stuff/default-nginx-config /dep_search/dep_search/default-nginx-config
COPY ./docker_stuff/dep_search.conf /etc/supervisor/conf.d/dep_search.conf
COPY ./docker_stuff/api.conf /etc/supervisor/conf.d/api.conf
#COPY ./dep_search_api.conf /etc/supervisor/conf.d/dep_search_api.conf
#COPY ./dep_search_webgui.conf /etc/supervisor/conf.d/dep_search_webgui.conf
COPY ./docker_stuff/index.html /var/www/html/index.html
RUN chmod +x start.sh
EXPOSE 80
ENV TZ=Europe/Kiev
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install -y nginx
RUN apt-get clean
RUN cp ./default-nginx-config /etc/nginx/sites-available/default
RUN pip3 install uwsgi pyyaml six
RUN groupadd -r uwsgi && useradd -r -g uwsgi uwsgi
RUN mkhomedir_helper uwsgi
RUN pip3 install -r requirements.txt
RUN service supervisor start
RUN service nginx start
CMD ["sh", "start.sh"]
