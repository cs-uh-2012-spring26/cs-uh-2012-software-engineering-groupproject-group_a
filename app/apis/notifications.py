from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.apis import MSG
from app.db.users import UserResource, NOTIFICATION_PREFS, TELEGRAM_CHAT_ID, VALID_CHANNELS

api = Namespace("notifications", description="Endpoint for managing notification preferences")

prefs_fields = api.model(
    "NotificationPreferences",
    {
        "notification_prefs": fields.List(
            fields.String,
            example=["email", "telegram"],
            description=(
                "List of channels to receive notifications through. "
                "Supported channels: 'email', 'telegram'."
            ),
        )
    },
)

@api.route("/preferences")
class NotificationPreferences(Resource):
    @jwt_required()
    @api.response(
        HTTPStatus.OK,
        "Preferences retrieved successfully",
        api.model("PreferencesResponse", {MSG: fields.Raw()}),
    )
    @api.response(
        HTTPStatus.NOT_FOUND, 
        "User not found",
        api.model("PreferencesNotFound", {MSG: fields.String}))
    
    def get(self):
        #Fetch user's current notification preferences

        user_id = get_jwt_identity()
        user_res = UserResource()
        user = user_res.get_user_by_id(user_id)
        if user is None:
            return {MSG: "User not found"}, HTTPStatus.NOT_FOUND
        return {
            MSG: {
                "channels": user.get(NOTIFICATION_PREFS, ["email"]),
                "telegram_linked": user.get(TELEGRAM_CHAT_ID) is not None,
            }
        }, HTTPStatus.OK

    @jwt_required()
    @api.expect(prefs_fields)
    @api.response(
        HTTPStatus.OK, 
        "Preferences updated successfully",
        api.model("PreferencesUpdated", {MSG: fields.String}))
    
    @api.response(
        HTTPStatus.NOT_ACCEPTABLE, 
        "Invalid request",
        api.model("PreferencesError", {MSG: fields.String}))
    
    def put(self):
        #Update the user's notification preferences
        data = request.json
        if data is None or not isinstance(data, dict):
            return {MSG: "Request body must be JSON"}, HTTPStatus.NOT_ACCEPTABLE

        prefs = data.get("notification_prefs")
        if not isinstance(prefs, list):
            return {MSG: "notification_prefs must be a list"}, HTTPStatus.NOT_ACCEPTABLE

        for channel in prefs:
            if channel not in VALID_CHANNELS:  
                return {MSG: f"Only supported channels are accepted: {list(VALID_CHANNELS)}"}, HTTPStatus.NOT_ACCEPTABLE

        user_id = get_jwt_identity()
        user_res = UserResource()
        updated = user_res.update_notification_prefs(user_id=user_id, prefs=prefs)
        if not updated:
            return {MSG: "Failed to update preferences"}, HTTPStatus.NOT_ACCEPTABLE

        if "telegram" in prefs:
            return {
                MSG: "Preferences updated. To activate Telegram notifications, message your registered phone number to @FitnessClassBot on Telegram."
            }, HTTPStatus.OK
        
        return {MSG: "Notification preferences updated successfully"}, HTTPStatus.OK
