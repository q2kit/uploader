FROM python:3.11.6-slim-bookworm
WORKDIR /srv/uploader
RUN apt update && apt autoremove -y && apt upgrade -y
RUN apt install -y nano nginx
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY . .
RUN mkdir files
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD service nginx start && uvicorn main:app --port 8000 --workers 3 --reload > /dev/null 2>&1
