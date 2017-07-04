# sweetshot
HTTP client for Steepshot API

# useful
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

5) http://45.55.190.241:8111

6) Agents -> Authorize

7) Add project from github

8) Setup build steps:
    - nuget restore -> Command Line -> Custom script: nuget restore
    - get-nunit -> Command Line -> Custom script: nuget install NUnit.Console -version 3.6.0 -o ~/home/nunit/
    - msbuild -> Command Line -> Custom script: msbuild
    - run-nunit -> Command Line -> Custom script: mono ~/home/nunit/NUnit.ConsoleRunner.3.6.0/tools/nunit3-console.exe src/Sweetshot.Tests/bin/Debug/Sweetshot.Tests.dll

9) Add logic for chaging settings on the fly:
    - update run-nunit command:
    sed -i "s/\(<steem_url.*>\)[^<>]*\(<\/steem_url.*\)/\1$https://steepshot.org/api/v1/\2/" $App.config
    sed -i "s/\(<golos_url.*>\)[^<>]*\(<\/golos_url.*\)/\1$https://golos.steepshot.org/api/v1/\2/" $App.config

    sed -i "s/\(<steem_url.*>\)[^<>]*\(<\/steem_url.*\)/\1$https://qa.steepshot.org/api/v1/\2/" $App.config
    sed -i "s/\(<golos_url.*>\)[^<>]*\(<\/golos_url.*\)/\1$https://qa.golos.steepshot.org/api/v1/\2/" $App.config