# sweetshot
HTTP client for Steepshot API

# useful
https://blog.agchapman.com/setting-up-a-teamcity-build-environment-using-docker/
sudo shutdown -r now

# teamcity setup
1) Create directory structure
/opt/teamcity/
├── agent
├── config
├── data
├── log
└── docker-compose.yml

2) copy docker-compose.yml

3) firewal
sudo ufw allow ssh
sudo ufw allow https
sudo ufw allow http
sudo ufw allow 8111
sudo ufw enable
sudo ufw status

4) docker-compose up -d