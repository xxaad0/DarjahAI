from flask import Flask, redirect, url_for, flash,jsonify,request
from dotenv import load_dotenv
from flask_migrate import Migrate

from .config import Config
from .extensions import db, bcrypt, login_manager, mail
import os
from zoneinfo import ZoneInfo


from .models import User

from datetime import datetime, timedelta
from flask import request
from flask_login import current_user
from .models import Character

migrate = Migrate()

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    migrate.init_app(app,db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."


    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path == "/chat/api":
            return jsonify({"error": "Unauthorized"}), 401
        
        flash("Please register/login first.", "warning")
        return redirect(url_for("main.home"))

    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    EXCLUDEDENDPOINTS = {
        "main.index",                
        "main.home",                 
        "main.about",                
        "main.verify_error",         
        "main.reset_password_error", 
        "auth.login",                
        "auth.register",             
        "auth.logout",               
        "auth.forgotpass",           
        "auth.reset_password",       
        "auth.verify_success",     
        }
    
    def todayCheck():
        return datetime.now(ZoneInfo("America/Toronto")).date()
    
    @app.before_request
    def trackVisit():
        if not current_user.is_authenticated or request.method!="GET" or request.endpoint is None or request.endpoint.startswith("static") or request.endpoint in EXCLUDEDENDPOINTS:
            return
        
        character= Character.query.filter_by(user_id=current_user.id).first()

        if not character:
            return
        
        td= todayCheck()
        last= character.lastdateactive

        if last == td:
            return
        
        if last == td- timedelta(days=1):
            character.dailystreak+=1
        else:
            character.dailystreak=1

        character.lastdateactive = td
        character.activedaystotal+=1

        if character.dailystreak> character.beststreak:
            character.beststreak=character.dailystreak

        

        db.session.commit()
        

    




    return app
