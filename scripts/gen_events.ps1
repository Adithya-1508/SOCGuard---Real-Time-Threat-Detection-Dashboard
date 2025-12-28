$api = "http://localhost:8000/api/ingest"

function Send-Event($body) {
    try {
        Invoke-WebRequest -Uri $api -Method POST -Headers @{ "Content-Type" = "application/json" } -Body ($body | ConvertTo-Json -Depth 5) -UseBasicParsing | Out-Null
    } catch {
        Write-Host "Error sending event: $_"
    }
}

# Send normal events
for ($i=0; $i -lt 300; $i++) {
    $ip = "192.168.$((Get-Random -Minimum 0 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 254))"
    $body = @{
        source = "web"
        message = "page_view"
        ip = $ip
        user = "user$((Get-Random -Minimum 1 -Maximum 400))"
        metadata = @{ ua = "Mozilla/5.0" }
    }
    Send-Event $body
    Start-Sleep -Milliseconds (Get-Random -Minimum 5 -Maximum 30)
}

# Bruteforce bursts
for ($b=0; $b -lt 25; $b++) {
    $att = "$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 254))"
    for ($a=0; $a -lt 20; $a++) {
        $body = @{
            source = "auth"
            message = "Failed login attempt"
            ip = $att
            user = "admin"
            metadata = @{ ua = "python-requests/2.31.0" }
        }
        Send-Event $body
        Start-Sleep -Milliseconds (Get-Random -Minimum 5 -Maximum 30)
    }
}

# Port-scan like events
for ($s=0; $s -lt 25; $s++) {
    $scanIp = "$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 255)).$((Get-Random -Minimum 1 -Maximum 254))"
    for ($e=0; $e -lt 40; $e++) {
        $body = @{
            source = "net"
            message = "Port scan attempt port=$((Get-Random -Minimum 1 -Maximum 65535))"
            ip = $scanIp
            user = $null
            metadata = @{ ua = "mass-scan-tool" }
        }
        Send-Event $body
        Start-Sleep -Milliseconds (Get-Random -Minimum 1 -Maximum 15)
    }
}
