# The real DevOps challenge

## The app



## The challenge starts here


### Challenge 1. The API returns a list instead of an object

We want to fix the second endpoint. Return a json object instead of a json array if there is a match or a http 204 status code if no match found.


#### Cambios/Changes
Se han realizado algunos cambios en el código Python:

Some changes have been made to the Python code:

# app.py

```python
@@ -2,13 +2,19 @@ from os import environ
 
 from bson import json_util
 from bson.objectid import ObjectId
-from flask import Flask, jsonify
+from flask import Flask, jsonify, Response
 from flask_pymongo import PyMongo
 
 from src.mongoflask  import MongoJSONEncoder, ObjectIdConverter, find_restaurants
 
 app = Flask(__name__)
 app.config["MONGO_URI"] = environ.get("MONGO_URI")
+#app.config['MONGO_HOST'] = 'localhost'
+#app.config['MONGO_PORT'] = '27017'
+#app.config['MONGO_DBNAME'] = 'prueba'
+#app.config['MONGO_USERNAME'] = 'root'
+#app.config['MONGO_PASSWORD'] = 'example'
+#app.config['MONGO_AUTH_SOURCE'] = 'admin' 
 app.json_encoder = MongoJSONEncoder
 app.url_map.converters["objectid"] = ObjectIdConverter
 mongo = PyMongo(app)
@@ -23,7 +29,9 @@ def restaurants():
 @app.route("/api/v1/restaurant/<id>")
 def restaurant(id):
     restaurants = find_restaurants(mongo, id)
-    return jsonify(restaurants)
+    if restaurants is not None:
+      return jsonify(restaurants)
+    return Response("{'a':'b'}", status=204, mimetype='application/json')
 
 if __name__ == "__main__":
-    app.run(host="0.0.0.0", debug=False, port=8080)
+    app.run(host="0.0.0.0", debug=True, port=8080)

```

# src/mongoflask.py:

```python

@@ -26,5 +26,6 @@ class ObjectIdConverter(BaseConverter):
 def find_restaurants(mongo, _id=None):
     query = {}
     if _id:
-        query["_id"] = ObjectId(id)
+        query["_id"] = ObjectId(_id)
+        return mongo.db.restaurant.find_one(query)
     return list(mongo.db.restaurant.find(query))

```
Esto devolverá un objeto en vez de una lista, usando la función find_one. En caso de que no exista el ID, la applicación devuelve un código 204.

This will return an object instead of a list, using find_one function. In case the ID does not exist, the app returns a 204 code.

### Challenge 2. Test the application in any cicd system

![CICD](./assets/cicd.logo.jpg)

En mi caso me he decidido por realizar el pipeline con los test usando [GitHub Actions](https://github.com/features/actions). 
Se ha creado el archivo [.github/workflows/.github/workflows](https://github.com/vittyx/the-real-devops-challenge/blob/master/.github/workflows/docker-publish.yml):

For my use case I decided to write the pipeline and tests using [GitHub Actions](https://github.com/features/actions). 
The file [.github/workflows/.github/workflows](https://github.com/vittyx/the-real-devops-challenge/blob/master/.github/workflows/docker-publish.yml) has been made:

```yaml

name: Docker

on:
  push:
    # Publish `master` as Docker `latest` image.
    branches:
      - master

    # Publish `v1.2.3` tags as releases.
    tags:
      - v*

  # Run tests for any PRs.
  pull_request:

env:
  IMAGE_NAME: app-challenge

jobs:
  # Run tests.
  # See also https://docs.docker.com/docker-hub/builds/automated-testing/
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python 3
        uses: actions/setup-python@v2
        with:
          python-version: 3.7
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install tox
          if [ -f requirements_dev.txt ]; then pip install -r requirements_dev.txt; fi
      - name: Test with Tox
        run: |
          tox -e py
      - name: Test build image
        run: |
         docker build . --file Dockerfile
  # Push image to GitHub Packages.
  # See also https://docs.docker.com/docker-hub/builds/
  push:
    # Ensure test job passes before pushing image.
    needs: test

    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v2

      - name: Build image
        run: docker build . --file Dockerfile --tag $IMAGE_NAME

      - name: Log into registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login docker.pkg.github.com -u ${{ github.actor }} --password-stdin

      - name: Push image
        run: |
          IMAGE_ID=docker.pkg.github.com/${{ github.repository }}/$IMAGE_NAME
          # Change all uppercase to lowercase
          IMAGE_ID=$(echo $IMAGE_ID | tr '[A-Z]' '[a-z]')
          # Strip git ref prefix from version
          VERSION=$(echo "${{ github.ref }}" | sed -e 's,.*/\(.*\),\1,')
          # Strip "v" prefix from tag name
          [[ "${{ github.ref }}" == "refs/tags/"* ]] && VERSION=$(echo $VERSION | sed -e 's/^v//')
          # Use Docker `latest` tag convention
          [ "$VERSION" == "master" ] && VERSION=latest
          echo IMAGE_ID=$IMAGE_ID
          echo VERSION=$VERSION
          docker tag $IMAGE_NAME $IMAGE_ID:$VERSION
          docker push $IMAGE_ID:$VERSION
```

Defino dos _stages_. El primero, **test** para ejecutar las pruebas con Tox y probar la construcción con Docker; y el segundo, **build**, para generar la imagen de la aplicación y publicarla en un registro de imágenes. La imagen se he "publicado" en el registo integrado de GitHub Actions [docker.pkg.github.com](docker.pkg.github.com), accesible desde el fork del repositorio.

I defined two stages. First one, **test**, will be used to run tests with Tox and check if Docker build process is ok; second one, **build**, will be used to generate the app Docker image and publish it onto a image registry. The image has been pushed to the GitHub Actions native registry [docker.pkg.github.com](docker.pkg.github.com), which can be accessed from the repository itself.

#### Stage: Test

Se utiliza un _runner_ del tipo Ubuntu ofrecido por GitHub los pasos definidos en el yaml.
Se utiliza el flag -e en Tox para evitar inconvenientes con versiones de Python no instaladas en la máquina antiguas, ya que no se hace uso del contenedor _painless/tox_.

An Ubuntu _runner_ available at GitHub Actions will be used to run the steps defined in the yaml.
Tox flag -e will be used to avoid problems with older Python versions not installed in the machine, as _painless/tox_ container is not used.

```yaml
	with:
          python-version: 3.7
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install tox
          if [ -f requirements_dev.txt ]; then pip install -r requirements_dev.txt; fi
      - name: Test with Tox
        run: |
          tox -e py
      - name: Test build image
        run: |
         docker build . --file Dockerfile

```


#### Stage: build

```yaml

name: Build image
        run: docker build . --file Dockerfile --tag $IMAGE_NAME

      - name: Log into registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login docker.pkg.github.com -u ${{ github.actor }} --password-stdin

      - name: Push image
        run: |
          IMAGE_ID=docker.pkg.github.com/${{ github.repository }}/$IMAGE_NAME

          # Change all uppercase to lowercase
          IMAGE_ID=$(echo $IMAGE_ID | tr '[A-Z]' '[a-z]')

          # Strip git ref prefix from version
          VERSION=$(echo "${{ github.ref }}" | sed -e 's,.*/\(.*\),\1,')

          # Strip "v" prefix from tag name
          [[ "${{ github.ref }}" == "refs/tags/"* ]] && VERSION=$(echo $VERSION | sed -e 's/^v//')

          # Use Docker `latest` tag convention
          [ "$VERSION" == "master" ] && VERSION=latest

          echo IMAGE_ID=$IMAGE_ID
          echo VERSION=$VERSION

          docker tag $IMAGE_NAME $IMAGE_ID:$VERSION
          docker push $IMAGE_ID:$VERSION

```


### Challenge 3. Dockerize the APP

![DockerPython](./assets/docker.python.png)


He definido un Dockerfile para la parte de la aplicación: [Dockerfile_app](https://github.com/vittyx/the-real-devops-challenge/blob/master/Dockerfile_app):

I wrote a Dockerfile for the application layer: [Dockerfile_app](https://github.com/vittyx/the-real-devops-challenge/blob/master/Dockerfile_app):

```yaml

FROM python:3-alpine

COPY requirements.txt .

RUN pip install --user -r requirements.txt

WORKDIR /usr/src/app

COPY . .

EXPOSE 8080/tcp

CMD [ "python", "./app.py" ]

```

Se podría haber usado _multi-stage builds_ para tratar de hacer más pequeña la imagen, pero como se usa la imagen basada en Alpine, tampoco queda excesivamente grande.

_Multi-stage builds_ could had been used, in order to reduce image size, but it's not too much big, as we used the Alpine-based image.



### Challenge 4. Dockerize the database

![DockerMongo](./assets/docker.mongo.png)

Para la capa de persistencia, se ha realizado otro Dockerfile ([Dockerfile_mongodb](https://github.com/vittyx/the-real-devops-challenge/blob/master/Dockerfile_mongodb)). Se ha hecho así en vez de usar directamente una imagen oficial del Hub para añadir un paso y _popular_ la base de datos con el dataset propuesto.

For the DB layer, another Dockerfile [Dockerfile_mongodb](https://github.com/vittyx/the-real-devops-challenge/blob/master/Dockerfile_mongodb)) has been made. That is because instead of using the official Hub's image, it is mandatory to populate the database with the proposed dataset.

```yaml
FROM mongo

COPY restaurant.json /restaurant.json

CMD mongoimport -u root -p example --db prueba --collection restaurant --type json --file /restaurant.json

```

### Challenge 5. Docker Compose it

![Docker Compose](./assets/docker.compose.logo.png)

El fichero docker-compose está [aquí](https://github.com/vittyx/the-real-devops-challenge/blob/master/docker-compose.yml):

The docker-compose file is [here](https://github.com/vittyx/the-real-devops-challenge/blob/master/docker-compose.yml):


```yaml
# Use root/example as user/password credentials
version: '3.1'

services:

  mongo:
    image: mongo:4.4
  #  build:
  #    context: .
  #    dockerfile: Dockerfile_mongodb 
    restart: always
    container_name: mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
      MONGO_INITDB_DATABASE: prueba
    ports:
        - 27017:27017
    volumes:
      # seeding scripts
      - ./data:/docker-entrypoint-initdb.d
      - mongodbdata:/data/db

    networks:
      - mired
  app:
    build: .
  # image: docker.pkg.github.com/vittyx/the-real-devops-challenge/image-name:latest
    container_name: app-challenge
    ports:
        - 8080:8080
    environment:
      MONGO_URI: mongodb://root:example@mongodb:27017/prueba?authSource=admin
    networks:
      - mired

volumes:
  mongodbdata:

networks:
  mired:
    external: false

```

#### MongoDB container

En vez de crear un Dockerfile de mongodb con la inicializacion y la importacion de los datos de restaurant.json, he decidido hacerlo todo directamente en el docker compose ya que es simplemente usar de base la imagen de [mongo](https://hub.docker.com/_/mongo/).

Para la inicialización y la importación de datos de restaurant.json se han creado dos scripts en el directorio data para mapearlos al entrypoint-initdb.d.

[init-users.sh](https://github.com/vittyx/the-real-devops-challenge/blob/master/data/init-users.sh)


```shell

if [ "$MONGO_INITDB_ROOT_USERNAME" ] && [ "$MONGO_INITDB_ROOT_PASSWORD" ]; then
  "${mongo[@]}" "$MONGO_INITDB_DATABASE" <<-EOJS
  db.createUser({
     user: $(_js_escape "$MONGO_INITDB_ROOT_USERNAME"),
     pwd: $(_js_escape "$MONGO_INITDB_ROOT_PASSWORD"),
     roles: [ "readWrite", "prueba" ]
     })
EOJS
fi

echo ======================================================
echo created $MONGO_INITDB_ROOT_USERNAME in database $MONGO_INITDB_DATABASE
echo ======================================================

```

[seed.sh](https://github.com/vittyx/the-real-devops-challenge/blob/master/data/seed.sh)


```bash

#!/bin/bash
mongoimport -u root -p example --authenticationDatabase admin --db prueba --collection restaurant --file restaurant.json

```

#### App container

En este caso el propio docker-compose contiene un parámetro que indica la construcción de una imagen a partir del Dockerfile de la app.

In this case, the docker-compose file contains a setting that will build an image by using the Dockerfile for the app.

### Final Challenge. Deploy it on kubernetes

![Kubernetes](./assets/kubernetes.logo.png)

Write the deployment file *(yaml file)* used to deploy your `API` *(python app and mongodb)*.


Usando _minikube_, se han utilizado pocos recursos de Kubernetes para un despliegue sencillo. Se podría mejorar usando un PVC para la base de datos de MongoDB.

Using _minikube_, a few k8s resources have been used to prepare a simple deployment. It could be better if a PVC is declared, for the MongoDB database.

# namespace.yml (To deploy all resources into)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  creationTimestamp: "2021-01-28T11:36:17Z"
  managedFields:
  - apiVersion: v1
    fieldsType: FieldsV1
    fieldsV1:
      f:status:
        f:phase: {}
    manager: kubectl-create
    operation: Update
    time: "2021-01-28T11:36:17Z"
  name: realchallenge
  resourceVersion: "7297"
  uid: bd8e39e7-820c-4a10-9db2-44a2757fecbf
spec:
  finalizers:
  - kubernetes
status:
  phase: Active
```

# secret.yml (Used to pull images from GitHub Registry)

```yaml
apiVersion: v1
data:
  .dockerconfigjson: Secret de Github personal
kind: Secret
metadata:
  creationTimestamp: null
  name: githubregistry
  namespace: realchallenge
type: kubernetes.io/dockerconfigjson

```

# deployment.yml (Contains two services an two deployments)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-python-challenge
  namespace: realchallenge
spec:
  selector:
    app: app-python-challenge
  ports:
  - protocol: "TCP"
    port: 8080
    targetPort: 8080
  type: NodePort
---

apiVersion: v1
kind: Service
metadata:
  name: mongodb-svc
  namespace: realchallenge
spec:
  selector:
    app: mongodb
  ports:
  - protocol: "TCP"
    port: 27017
    targetPort: 27017
  type: ClusterIP

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-python-challenge
  namespace: realchallenge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-python-challenge
  template:
    metadata:
      labels:
        app: app-python-challenge
    spec:
      imagePullSecrets:
        - name: githubregistry  
      containers:
        - name: app-python
          image: docker.pkg.github.com/vittyx/the-real-devops-challenge/app-challenge:latest
          env:
            - name: MONGO_URI
              value: mongodb://root:example@mongodb-svc:27017/prueba?authSource=admin 
          ports:
            - containerPort: 8080

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
  namespace: realchallenge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:4.4
        env:
          - name: MONGO_INITDB_ROOT_USERNAME
            value: root
          - name: MONGO_INITDB_ROOT_PASSWORD
            value: example
          - name: MONGO_INITDB_DATABASE
            value: prueba
        ports:
          - containerPort: 27017
```