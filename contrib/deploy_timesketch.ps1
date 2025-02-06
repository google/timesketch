# Requires powershell 6.0 or newer - just because the out-file does not support encoding of UTF8NoBom on older versions.
# This is a copy from the official Bash script of Timesketch. https://timesketch.org/
# https://raw.githubusercontent.com/hnhdev/timesketch/main/contrib/deploy_timesketch.sh
# Some of the functionality might be still missing that is present on the bash script.

# Check for the existing timesketch path
if (Test-Path -path timesketch) {
	write-host "ERROR: Timesketch directory already exist."
	exit
}

# Check if the docker service is available and running
if((Get-Service com.docker.service).status -ne "Running") {
	write-host "ERROR: Docker is not available."
	exit
}

# Check if Timesketch container is already present
if ((docker ps | sls timesketch) -ne $null) {
	write-host "ERROR: Timesketch containers already running."
	exit
}

#set the vm.max_map_count for OpenSearch in WSL
write-host "Set the vm.max_map_count for OpenSearch"
wsl -d docker-desktop sysctl -w vm.max_map_count=262144

# Create dirs.
# Casting to void to avoid output.
[void](New-Item -ItemType Directory -Name timesketch)
[void](New-Item -ItemType Directory -Name timesketch\data)
[void](New-Item -ItemType Directory -Name timesketch\data\postgresql)
[void](New-Item -ItemType Directory -Name timesketch\data\opensearch)
[void](New-Item -ItemType Directory -Name timesketch\logs)
[void](New-Item -ItemType Directory -Name timesketch\etc)
[void](New-Item -ItemType Directory -Name timesketch\etc\timesketch)
[void](New-Item -ItemType Directory -Name timesketch\etc\timesketch\sigma)
[void](New-Item -ItemType Directory -Name timesketch\etc\timesketch\sigma\rules)
[void](New-Item -ItemType Directory -Name timesketch\upload)

# function to get Cryptographically random alphanumeric characters
$CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
Function Get-RandomString {
    Param($length)
    $KEY = ""
    for($i = 0; $i -lt [int]$length; $i++)
    {
        [byte[]] $byte = 1
        $rng.GetBytes($byte)
        $KEY = $KEY + $CHARS[[int]$byte[0]%62]
    }
    $KEY
}

# config parameters
Write-Host "* Setting default config parameters.."
$POSTGRES_USER="timesketch"
$POSTGRES_PASSWORD=Get-RandomString -length 42 
$POSTGRES_ADDRESS="postgres"
$POSTGRES_PORT="5432"
$SECRET_KEY=Get-RandomString -length 42
$OPENSEARCH_ADDRESS="opensearch"
$OPENSEARCH_PORT="9200"
# The command below will take half of the system memory. This can be changed to whatever suits you. More the merrier for the ES though.
$OPENSEARCH_MEM_USE_GB=(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum /1gb / 2
$REDIS_ADDRESS="redis"
$REDIS_PORT="6379"
$GITHUB_BASE_URL="https://raw.githubusercontent.com/hnhdev/timesketch/main"
Write-Host "OK"
Write-Host "Setting OpenSearch memory allocation to $OPENSEARCH_MEM_USE_GB GB"

# Docker compose and configuration
Write-Host "* Fetching configuration files.."
(Invoke-webrequest -URI $GITHUB_BASE_URL/docker/release/docker-compose.yml).Content > timesketch\docker-compose.yml
(Invoke-webrequest -URI $GITHUB_BASE_URL/docker/release/config.env).Content > timesketch\config.env

# Fetch default Timesketch config files
# The encoding is set as UTF8NoBOM as otherwise the dockers can't read the configurations right.
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/timesketch.conf).Content | out-file timesketch\etc\timesketch\timesketch.conf -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/tags.yaml).Content | out-file timesketch\etc\timesketch\tags.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/plaso.mappings).Content | out-file timesketch\etc\timesketch\plaso.mappings -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/generic.mappings).Content | out-file timesketch\etc\timesketch\generic.mappings -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/regex_features.yaml).Content | out-file timesketch\etc\timesketch\regex_features.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/winevt_features.yaml).Content | out-file timesketch\etc\timesketch\winevt_features.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/ontology.yaml).Content | out-file timesketch\etc\timesketch\ontology.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/intelligence_tag_metadata.yaml).Content | out-file timesketch\etc\timesketch\intelligence_tag_metadata.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/sigma_config.yaml).Content | out-file timesketch\etc\timesketch\sigma_config.yaml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/data/sigma/rules/lnx_susp_zmap.yml).Content | out-file timesketch\etc\timesketch\sigma\rules\lnx_susp_zmap.yml -encoding UTF8NoBOM
(Invoke-webrequest -URI $GITHUB_BASE_URL/contrib/nginx.conf).Content | out-file timesketch\etc\nginx.conf -encoding UTF8NoBOM
Write-Host "OK"

# Create a minimal Timesketch config
Write-Host "* Edit configuration files."
$timesketchconf = 'timesketch\etc\timesketch\timesketch.conf'
$convfenv = 'timesketch\config.env'
(Get-Content $timesketchconf).replace("SECRET_KEY = '<KEY_GOES_HERE>'", "SECRET_KEY = '$SECRET_KEY'") | Set-Content $timesketchconf

# Set up the OpenSearch connection
(Get-Content $timesketchconf).replace("OPENSEARCH_HOST = '127.0.0.1'", "ELASTIC_HOST = '$OPENSEARCH_ADDRESS'") | Set-Content $timesketchconf
(Get-Content $timesketchconf).replace("OPENSEARCH_PORT = 9200", "ELASTIC_PORT = $OPENSEARCH_PORT") | Set-Content $timesketchconf

# Set up the Redis connection
(Get-Content $timesketchconf).replace("UPLOAD_ENABLED = False", "UPLOAD_ENABLED = True") | Set-Content $timesketchconf
(Get-Content $timesketchconf).replace("UPLOAD_FOLDER = '/tmp'", "UPLOAD_FOLDER = '/usr/share/timesketch/upload'") | Set-Content $timesketchconf

(Get-Content $timesketchconf).replace("CELERY_BROKER_URL = 'redis://127.0.0.1:6379'", "CELERY_BROKER_URL = 'redis://$($REDIS_ADDRESS):$($REDIS_PORT)'") | Set-Content $timesketchconf
(Get-Content $timesketchconf).replace("CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'", "CELERY_RESULT_BACKEND = 'redis://$($REDIS_ADDRESS):$($REDIS_PORT)'") | Set-Content $timesketchconf

# Set up the Postgres connection
(Get-Content $timesketchconf).replace("SQLALCHEMY_DATABASE_URI = 'postgresql://<USERNAME>:<PASSWORD>@localhost/timesketch'", "SQLALCHEMY_DATABASE_URI = 'postgresql://$($POSTGRES_USER):$($POSTGRES_PASSWORD)@$($POSTGRES_ADDRESS):$($POSTGRES_PORT)/timesketch'") | Set-Content $timesketchconf

(Get-Content $convfenv).replace("POSTGRES_PASSWORD=", "POSTGRES_PASSWORD=$POSTGRES_PASSWORD") | Set-Content $convfenv
(Get-Content $convfenv).replace("OPENSEARCH_MEM_USE_GB=", "OPENSEARCH_MEM_USE_GB=$OPENSEARCH_MEM_USE_GB") | Set-Content $convfenv

copy-item -Path $convfenv -Destination timesketch\.env
Write-Host "OK"
Write-Host "* Installation done."

Write-Host "--"
Write-Host "--"
Write-Host "--"
Write-Host "Start the system:"
Write-Host "1. cd timesketch"
Write-Host "2. docker compose up -d"
Write-Host "3. docker compose exec timesketch-web tsctl create-user <USERNAME>"
Write-Host "--"
Write-Host "WARNING: The server is running without encryption."
Write-Host "Follow the instructions to enable SSL to secure the communications:"
Write-Host "https://github.com/hnhdev/timesketch/blob/main/docs/Installation.md"
