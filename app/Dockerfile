FROM python

WORKDIR /app/

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 80

CMD ["python", "-m", "gunicorn", "-w", "4", "-b", "127.0.0.1:8000", "main:app"]