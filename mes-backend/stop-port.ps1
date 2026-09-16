# Giải phóng một cổng TCP trên Windows.  Dùng:  ./run.sh stop [cổng]
#
# Vì sao cần cả file này thay vì một dòng `kill`:
#
#   * `pkill` của Git Bash không với tới tiến trình Windows.
#   * `uvicorn --reload` chạy HAI tiến trình: cha theo dõi file, con phục vụ
#     HTTP. Con sinh ra qua `multiprocessing.spawn` nên dòng lệnh của nó KHÔNG
#     chứa chữ "uvicorn" — lọc theo tên là trượt.
#   * Giết mỗi cha thì con vẫn giữ socket, cổng vẫn bận. Giết mỗi con thì cha
#     sinh con mới. Phải giết CẢ HAI, con trước.

param([int]$Port = 8000)

$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $conns) { Write-Output "cong $Port dang trong"; exit 0 }

foreach ($owner in ($conns.OwningProcess | Select-Object -Unique)) {

    # Con trước: mọi python có `parent_pid=<owner>` trong dòng lệnh.
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*parent_pid=$owner*" } |
        ForEach-Object {
            Write-Output "tat tien trinh con $($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }

    # Rồi tới cha — nếu nó còn sống.
    if (Get-Process -Id $owner -ErrorAction SilentlyContinue) {
        Write-Output "tat PID $owner"
        Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Milliseconds 800
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Write-Output "CANH BAO: cong $Port van con bi giu"
    exit 1
}
Write-Output "cong $Port da trong"
