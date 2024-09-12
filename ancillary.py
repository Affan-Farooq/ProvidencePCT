from functools import wraps
from flask import redirect, session


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userID") is None:
            return redirect("/authentication")
        return f(*args, **kwargs)
    return decorated_function

def percent(value):
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    else:
        return f"{value:.2f}%"

def usd(value):
    return f"${value:,.5f}"

def usdTrad(value):
    return f"${value:,.2f}"

def intFormat(value):
    try:
        return f"{value:,.2f}"
    except:
        return "None"

def monetaryChange(value):
    if value > 0:
        return f"+${value:,.5f}"
    elif value < 0:
        return f"-${(value * -1):,.5f}"
    else:
        return f"${value:,.5f}"

