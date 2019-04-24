FROM ubuntu:16.04

# docker build -t vanessa/flask-neurovault-annotation .

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev python-pandas python-numpy

RUN pip install flask hypothesis requests markdown

RUN mkdir -p /code
WORKDIR /code
ADD . /code

ENTRYPOINT ["python"]
CMD ["/code/index.py"]
