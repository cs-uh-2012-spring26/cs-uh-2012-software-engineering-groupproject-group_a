from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.bookings import CLASS_ID, BOOKING_DATETIME, BookingResource
from app.db.classes import ClassResource
from http import HTTPStatus
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity


api = Namespace("bookings", description="Endpoint for creating bookings")

_EXAMPLE_BOOK_CLASS_1 = {
    CLASS_ID: "605c3d2b5f1c2a1b2c3d4e5f",
}

_EXAMPLE_BOOKING_1 = {
    CLASS_ID: "605c3d2b5f1c2a1b2c3d4e5f",
    BOOKING_DATETIME: "2026-03-02T08:30:00",
}

BOOK_CLASS_MODEL = api.model( #for Book a Class request
    "BookClass",
    {
        CLASS_ID: fields.String(required=True, example=_EXAMPLE_BOOK_CLASS_1[CLASS_ID]),
    },
)

MY_BOOKING_MODEL = api.model( #for a single booking item
    "MyBooking",
    {
        CLASS_ID: fields.String(required=True, example=_EXAMPLE_BOOKING_1[CLASS_ID]),
        BOOKING_DATETIME: fields.String(required=True, example=_EXAMPLE_BOOKING_1[BOOKING_DATETIME]),
    },
)


@api.route("/")
class BookClass(Resource):
    @jwt_required()
    @api.expect(BOOK_CLASS_MODEL, validate=True)
    @api.response(
        HTTPStatus.OK, 
        "Booking successful",
        api.model("BookClassResponse", {MSG: fields.String(example="Booking successful")}),
    )
    @api.response(
        HTTPStatus.BAD_REQUEST,
        "Invalid booking request",
        api.model("BookClassBadRequest", {MSG: fields.String}),
    )
    @api.response(
        HTTPStatus.NOT_FOUND,
        "Class not found",
        api.model("BookClassNotFound", {MSG: fields.String}),
    )
    def post(self):
        class_id = request.json.get(CLASS_ID) #get class,user id from request json body
        user_id = get_jwt_identity()

        class_res = ClassResource()
        booking_res = BookingResource()

        #check class exists
        cls = class_res.get_class_by_id(class_id)
        if cls is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        #prevent duplicate booking
        existing = booking_res.get_booking(user_id, class_id)
        if existing is not None:
            return {MSG: "You have already booked this class"}, HTTPStatus.BAD_REQUEST

        #check if full
        if not class_res.has_remaining_spots(class_id):
            return {MSG: "Class is full"}, HTTPStatus.BAD_REQUEST

        #decrement remaining spots atomically
        ok = class_res.decrement_remaining_spots(class_id)
        if not ok:
            #someone else may have booked the last spot
            return {MSG: "Class is full"}, HTTPStatus.BAD_REQUEST

        #create booking
        booking_id = booking_res.create_booking(user_id, class_id)

        return {MSG: f"Booking successful with id {booking_id}"}, HTTPStatus.OK

@api.route("/mine")
class MyBookings(Resource):
    @jwt_required()
    @api.response(
        HTTPStatus.OK,
        "Success",
        api.model( #for a list of booking items
            "MyBookingsResponse",
            {
                MSG: fields.List(
                    fields.Nested(
                        api.model(
                            "BookingItem",
                            {
                                "booking_id": fields.String,
                                "class_id": fields.String,
                                "booking_datetime": fields.String,
                            },
                        )
                    )
                )
            },
        ),
    )
    def get(self):
        user_id = get_jwt_identity()
        booking_res = BookingResource()
        bookings = booking_res.get_user_bookings(user_id) #get all bookings for the user

        result = [
            {"booking_id": b["_id"], "class_id": b[CLASS_ID], "booking_datetime": b[BOOKING_DATETIME]} for b in bookings
        ]
        return {MSG: result}, HTTPStatus.OK