# Reservations


class ReservationError(Exception):
    pass


class ReservationOverlap(ReservationError):
    pass


class ReservationNotFound(ReservationError):
    pass


class InvalidTimeRange(ReservationError):
    pass


# Parking lots
class ParkingLotError(Exception):
    pass


class ParkingLotNotFound(ParkingLotError):
    pass


class ParkingLotAtCapacity(Exception):
    pass


# Auth
class AuthError(Exception):
    pass


class AccountAlreadyExists(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class AccessForbidden(AuthError):
    pass


# Users
class UserError(Exception):
    pass


class UserNotFound(UserError):
    pass


# Sessions
class ParkingSessionError(Exception):
    pass


class ParkingSessionNotFound(ParkingSessionError):
    pass


# Payments
class PaymentError(Exception):
    pass


class PaymentNotFound(PaymentError):
    pass


class PaymentNoEntryOrExitTime(PaymentError):
    pass
