from account.forms import SignupForm
from captcha.fields import CaptchaField


class SignupFormWithCaptcha(SignupForm):
    captcha = CaptchaField()