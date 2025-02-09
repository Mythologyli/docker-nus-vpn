import os
import signal
import subprocess
import time

import pyotp
import requests


def run_command(dsid):
    command = f'openconnect --protocol=nc https://webvpn.nus.edu.sg/stu -i nus -C "DSID={
        dsid}"'
    if os.environ['NO_DTLS'] == 'true':
        command += ' --no-dtls'
    return subprocess.Popen(command, shell=True, preexec_fn=os.setsid)


def ping_host(host):
    command = ["ping", "-c", "1", host]
    result = subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def login():
    session = requests.session()

    resp = session.get("https://webvpn.nus.edu.sg/stu")

    resp = session.post(
        "https://vafs.u.nus.edu" +
        resp.text.split("Login.submitLoginRequest();\" action=\"")[
            1].split("\"")[0].strip(),
        data={
            "UserName": os.environ['VPN_USERNAME'],
            "Password": os.environ['VPN_PASSWORD'],
            "AuthMethod": "FormsAuthentication"
        }
    )

    url = resp.url

    context = resp.text.split(
        '<input id="context" type="hidden" name="Context" value="'
    )[1].split('"/>')[0].strip()

    resp = session.post(
        url,
        data={
            "AuthMethod": "AzureMfaAuthentication",
            "Context": context,
            "__EVENTTARGET": ""
        }
    )

    context = resp.text.split(
        '<input id="context" type="hidden" name="Context" value="'
    )[1].split('"/>')[0].strip()

    time.sleep(1)

    resp = session.post(
        url,
        data={
            "AuthMethod": "AzureMfaAuthentication",
            "Context": context,
            "__EVENTTARGET": "",
            "VerificationCode": pyotp.TOTP(os.environ['VPN_TOTP_SECRET']).now(),
            "SignIn": "Sign in"
        }
    )

    url = resp.text.split(
        '<form method="POST" name="hiddenform" action="'
    )[1].split('"')[0].strip()

    saml_response = resp.text.split(
        '<input type="hidden" name="SAMLResponse" value="'
    )[1].split('"')[0].strip()

    session.post(
        url,
        data={
            "RelayState": "https://webvpn.nus.edu.sg/stu",
            "SAMLResponse": saml_response
        }
    )

    return session.cookies["DSID"]


if __name__ == "__main__":
    while True:
        try:
            dsid = login()
            break
        except Exception as e:
            time.sleep(10)
    process = run_command(dsid)

    host_to_ping = os.environ['VPN_HOST_TO_PING']
    try:
        while True:
            time.sleep(60)
            if ping_host(host_to_ping):
                print(time.strftime("%H:%M:%S", time.localtime()), end=' ')
                print("Ping successful!")
            else:
                print(time.strftime("%H:%M:%S", time.localtime()), end=' ')
                print("Ping failed. Retrying...")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                time.sleep(10)
                while True:
                    try:
                        dsid = login()
                        break
                    except Exception as e:
                        time.sleep(10)
                process = run_command(dsid)
    except KeyboardInterrupt:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        print("Exiting...")
