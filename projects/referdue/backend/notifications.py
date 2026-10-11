"""Notification worker. Dry-run by default; live delivery is a Vishwa-only action."""
import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from server import App


def dispatch(app, send=None):
    """A single worker per database. Stable Message-ID supports downstream deduplication."""
    accounts=app.db.execute("SELECT id,recipient,purpose,body FROM account_mail WHERE status='pending' ORDER BY id").fetchall()
    rows=app.db.execute("SELECT id,recipient,event,referral FROM outbox WHERE status='pending' ORDER BY id").fetchall()
    delivered=0
    for key,recipient,event,referral in rows:
        message=EmailMessage()
        message['To']=recipient
        message['Subject']='ReferDue: '+event.split('.')[0]+' update'
        message['Message-ID']=f'<referdue-{key}-{referral}@notifications.invalid>'
        message.set_content(f'Your referral record has an update.\nReferral reference: {referral}\nEvent: {event}\nOpen your private ReferDue portal for details.\nReferDue records external payments; it does not move money.\n')
        if send is None: continue
        send(message)
        with app.db: app.db.execute("UPDATE outbox SET status='sent' WHERE id=? AND status='pending'",(key,))
        delivered+=1
    for key,recipient,purpose,body in accounts:
        message=EmailMessage(); message['To']=recipient
        message['Subject']='ReferDue: '+('verify your email' if purpose=='verify' else 'password reset')
        message['Message-ID']=f'<referdue-account-{key}@notifications.invalid>'
        message.set_content(body)
        if send is None: continue
        send(message)
        with app.db: app.db.execute("UPDATE account_mail SET status='sent',body='' WHERE id=? AND status='pending'",(key,))
        delivered+=1
    return {'pending_seen':len(rows)+len(accounts),'sent':delivered,'dry_run':send is None}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Single-worker outbox dispatch. Default only counts pending notifications.')
    parser.add_argument('--database',required=True)
    parser.add_argument('--send',action='store_true',help='Actually send email. Requires owner authorization and SMTP configuration.')
    args=parser.parse_args()
    app=App(Path(args.database).expanduser())
    try:
        if not args.send: print(dispatch(app))
        else:
            # These variables are read only on an explicit live-send invocation.
            host=os.environ['REFERDUE_SMTP_HOST']; username=os.environ['REFERDUE_SMTP_USER']; password=os.environ['REFERDUE_SMTP_PASSWORD']; sender=os.environ['REFERDUE_FROM']
            with smtplib.SMTP(host,int(os.environ.get('REFERDUE_SMTP_PORT','587')),timeout=20) as smtp:
                smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo(); smtp.login(username,password)
                def send(message):
                    message['From']=sender
                    smtp.send_message(message)
                print(dispatch(app,send))
    finally: app.store.close()
