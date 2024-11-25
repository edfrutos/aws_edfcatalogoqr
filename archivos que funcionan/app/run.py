from app import create_app

app = create_app()

if app:
    app.run(debug=True)
else:
    print("Failed to create the Flask application.")
