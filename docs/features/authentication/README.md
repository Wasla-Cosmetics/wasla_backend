# Authentication

Authentication routes are mounted under `/api/auth/` and use bearer JWTs.
Access tokens expire after 10 minutes; refresh tokens expire after 30 days and
rotate through `POST /api/auth/token/refresh/`.

## OTP Flow

Registration and password reset use six-digit, purpose-bound OTPs. Only a
password hash of the OTP is stored, and the OTP is cleared after successful
verification or failed delivery. Authentication endpoints are throttled by
both client IP and normalized phone number.

Settings remain fail-closed with an unconfigured delivery backend until one is
selected. The provided Docker development configuration selects
`EmailOtpDeliveryBackend` and delivers messages to Mailpit. Open its local inbox
at `http://localhost:8025/` to read an OTP without an external provider.

Staging and production refuse to start with the unconfigured backend. They can
use the email backend with a real SMTP service or the webhook backend for an SMS
provider. The webhook backend posts this payload to the configured HTTPS
endpoint:

```json
{
  "phone": "+201000000001",
  "otp": "654321"
}
```

It authenticates with `Authorization: Bearer <AUTH_OTP_WEBHOOK_TOKEN>`.

The email backend sends a plain-text verification message to the unique email
address stored on the user account. SMTP connection failures are returned as an
OTP delivery-unavailable response and the stored OTP is cleared.

## Password Reset

The reset flow is deliberately separate from login:

1. `POST /api/auth/send-otp/` with the phone number.
2. `POST /api/auth/verify-otp/` with `action: "reset-password"`.
3. Read the short-lived `reset_token` from the response. No access or refresh
   token is returned at this step.
4. `POST /api/auth/reset-password/` with `reset_token`, `password`, and
   `confirm_password`.

Changing or resetting a password increments the user's token version and
blacklists outstanding refresh tokens, invalidating previously issued access
and refresh tokens. Logout accepts only a refresh token belonging to the
authenticated user.

Login and OTP-request failures use generic responses where necessary so the
API does not disclose whether a phone number belongs to an active account.

## Guest Sessions

`POST /api/auth/guest-users/` creates a guest session for clients that do not
yet have an account. Creation is rate limited per client IP, sessions expire
after the configured retention period, and expired rows are removed whenever a
new guest session is created. The response includes `expires_at`; send the
session key in `X-Guest-Token` while it remains valid.
