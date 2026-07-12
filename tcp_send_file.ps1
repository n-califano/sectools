param(
    [Parameter(Mandatory=$true)]
    [string]$ip,

    [Parameter()]
    [int]$port = 9001,

    [Parameter(Mandatory=$true)]
    [string]$filepath,
)

$client = New-Object System.Net.Sockets.TcpClient($ip, $port)
$stream = $client.GetStream()
$fileStream = [System.IO.File]::OpenRead($filepath)
$buffer = New-Object byte[] 4096
while (($read = $fileStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
    $stream.Write($buffer, 0, $read)
}
$stream.Flush()
$fileStream.Close()
$stream.Close()
$client.Close()