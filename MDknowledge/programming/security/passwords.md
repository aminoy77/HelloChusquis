# Password security

- Argon2id, scrypt, or bcrypt with tuned cost store passwords; never MD5/SHA-1.
- Unique salts per user defeat rainbow tables even for identical passwords.
- Peppers (secret server-side salt) add breach-resistance beyond database salts.
- Enforce length (12+ chars) over complexity theater for memorable strength.
- Check new passwords against breach corpora (HaveIBeenPwned API) at signup.
- Rate-limit plus lockout plus CAPTCHA layers slow online guessing.
- Password managers plus passkeys beat human-memorable secrets entirely.
- Never log, email, or URL-embed passwords in any retrievable form.
- Rotate on breach evidence, not calendars — forced rotation weakens choices.
- Argon2 memory-hardness specifically punishes GPU/ASIC cracking rigs.
