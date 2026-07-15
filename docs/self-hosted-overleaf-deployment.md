# Self-Hosted Overleaf Deployment Notes

This document captures the deployment pattern that informed ChatOL design. It deliberately avoids real service URLs, hostnames, project paths, account emails, passwords, cookies, proxy credentials, and other environment-specific values.

## Sanitization Contract

Keep this document portable. Use placeholders such as `<public-overleaf-host>`, `<local-port>`, `<admin-email>`, and `<ssh-host>` instead of live domains, private hostnames, usernames, credentials, cookies, tokens, or machine-specific paths. Operational reports may exist in private task directories, but repository documentation should describe the pattern only.

## Deployment Shape

The tested deployment uses Overleaf Community Edition through the official Toolkit.

```text
client / browser
  -> public or internal reverse proxy
  -> local nginx vhost
  -> localhost-only Overleaf web container
  -> MongoDB + Redis containers
```

The Overleaf application itself should bind to localhost first. Public access is layered on later through nginx or the existing service-entry mechanism.

## Why Docker Is The Practical Route

Overleaf Community Edition is operationally coupled to multiple services. The supported Toolkit route manages at least:

- Overleaf web application container;
- MongoDB;
- Redis;
- generated Docker Compose configuration;
- persistent application data and config.

A bare-metal deployment is not the recommended first path for this project because it would increase upgrade and maintenance complexity.

## Localhost-First Configuration

The first safe deployment target is a loopback-only application port.

Example shape:

```text
OVERLEAF_LISTEN_IP=127.0.0.1
OVERLEAF_PORT=<local-port>
OVERLEAF_SITE_URL=http://127.0.0.1:<local-port>
SIBLING_CONTAINERS_ENABLED=false
NGINX_ENABLED=false
```

After a reverse proxy is configured, update the public-facing settings:

```text
OVERLEAF_SITE_URL=https://<public-overleaf-host>
OVERLEAF_BEHIND_PROXY=true
```

Then recreate the Overleaf web container through the Toolkit.

## Host Preparation Checklist

1. Confirm Docker and Docker Compose availability.
2. Confirm existing ports and avoid collisions with `80` and `443`.
3. Confirm Docker can pull images, including proxy configuration if the host requires one.
4. Inventory existing containers before Docker restart.
5. Avoid removing unrelated containers or host-level services.
6. Use a project-local deployment task directory for scripts, reports, and logs.

## Toolkit Flow

Generic sequence:

```bash
git clone https://github.com/overleaf/toolkit.git <toolkit-dir>
cd <toolkit-dir>
bin/init
# edit config/overleaf.rc and config/variables.env
bin/doctor
bin/up -d
```

When a host only has standalone `docker-compose`, verify Toolkit's compose wrapper before assuming the newer plugin is present.

## Admin Bootstrap Flow

1. Start Overleaf and wait for the web container to finish migrations.
2. Open `/launchpad` on the local endpoint.
3. Create the first administrator account.
4. Generate the initial password with a password generator.
5. Store credentials only in an approved private env file if the operator explicitly asks for local lookup.
6. Do not put passwords into reports, Git commits, task summaries, or public docs.

Example private env shape:

```text
OVERLEAF_URL=http://127.0.0.1:<local-port>
OVERLEAF_PUBLIC_URL=https://<public-overleaf-host>
OVERLEAF_ADMIN_EMAIL=<admin-email>
OVERLEAF_ADMIN_PASSWORD=<secret>
OVERLEAF_SSH_TUNNEL=ssh -L <local-port>:127.0.0.1:<local-port> <ssh-host>
```

The env file should be chmod `600` and gitignored.

## Verification Flow

### Container checks

```bash
cd <toolkit-dir>
SKIP_WARNINGS=true bin/docker-compose ps
```

Expected shape:

```text
sharelatex   127.0.0.1:<local-port>->80/tcp
mongo        healthy
redis        running
```

### HTTP checks

Before public proxy:

```text
GET /          -> redirects to /login
GET /login     -> 200
GET /launchpad -> redirects to /login after admin exists
GET /status    -> 200
```

After public proxy:

```text
GET http://127.0.0.1:<local-port>/login -> 200
GET https://<local-overleaf-host>/login  -> 200
GET https://<public-overleaf-host>/login -> 200
```

### Functional smoke

A useful smoke test is:

1. log in as admin;
2. create a sample project;
3. compile it;
4. verify compile status is success;
5. verify PDF or compile outputs can be downloaded.

## Reverse Proxy Pattern

The local nginx config should proxy the local host name to the loopback Overleaf upstream.

```nginx
server {
    listen 80;
    server_name <local-overleaf-host>;

    client_max_body_size 512m;

    location / {
        proxy_pass http://127.0.0.1:<local-port>;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }
}

server {
    listen 443 ssl;
    server_name <local-overleaf-host>;

    ssl_certificate <wildcard-cert-fullchain>;
    ssl_certificate_key <wildcard-cert-privkey>;

    client_max_body_size 512m;

    location / {
        proxy_pass http://127.0.0.1:<local-port>;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
    }
}
```

## Operations Cheatsheet

```bash
cd <toolkit-dir>
SKIP_WARNINGS=true bin/docker-compose ps
SKIP_WARNINGS=true bin/up -d
SKIP_WARNINGS=true bin/stop
```

Logs:

```bash
docker logs --tail=100 sharelatex
docker logs --tail=100 mongo
docker logs --tail=100 redis
```

Recreate after config updates:

```bash
cd <toolkit-dir>
SKIP_WARNINGS=true bin/up -d
```

## ChatOL Design Implications

- ChatOL must support self-hosted base URLs.
- ChatOL must support a configurable session cookie name.
- Password login should be available for self-hosted instances, but stored only in env/profile systems.
- Public URL and container upstream are different concepts; the client should only need the public/reverse-proxied base URL.
- Admin bootstrap is an operations workflow, not the same as the ordinary project editing API.
- Compile smoke testing should become a reusable optional live test once the client exists.
