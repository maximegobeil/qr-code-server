from dotenv import load_dotenv
import jwt
import qrcode
import os
from PIL import Image


load_dotenv()
secret = os.getenv('SECRET_KEY')

# Generate JWT token
jwt_payload = {
    'ticket_id': 222,
}
jwt_token = jwt.encode(jwt_payload, secret, algorithm='HS256')
print(jwt_token)

# Generate QR code containing the JWT token as a parameter
qr_payload = f"https://www.lesproductions725.com/verify/{jwt_token}"
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4,
)
qr.add_data(qr_payload)

img = qr.make_image(fill_color="black", back_color="white")

ticket_template = Image.open('ticket_template.png')
position = (743, 612)
img = img.resize((140, 140))
ticket_template.paste(img, position)

ticket_template.save('combined_ticket.png')
