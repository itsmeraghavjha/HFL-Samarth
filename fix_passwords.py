"""
fix_passwords.py — Reset all RH/CXO user passwords to Heritage@123
Run once: python fix_passwords.py
"""
import db

db.init_db()

emails = [
    'admin@heritagefoods.in',
    'ceo@heritagefoods.in',
    'coo@heritagefoods.in',
    'rh.tn@heritagefoods.in',
    'rh.ka@heritagefoods.in',
    'rh.ts1@heritagefoods.in',
    'rh.ts2@heritagefoods.in',
    'sh.ts.cat4@heritagefoods.in',
    'rh.ap1@heritagefoods.in',
    'rh.ap2@heritagefoods.in',
    'rh.ods@heritagefoods.in',
    'rh.ap.cat4@heritagefoods.in',
    'rh.mh1@heritagefoods.in',
    'rh.mh2@heritagefoods.in',
    'rh.zone4@heritagefoods.in',
]

for email in emails:
    db.change_password(email, 'Heritage@123')
    print(f'  ✅  Reset: {email}')

print('\nDone — all passwords set to Heritage@123')