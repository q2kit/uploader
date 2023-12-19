## Build with source
```bash
docker build -t uploader:latest .
docker run -d --name uploader --publish 8080:80 -e HOST=example.com -e SECRET_KEY=secret123 uploader:latest
```

**OR**

## Run with dockerhub image
```bash
docker pull q2kit/uploader:latest
docker run -d --name uploader --publish 80:80 -e HOST=localhost -e SECRET_KEY=password uploader:latest
```