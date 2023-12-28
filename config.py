# Database setup
username = "brycepm2"        # you may put your username instead
password = "$QLData4Me"  # use your MySQL password
hostname = f"{username}.mysql.pythonanywhere-services.com"
databasename = f"{username}$rfpProcInfo"

SQLALCHEMY_DATABASE_URI = (
    f"mysql://{username}:{password}@{hostname}/{databasename}"
)
SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 200}
SQLALCHEMY_TRACK_MODIFICATIONS = False
