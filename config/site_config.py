# imports - standard imports
import json
import os
from collections import defaultdict


def get_site_config(site, aksara_path="."):
    config_path = os.path.join(aksara_path, "sites", site, "site_config.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        return json.load(f)


def put_site_config(site, config, aksara_path="."):
    config_path = os.path.join(aksara_path, "sites", site, "site_config.json")
    with open(config_path, "w") as f:
        return json.dump(config, f, indent=1)


def update_site_config(site, new_config, aksara_path="."):
    config = get_site_config(site, aksara_path=aksara_path)
    config.update(new_config)
    put_site_config(site, config, aksara_path=aksara_path)


def set_nginx_port(site, port, aksara_path=".", gen_config=True):
    set_site_config_nginx_property(
        site, {"nginx_port": port}, aksara_path=aksara_path, gen_config=gen_config
    )


def set_ssl_certificate(site, ssl_certificate, aksara_path=".", gen_config=True):
    set_site_config_nginx_property(
        site,
        {"ssl_certificate": ssl_certificate},
        aksara_path=aksara_path,
        gen_config=gen_config,
    )


def set_ssl_certificate_key(
    site, ssl_certificate_key, aksara_path=".", gen_config=True
):
    set_site_config_nginx_property(
        site,
        {"ssl_certificate_key": ssl_certificate_key},
        aksara_path=aksara_path,
        gen_config=gen_config,
    )


def set_site_config_nginx_property(site, config, aksara_path=".", gen_config=True):
    from aksara.config.nginx import make_nginx_conf
    from aksara.aksara import Aksara

    if site not in Aksara(aksara_path).sites:
        raise Exception("No such site")
    update_site_config(site, config, aksara_path=aksara_path)
    if gen_config:
        make_nginx_conf(aksara_path=aksara_path)


def set_url_root(site, url_root, aksara_path="."):
    update_site_config(site, {"host_name": url_root}, aksara_path=aksara_path)


def add_domain(site, domain, ssl_certificate, ssl_certificate_key, aksara_path="."):
    domains = get_domains(site, aksara_path)
    for d in domains:
        if (isinstance(d, dict) and d["domain"] == domain) or d == domain:
            print(f"Domain {domain} already exists")
            return

    if ssl_certificate_key and ssl_certificate:
        domain = {
            "domain": domain,
            "ssl_certificate": ssl_certificate,
            "ssl_certificate_key": ssl_certificate_key,
        }

    domains.append(domain)
    update_site_config(site, {"domains": domains}, aksara_path=aksara_path)


def remove_domain(site, domain, aksara_path="."):
    domains = get_domains(site, aksara_path)
    for i, d in enumerate(domains):
        if (isinstance(d, dict) and d["domain"] == domain) or d == domain:
            domains.remove(d)
            break

    update_site_config(site, {"domains": domains}, aksara_path=aksara_path)


def sync_domains(site, domains, aksara_path="."):
    """Checks if there is a change in domains. If yes, updates the domains list."""
    changed = False
    existing_domains = get_domains_dict(get_domains(site, aksara_path))
    new_domains = get_domains_dict(domains)

    if set(existing_domains.keys()) != set(new_domains.keys()):
        changed = True

    else:
        for d in list(existing_domains.values()):
            if d != new_domains.get(d["domain"]):
                changed = True
                break

    if changed:
        # replace existing domains with this one
        update_site_config(site, {"domains": domains}, aksara_path=".")

    return changed


def get_domains(site, aksara_path="."):
    return get_site_config(site, aksara_path=aksara_path).get("domains") or []


def get_domains_dict(domains):
    domains_dict = defaultdict(dict)
    for d in domains:
        if isinstance(d, str):
            domains_dict[d] = {"domain": d}

        elif isinstance(d, dict):
            domains_dict[d["domain"]] = d

    return domains_dict
