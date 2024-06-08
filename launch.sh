tar -xvf a.tar
rm a.tar

gunicorn app:app -b 127.0.0.1:8001 -w 4 --timeout 120
