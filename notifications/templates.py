from html import escape


def booking_created_message(booking) -> str:
    return (
        "🏨 <b>New booking created</b>\n\n"
        f"<b>Booking ID:</b> {booking.id}\n"
        f"<b>Guest:</b> {escape(booking.user.email)}\n"
        f"<b>Room:</b> {escape(str(booking.room))}\n"
        f"<b>Check-in:</b> {booking.check_in_date}\n"
        f"<b>Check-out:</b> {booking.check_out_date}\n"
        f"<b>Price per night:</b> {booking.price_per_night} USD"
    )


def booking_cancelled_message(booking) -> str:
    return (
        "❌ <b>Booking cancelled</b>\n\n"
        f"<b>Booking ID:</b> {booking.id}\n"
        f"<b>Guest:</b> {escape(booking.user.email)}\n"
        f"<b>Room:</b> {escape(str(booking.room))}\n"
        f"<b>Check-in:</b> {booking.check_in_date}\n"
        f"<b>Check-out:</b> {booking.check_out_date}\n"
        f"<b>Late cancellation:</b> {booking.is_late_cancellation}"
    )


def booking_no_show_message(booking) -> str:
    return (
        "⚠️ <b>Booking marked as no-show</b>\n\n"
        f"<b>Booking ID:</b> {booking.id}\n"
        f"<b>Guest:</b> {escape(booking.user.email)}\n"
        f"<b>Room:</b> {escape(str(booking.room))}\n"
        f"<b>Check-in:</b> {booking.check_in_date}\n"
        f"<b>Check-out:</b> {booking.check_out_date}"
    )


def payment_success_message(payment) -> str:
    return (
        "✅ <b>Payment successful</b>\n\n"
        f"<b>Payment ID:</b> {payment.id}\n"
        f"<b>Booking ID:</b> {payment.booking.id}\n"
        f"<b>Guest:</b> {escape(payment.booking.user.email)}\n"
        f"<b>Type:</b> {payment.type}\n"
        f"<b>Amount:</b> {payment.amount} USD"
    )
