# Docker NUS VPN

## Build the image
```bash
docker build -t nus-vpn .
```

## Run the container
```bash
docker run -e VPN_USERNAME="e0000000@u.nus.edu" -e VPN_PASSWORD="password" -e VPN_TOTP_SECRET="xxxxxxxxx" -p 10800:10800 -it --privileged --name nus-vpn nus-vpn
```
