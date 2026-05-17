#!/bin/sh

# 0. Check directory location
# 1. Install tools
# 2. Build source code
# 3. Setup daemons
# 4. Run daemons


# check directory location
if [[ "$(pwd)" != "root/traffic_stat" ]]; then
    echo "project located at $(pwd), should at root/traffic_stat"
    exit 1
fi

# install tools
which go || sudo apt install go
which uv || curl -LsSf https://astral.sh/uv/install.sh | sh

# check installed tools
if [[ "$(which uv)" != "$HOME/.local/bin" ]]; then
    echo "uv located at $(which uv), should at ~/.local/bin"
    exit 1
fi

# build go source code
go build .

# setup daemons
cp traffic_stat_bot.service /etc/systemd/system/traffic_stat_bot.service
cp traffic_stat_collect.service /etc/systemd/system/traffic_stat_collect.service

# start the service
systemctl daemon-reload
systemctl enable traffic_stat_bot
systemctl start traffic_stat_bot
systemctl enable traffic_stat_collect
systemctl start traffic_stat_collect
