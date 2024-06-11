# dependencies.py
from fastapi import Request, HTTPException, Depends
from jose import JWTError, jwt

SECRET_KEY = "your_secret_key"  # Makerkit secret key
ALGORITHM = "HS256"

def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Not authenticated")
    except JWTError:
        raise HTTPException(status_code=403, detail="Not authenticated")

    return user_id