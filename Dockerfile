FROM python:3.11
WORKDIR /app
COPY ./main.py /app
COPY requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt
CMD ["python", "main.py"]
