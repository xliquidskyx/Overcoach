# Deploy Checklist

## Before Deploy
- [ ] SECRET_KEY: generate new longer secret key
- [ ] Set DEBUG=False
- [ ] SET UP: SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_SSL_REDIRECT. SECURE_HSTS_SECONDS
- [ ] Configure [MAILERS](https://docs.djangoproject.com/en/6.1/ref/settings/#mailers)
- [ ] Configure STATIC_ROOT
- [ ] check --deploy: no warnings
[deployment checklist](https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/)

## After Deploy