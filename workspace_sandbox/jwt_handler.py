import jwt


jwt_secret_key = "secret_key_for_jwt"


def encode_token(payload):
    return jwt.encode(payload, jwt_secret_key, algorithm='HS256')


def decode_token(token):
    try:
        return jwt.decode(token, jwt_secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return { 'error': 'Token has expired' }
    except jwt.InvalidTokenError:
        return { 'error': 'Invalid token' }