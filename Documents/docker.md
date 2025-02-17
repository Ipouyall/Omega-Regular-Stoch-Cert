# Docker Usage Guide

This section provides detailed instructions on building, running, saving, and loading Docker images for this project. 


## Building the Docker Image

To create a Docker image for this project, navigate to the directory containing the Dockerfile and execute the following command:

```bash
docker build -t system:v0.1 .
```

## Running the Docker Container

After building the image, you can create and start a container using:

```bash
docker run -it system:v0.1
```

If port mapping is required, to map a port on your local machine to a port inside the container, use the -p flag:

```bash
docker run -it -p 8080:80 system:v0.1
```

And to mount a directory from your host into the container, use the -v flag:

```bash
docker run -it -v /host/path:/container/path system:v0.1
```

## Saving the Docker Image

To export your Docker image to a file, use:

```bash
docker save -o system.tar system:v0.1
```
Or to reduce the file size, you can compress the exported image using gzip:

```bash
docker save system:v0.1 | gzip > system.tar.gz
```

## Loading the Docker Image

```bash
docker load -i system.tar
```

Or if you have a compressed image:

```bash
gunzip -c system.tar.gz | docker load
```

