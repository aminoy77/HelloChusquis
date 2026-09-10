# URL anatomy

- URLs split as scheme://user@host:port/path?query#fragment in full form.
- The scheme selects protocol semantics: https, ftp, mailto, file, and more.
- Default ports hide: 443 for https, 80 for http need no explicit port.
- Paths are case-sensitive on most servers; normalize before comparing.
- Query strings encode key=value pairs joined by `&` with percent-encoding.
- Fragments (`#section`) scroll clientside and never reach servers.
- Percent-encoding (`%20` for space) escapes reserved characters in URLs.
- Trailing slashes can route differently; canonicalize one form per resource.
- Internationalized domain names encode to punycode (`xn--...`) for DNS.
- Relative URLs resolve against the base URL of their containing document.
