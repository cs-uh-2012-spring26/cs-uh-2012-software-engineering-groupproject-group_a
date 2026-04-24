from app.db.bookings import BookingResource, USER_ID
from app.db.users import UserResource, USERNAME, EMAIL, PHONE, NOTIFICATION_PREFS

def get_class_members(class_id):
    booking_res = BookingResource()
    bookings = booking_res.get_class_bookings(class_id)
    user_res = UserResource()
    seen = set()
    members = []

    for booking in bookings:
        member_id = booking.get(USER_ID)
        if not isinstance(member_id, str) or member_id in seen:
            continue
        seen.add(member_id)

        member = user_res.get_user_by_id(member_id)
        if member is None:
            continue
        members.append({
            USERNAME: member.get(USERNAME),
            EMAIL: member.get(EMAIL),
            PHONE: member.get(PHONE),
            NOTIFICATION_PREFS: member.get(NOTIFICATION_PREFS),
        })
    return members