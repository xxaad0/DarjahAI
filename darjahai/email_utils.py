from flask import url_for, render_template_string
from flask_mailman import EmailMessage

from .extensions import mail

def send_reset_password_email(user):
    reset_url = url_for(
        "auth.reset_password",
        token=user.generate_reset_password_token(),
        user_id=user.id,
        _external=True,
    )

    body = render_template_string(
        """
        <p>Hey there!</p>
        <p>You requested a password reset.</p>
        <p><a href="{{ reset_url }}">Click here to reset</a></p>
        """,
        reset_url=reset_url,
    )

    msg = EmailMessage(
        subject="DarjahAI ~ Reset your password",
        body=body,
        to=[user.email],
        mail=mail,
    )
    msg.content_subtype = "html"
    msg.send()

def send_verify_email(user):
    verify_url = url_for(
        "auth.verify_success",
        token=user.generate_verify_email_token(),
        user_id=user.id,
        _external=True,
    )

    body = render_template_string(
        """
        <p>Hey there!</p>
        <p>Verify your email:</p>
        <p><a href="{{ verify_url }}">Click here to verify</a></p>
        """,
        verify_url=verify_url,
    )

    msg = EmailMessage(
        subject="DarjahAI ~ Verify Your Email",
        body=body,
        to=[user.email],
        mail=mail,
    )
    msg.content_subtype = "html"
    msg.send()
