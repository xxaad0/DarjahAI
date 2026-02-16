from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import select

from ..extensions import db, bcrypt
from ..models import User, Character, ChatMessages,ChatSession, Tasks,SubTasks, TaskTopTerm
from ..forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, VerifyEmailForm, DeleteAccountForm
from ..email_utils import send_reset_password_email, send_verify_email
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

bp = Blueprint("auth", __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            fullname=f"{form.firstname.data} {form.lastname.data}".strip(),
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        char = Character(c_name=form.character_name.data, c_class="Novice", user_id=user.id)
        db.session.add(char)
        db.session.commit()

        login_user(user)
        flash("Logged in Successfully. Welcome Player.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid Username/Password.", "danger")

    return render_template("login.html", form=form)


@bp.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    flash("You have logged out.", "success")
    return redirect(url_for("main.home"))


@bp.route("/verify", methods=["GET", "POST"])
@login_required
def verify():
    form = VerifyEmailForm()

    if current_user.email_verified:
        flash("Your email is already verified.", "success")
        return render_template("verify.html", form=form)

    if form.validate_on_submit():
        send_verify_email(current_user)
        flash("A verification link has been sent.", "success")
        return redirect(url_for("auth.verify"))

    return render_template("verify.html", form=form)


@bp.route("/verify-success/<token>/<int:user_id>",methods=["GET","POST"])
def verify_success(token, user_id):
    user = User.verify_verification_token(token, user_id)
    if not user:
        return render_template("verify_error.html")

    user.email_verified = True
    db.session.commit()
    flash("Email successfully verified.", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/forgotpass", methods=["GET", "POST"], endpoint="forgotpass")
def forgotpassword():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        stmt = select(User).where(User.email == form.email.data)
        user = db.session.scalar(stmt)
        if user:
            send_reset_password_email(user)

        flash("If the email is associated with an account, a link will be sent.", "success")
        return redirect(url_for("auth.forgotpass"))

    return render_template("forgotpass.html", form=form)


@bp.route("/reset_password/<token>/<int:user_id>", methods=["GET", "POST"])
def reset_password(token, user_id):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user = User.validate_reset_password_token(token, user_id)
    if not user:
        return render_template("reset_password_error.html")

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        return render_template("reset_password_success.html")

    return render_template("reset_password.html", form=form)


@bp.route("/settings",methods=["GET","POST"])
@login_required
def settings():
    form = DeleteAccountForm()

    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()

        if not user:
            flash("User not found","danger")
            return redirect(url_for("main.home"))

        try:
            sessions = db.session.scalars(
                select(ChatSession).where(ChatSession.user_id == user.id)
            ).all()
            for s in sessions:
                db.session.delete(s)

            subs = db.session.scalars(
                select(SubTasks).where(SubTasks.user_id == user.id)
            ).all()
            for st in subs:
                db.session.delete(st)

            tasks = db.session.scalars(
                select(Tasks).where(Tasks.user_id == user.id)
            ).all()
            for t in tasks:
                db.session.delete(t)

            terms = db.session.scalars(
                select(TaskTopTerm).where(TaskTopTerm.user_id == user.id)
            ).all()
            for tt in terms:
                db.session.delete(tt)

            if user.character:
                for x in list(user.character.xp_stats):
                    db.session.delete(x)
                db.session.delete(user.character)

            logout_user()
            db.session.delete(user)
            db.session.commit()
        

            flash("Account deleted successfully.", "success")
            return redirect(url_for("main.home"))
        
        except IntegrityError:
            db.session.rollback()
            flash("Could not delete account.","danger")
            return redirect(url_for("auth.settings"))


    return render_template("settings.html", form=form)
