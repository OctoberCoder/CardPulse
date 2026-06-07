# Domain Setup: cardpulse.publicvm.com

## DNS Records

Since `publicvm.com` is managed by FreeDomain.One (DNSExit):

1. Log in to https://freedomain.one/
2. Go to **DNS Management** for `cardpulse.publicvm.com`
3. Add these records:

| Type | Name | Value |
|------|------|-------|
| **CNAME** | `@` | `cardpulse-production-2d54.up.railway.app` |
| **CNAME** | `www` | `cardpulse-production-2d54.up.railway.app` |
| **CNAME** | `api` | `cardpulse-production-2d54.up.railway.app` |
| **CNAME** | `frontend` | `cardpulse.vercel.app` (replace after Vercel deploy) |

## After DNS propagates (5-30 min):

- `https://cardpulse.publicvm.com` → Backend API
- `https://cardpulse.publicvm.com/frontend` → Flutter app (or separate subdomain)

## Railway Custom Domain

1. Go to **Railway** → **CardPulse service** → **Settings** → **Domains**
2. Add `cardpulse.publicvm.com`
3. Railway auto-provisions SSL certificate

## Vercel Custom Domain

1. Go to **Vercel** → project → **Domains**
2. Add `cardpulse.publicvm.com`
3. Vercel auto-provisions SSL certificate
