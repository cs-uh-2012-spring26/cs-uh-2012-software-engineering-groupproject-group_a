![CI](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group_a/actions/workflows/ci.yml/badge.svg?branch=main)

# Fitness Class Management and Booking System

This repo is a web application for managing gym class schedules, bookings, and trainer–member interactions. It provides role-based access for members, trainers, and admins, with JWT-based authentication and a RESTful API backend.

## Background
This system built around the idea of making it simple for gyms to publish class schedules and for members to discover, book, and manage their classes online. 

## Prerequisites

- python 3.10 or higher
- MongoDB installed. Follow [https://www.mongodb.com/docs/manual/installation/](https://www.mongodb.com/docs/manual/installation/)
to install MongoDB locally. Select the right link for your operating system.
- Make sure the MongoDB service is running locally before starting the backend server.

## Tech Stack

This flask web app uses:

- [Flask-RESTX][flask-restx] for creating REST APIs. Directory structure
follows [flask restx instructions on scaling your project][flask-restx-scaling]
  - flask-restx automatically generates
  [OpenAPI specifications][openapi-specification] for your API
- [PyMongo][pymongo] for communicating with the mongodb database
- [pytest][pytest] for testing
(see [flask specific testing instructions on pytest][pytest-flask]
for more info specific to testing Flask applications)
- [mongomock][mongomock] for mocking the mongodb during unit testing

[flask-restx]: https://flask-restx.readthedocs.io/en/latest/quickstart.html
[flask-restx-scaling]: https://flask-restx.readthedocs.io/en/latest/scaling.html
[openapi-specification]: https://swagger.io/docs/specification/v3_0/about/
[pymongo]: https://pymongo.readthedocs.io/en/stable/
[pytest]: https://docs.pytest.org/en/stable/
[pytest-flask]: https://flask.palletsprojects.com/en/stable/testing/
[mongomock]: https://docs.mongoengine.org/guide/mongomock.html

## Running Locally

This assumes you are already running MongoDB (e.g., through
`brew services restart mongodb-community` on MacOS or
`sudo systemctl restart mongod` on Linux.
Find the equivalent for your OS)

### Setting up the environment

1. Check `.samplenv` file and follow the instructions there to create
your `.env` file
2. Run `make dev_env` to create a virtual environment and install dependencies

### Running the server

1. Run `make run_local_server` to run the server. This will also run the tests first.
2. Go to [http://127.0.0.1:8000](http://127.0.0.1:8000) to see it running!

You can use `ctrl-c` to stop the server.

### Manually activating and deactivating the virtual environment

Manually activating and deactivating the virtual environment is useful for
debugging issues and running specific scripts with flexibility (e.g., you can
run `FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000`
inside the virtual environment to directly start
the server without running tests first).

To activate the virtual environment manually:

```sh
source .venv/bin/activate
```

Alternatively, you can use:

```sh
. .venv/bin/activate
```

To deactivate the virtual environment:

```sh
deactivate
```

## Authentication & Testing Protected Endpoints

This API uses JWT-based authentication to protect certain endpoints.

### Pre-seeded Trainer Account

A trainer account is automatically created when the application starts.

**Trainer Credentials:**

- Username: `trainer1`
- Password: `password123`

---

## How to Test Trainer-Only Endpoints in Swagger

- Start the server following the instructions above.
- Open Swagger UI in your browser.
- Navigate to `POST /auth/login`.
- Login using: 
{
  "username": "trainer1",
  "password": "password123"
}
5. Copy the access_token from the response.
6. Click the Authorize button in Swagger.
7. Paste the token in the following format:
`Bearer <your_access_token>`
8. You can now access protected endpoints such as:
- `POST /classes/` (Create Class – trainer only)
- `GET /classes/{class_id}/members` (View Class Members – trainer only)

## Maintainers
Isumi Wanniarachchi @isumisw 
\
Nada Kaluderovic @nadja2506
\
Rujul Malhotra @rujulm
