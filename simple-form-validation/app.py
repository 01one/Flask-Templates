from flask import Flask, request, jsonify, render_template
import re  # We will use regex module to validate inputs


app = Flask(__name__)


@app.route('/')
def form_example():
    return render_template('form-example.html')


def validate_input(address, phone, email):
    errors = {}
    
    # Address validation: It should be between 5 to 200 characters
    # Also, it should NOT contain links like 'http://', 'www.', etc.
    if not (5 <= len(address) <= 200):
        errors['address'] = "Address must be between 5 and 200 characters."
    
    link_pattern = re.compile(r"(http[s]?:\/\/|www\.)\S+", re.IGNORECASE)
    if link_pattern.search(address):
        errors['address'] = "Address cannot contain links."

    # Phone number validation: It must be between 9 to 15 digits
    # It can optionally start with a '+' sign
    phone_pattern = re.compile(r"^\+?[0-9]{9,15}$")
    if not phone_pattern.match(phone):
        errors['phone'] = "Invalid phone number format."

    # Email validation: It's optional, but if provided, it must be a valid format
    if email and not re.match(r"^\S+@\S+\.\S+$", email):
        errors['email'] = "Invalid email format."
    
    return errors


@app.route('/submit-form', methods=['POST'])
def submit_form():
    data = request.json
    
    # Extract values from the request, remove any unwanted spaces
    address = data.get("address", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    
    # Validate the extracted input data
    errors = validate_input(address, phone, email)
    
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    # If everything is valid, return a success message
    return jsonify({"success": True, "message": "Form submitted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
