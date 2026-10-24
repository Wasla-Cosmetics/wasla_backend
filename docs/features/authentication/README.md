# Authentication

Authentication routes are mounted under `/api/auth/` and use bearer JWTs.
Access tokens expire after 10 minutes; refresh tokens expire after 30 days and
rotate through `POST /api/auth/token/refresh/`.

## API Routes

| Method | Route | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register/` | Public | Create an inactive account and send its registration OTP. |
| `POST` | `/api/auth/verify-otp/` | Public | Activate registration or issue a password-reset token. |
| `POST` | `/api/auth/login/` | Public | Issue access and refresh JWTs. |
| `POST` | `/api/auth/token/refresh/` | Public | Rotate a valid refresh token. |
| `POST` | `/api/auth/send-otp/` | Public | Request an OTP without disclosing account state. |
| `POST` | `/api/auth/reset-password/` | Public | Reset a password with a reset token. |
| `GET`, `PUT`, `PATCH` | `/api/auth/profile/` | User | Read or update the current profile. |
| `POST` | `/api/auth/change-password/` | User | Change the current password. |
| `POST` | `/api/auth/logout/` | User | Blacklist the submitted refresh token. |
| `POST` | `/api/auth/delete-account/` | User | Delete the account after password confirmation. |
| `POST` | `/api/auth/guest-users/` | Public | Create an expiring guest session. |
| CRUD | `/api/auth/users/` | Admin | Manage users; list results can be filtered by exact `phone`. |

Registration accepts `phone`, `email`, `full_name`, and `password`. Profile
updates cannot change the phone number or password; use the dedicated password
endpoint instead. Login accepts `phone` and `password`.

## OTP Flow

Registration and password reset use six-digit, purpose-bound OTPs. Only a
password hash of the OTP is stored, and the OTP is cleared after successful
verification or failed delivery. Authentication endpoints are throttled by
both client IP and normalized phone number.

For an inactive account, `send-otp` issues a registration OTP. For an active
account, it issues a password-reset OTP. Its response remains generic so callers
cannot use it to discover whether an account exists or is active.

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

Login failures also use a generic response so the API does not disclose whether
a phone number belongs to an active account.

## Token Revocation

Access tokens carry the user's current token version. Changing or resetting a
password increments that version and blacklists the user's outstanding refresh
tokens. Deleting the account invalidates it entirely. Logout validates that the
submitted refresh token belongs to the authenticated user before blacklisting
that token.

## Guest Sessions

`POST /api/auth/guest-users/` creates a guest session for clients that do not
yet have an account. Creation is rate limited per client IP, sessions expire
after the configured retention period, and expired rows are removed whenever a
new guest session is created. The response includes `expires_at`; send the
session key in `X-Guest-Token` while it remains valid.

Guest sessions are anonymous for permission checks. They cannot create product
reviews or call user-only endpoints.

## Throttling

Registration, login, OTP, reset, and token-refresh requests are throttled by
both trusted client IP and normalized phone number. Guest creation has its own
IP throttle. Rates are configured with `AUTH_IP_THROTTLE_RATE`,
`AUTH_PHONE_THROTTLE_RATE`, and `GUEST_USER_THROTTLE_RATE`.
