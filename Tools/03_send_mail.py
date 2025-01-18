from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object("config.Config")

mail = Mail(app)


@app.route("/send-email")
def send_email():
    try:
        msg = Message(
            "Prueba de correo",
            sender=app.config["MAIL_USERNAME"],
            recipients=["edfrutos@gmail.com"],
        )
        msg.body = "Este es un correo de prueba."
        mail.send(msg)
        return "Correo enviado exitosamente!"
    except Exception as e:
        return f"Error enviando correo: {e}"


if __name__ == "__main__":
    app.run(debug=True)
