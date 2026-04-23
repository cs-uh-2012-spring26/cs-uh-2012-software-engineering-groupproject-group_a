from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.users import UserResource
from app.db.users import USERNAME, EMAIL, PASSWORD_HASH, PHONE, Role
from http import HTTPStatus
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


api = Namespace("auth", description="Authentication endpoints")

_EXAMPLE_USER_1 = {
    USERNAME: "Jane Doe",
    EMAIL: "jane.doe@software.io",
    "password": "janedoe12345",
    PHONE: "+971500000000",
}

_EXAMPLE_USER_2 = {
    USERNAME: "John Doe",
    EMAIL: "john.doe@software.io",
    "password": "johndoe54321",
    PHONE: "+971500000001",
}

REGISTER_USER = api.model(
    "Register",
    {
        USERNAME: fields.String(required=True, example=_EXAMPLE_USER_1[USERNAME]),
        EMAIL: fields.String(required=True, example=_EXAMPLE_USER_1[EMAIL]),
        "password": fields.String(required=True, example=_EXAMPLE_USER_1["password"]),
        PHONE: fields.String(required=True, example=_EXAMPLE_USER_1[PHONE]),
    },
)

LOGIN_USER = api.model(
    "Login",
    {
        EMAIL: fields.String(required=True, example=_EXAMPLE_USER_1[EMAIL]),
        "password": fields.String(required=True, example=_EXAMPLE_USER_1["password"]),
    },
)

TOKEN_MODEL = api.model(
    "TokenResponse",
    {
        "access_token": fields.String(example="JWT_TOKEN_HERE"),
    },
)

@api.route("/register/member")
class RegisterMember(Resource):
    @api.expect(REGISTER_USER, validate=True)
    @api.response(HTTPStatus.CREATED, "User registered")
    @api.response(HTTPStatus.BAD_REQUEST, "Username or email already exists")
    def post(self):
        username = request.json.get(USERNAME)
        email = request.json.get(EMAIL)
        password = request.json.get("password")
        phone = request.json.get(PHONE)
        user_res = UserResource()
        if user_res.get_user_by_username(username) or user_res.get_user_by_email(email):
            return {MSG: "Username or email already exists"}, HTTPStatus.BAD_REQUEST
        password_hash = generate_password_hash(password)
        user_id = user_res.create_user(username, email, password_hash, phone, role=Role.MEMBER)

        return {MSG: f"Member created with id: {user_id}"}, HTTPStatus.CREATED
    
@api.route("/register/trainer")
class RegisterTrainer(Resource):
    @jwt_required()
    @api.expect(REGISTER_USER, validate=True)
    @api.response(HTTPStatus.CREATED, "User registered")
    @api.response(HTTPStatus.BAD_REQUEST, "Username or email already exists")
    def post(self):
        user_id = get_jwt_identity()
        user_res = UserResource()
        user = user_res.get_user_by_id(user_id)
        if user is None or not user_res.is_admin(user):
            return {MSG: "Admin access required"}, HTTPStatus.FORBIDDEN
        
        username = request.json.get(USERNAME)
        email = request.json.get(EMAIL)
        password = request.json.get("password")
        phone = request.json.get(PHONE)

        if user_res.get_user_by_username(username) or user_res.get_user_by_email(email):
            return {MSG: "Username or email already exists"}, HTTPStatus.BAD_REQUEST
        password_hash = generate_password_hash(password)
        user_id = user_res.create_user(username, email, password_hash, phone, role=Role.TRAINER)

        return {MSG: f"Trainer created with id: {user_id}"}, HTTPStatus.CREATED

@api.route("/login")
class Login(Resource):
    @api.expect(LOGIN_USER, validate=True)
    @api.response(HTTPStatus.OK, "Login successful", TOKEN_MODEL)
    @api.response(HTTPStatus.UNAUTHORIZED, "Invalid credentials")
    def post(self):
        email = request.json.get(EMAIL)
        password = request.json.get("password")

        user_res = UserResource()
        user = user_res.get_user_by_email(email)
        if user is None:
            return {MSG: "Invalid credentials"}, HTTPStatus.UNAUTHORIZED

        if not check_password_hash(user[PASSWORD_HASH], password):
            return {MSG: "Invalid credentials"}, HTTPStatus.UNAUTHORIZED

        access_token = create_access_token(identity=str(user["_id"]))
        return {"access_token": access_token}, HTTPStatus.OK

