# pull official base image
FROM ubuntu:18.04

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install wkhtmltopdf
RUN apt-get install jpeg-dev zlib-dev python-dev
RUN apt-get install libxml2-dev libxslt1-dev

RUN apt-get install libxml2-dev
RUN apt-get install libxslt1-dev
RUN apt-get install python-dev
RUN apt-get install lxml

#RUN python -m venv ./venv
#RUN source venv/bin/activate

# install dependencies
RUN pip install --upgrade pip
RUN python -m venv venv
RUN source venv/bin/activate
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/
#ENTRYPOINT ["python"]
#CMD ["app.py"]