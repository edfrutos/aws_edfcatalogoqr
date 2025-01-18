from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config["MAIL_SERVER"] = "smtp-relay.brevo.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
app.config["MAIL_DEFAULT_SENDER"] = "admin@edefrutos.me"

mail = Mail(app)


@app.route("/send_email")
def send_email():
    msg = Message("Hello", recipients=["edfrutos@gmail.com"])
    msg.body = "This is a test email."
    try:
        mail.send(msg)
        return "Email sent!"
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run(debug=True)
