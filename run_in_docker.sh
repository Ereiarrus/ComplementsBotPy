set -a
source .env

received_github_token=""

if "$TMI_TOKEN" != "$received_github_token"; then
  echo "Wrong sender; exiting"
  exit 1
fi

set +a
