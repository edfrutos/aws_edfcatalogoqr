from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object("app.config.Config")

mail = Mail(app)


@app.route("/send-email")
def send_email():
    try:
        msg = Message(
            "Prueba de correo",
            sender=app.config["MAIL_USERNAME"],
            recipients=["edefrutos@edefrutos.me"],
        )
        msg.body = "Este es un correo de prueba."
        mail.send(msg)
        return "Correo enviado exitosamente!"
    except Exception as e:
        app.logger.error(f"Error enviando correo: {e}")
        return f"Error enviando correo: {e}"


@app.route("/")
def index():
    return "Bienvenido a la aplicación de envío de correos!"


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
