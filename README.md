To test API's:
1. Create virtual environment, command: python -m venv env
2. Activate the venv, command: env/Scripts/activate
3. Install all requirements, command: pip install -r requirements.txt
4. Install phone number field manually, command: pip install "django-phonenumber-field[phonenumberslite]"
5. Create credentials files: .env and firebase_serviceaccountkey.json
6. Make migrations of models, command: python manage.py makemigrations
7. Migrate the models, command: python manage.py migrate
8. Run local server, command: python manage.py runserver
9. Open Postman and import the collection file, file name: Handy Book.postman_collection
10. Start testing API's :)

Pre-requirements:
1. Python
2. Any code editor(VS code preffered)
3. Postman
