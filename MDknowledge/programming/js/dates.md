# JavaScript dates

- In JavaScript, `new Date()` is now and `Date.now()` is epoch milliseconds for timing.
- In JavaScript, months are zero-indexed: `new Date(2024, 0, 1)` is January 1st.
- In JavaScript, `toISOString()` emits UTC ISO 8601, the portable interchange format.
- In JavaScript, `getTime()` timestamps enable arithmetic; subtract dates for durations.
- In JavaScript, `Intl.DateTimeFormat(locale, opts)` renders localized dates without libraries.
- In JavaScript, `toLocaleDateString` varies by runtime; pin options for stable output.
- In JavaScript, date-only strings parse as UTC while datetime strings parse as local time.
- In JavaScript, store and transmit UTC, converting to local zones only at display.
- In JavaScript, `setHours/getHours` use local time; `setUTCHours` variants use UTC.
- In JavaScript, daylight-saving transitions make day arithmetic unsafe; use libraries for calendars.
