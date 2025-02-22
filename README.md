install poetry
curl -sSL https://install.python-poetry.org | python3 -

~/.bashrc

export PATH="/home/pi/.local/bin:$PATH"
export PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring

reload

install chromium


server: 
 - every hour:
  - get events
  - render picture

client:
 - on boot:
   - scp image from server 
   - display image
   - set battery timer
   - shutdown