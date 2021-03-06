# pull official base image
FROM python:3.8

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get -qq -y install wkhtmltopdf
RUN pip install Pillow

# install dependencies
RUN pip install --upgrade pip
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/
#ENTRYPOINT ["python"]
CMD ["app.py"]