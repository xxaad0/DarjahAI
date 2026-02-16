from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc  import IntegrityError
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mailman import Mail

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
