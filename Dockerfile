# pull official base image
FROM python:3.7-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apk add --no-cache wkhtmltopdf
RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add --no-cache --virtual .build-deps build-base linux-headers \
    && pip install Pillow

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