# Python email handling

- In Python, `smtplib.SMTP` sends mail; `email.message.EmailMessage` builds it.
- In Python, `imaplib` fetches; `poplib` reads legacy POP boxes.
- In Python, `EmailMessage.set_content` plus `add_attachment` compose rich mails.
- In Python, `smtplib` needs STARTTLS/login for most providers today.
- In Python, `mailbox` parses local mbox/Maildir archives directly.
- In Python, `email.utils.parseaddr` splits display names from addresses.
- In Python, `flanker`-style validation beats regexes for real addresses.
- In Python, never log full messages; headers alone usually suffice.
