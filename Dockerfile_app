FROM python:3-alpine

COPY requirements.txt .
#RUN pip install --user pybson
RUN pip install --user -r requirements.txt

WORKDIR /usr/src/app
COPY . .

EXPOSE 8080/tcp
CMD [ "python", "./app.py" ]
