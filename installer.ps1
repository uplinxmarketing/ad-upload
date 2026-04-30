#Requires -Version 5.0
<#
.SYNOPSIS
    Uplinx Meta Manager — Windows Installer
.DESCRIPTION
    GUI installer: choose directory → progress bar install → launch option.
    Right-click this file and choose "Run with PowerShell" to start.
    Must be run with PowerShell -Sta flag (Single-Threaded Apartment) for Windows Forms.
#>

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
} catch {
    [System.Windows.Forms.MessageBox]::Show(
        "Could not load Windows Forms:`n`n$_`n`nMake sure you are running PowerShell 5+ on Windows 10 or later.",
        "Uplinx Installer Error", "OK", "Error")
    exit 1
}

# ── Config ────────────────────────────────────────────────────────────────────
$AppName    = "Uplinx Meta Manager"
$GithubZip  = "https://github.com/uplinxmarketing/ad-upload/archive/refs/heads/main.zip"
$DefaultDir = "$env:LOCALAPPDATA\Uplinx"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Set-Label($lbl, $text) { $lbl.Text = $text; $form.Refresh() }
function Set-Progress($bar, $pct) { $bar.Value = [Math]::Min($pct, 100); $form.Refresh() }

# ── Colour palette ────────────────────────────────────────────────────────────
$bgDark   = [System.Drawing.Color]::FromArgb(13,13,20)
$bgCard   = [System.Drawing.Color]::FromArgb(22,22,31)
$accent   = [System.Drawing.Color]::FromArgb(108,99,255)
$txtLight = [System.Drawing.Color]::FromArgb(232,232,240)
$txtDim   = [System.Drawing.Color]::FromArgb(96,96,128)
$green    = [System.Drawing.Color]::FromArgb(34,197,94)

# ── Form ──────────────────────────────────────────────────────────────────────
$form = New-Object System.Windows.Forms.Form
$form.Text            = "$AppName — Installer"
$form.Size            = New-Object System.Drawing.Size(520,380)
$form.StartPosition   = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox     = $false
$form.BackColor       = $bgDark
$form.ForeColor       = $txtLight
$form.Font            = New-Object System.Drawing.Font("Segoe UI", 10)

# ── Panel helper ──────────────────────────────────────────────────────────────
function New-Panel {
    $p = New-Object System.Windows.Forms.Panel
    $p.Dock      = "Fill"
    $p.BackColor = $bgDark
    $p.Visible   = $false
    $form.Controls.Add($p)
    $p
}

function New-Lbl($text, $x, $y, $w, $h, $size=10, $bold=$false, $color=$null) {
    $l = New-Object System.Windows.Forms.Label
    $l.Text     = $text
    $l.Location = New-Object System.Drawing.Point($x,$y)
    $l.Size     = New-Object System.Drawing.Size($w,$h)
    $l.Font     = New-Object System.Drawing.Font("Segoe UI", $size, $(if($bold){"Bold"}else{"Regular"}))
    $l.ForeColor = if($color){$color}else{$txtLight}
    $l
}

function New-Btn($text, $x, $y, $w=120, $h=38) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text      = $text
    $b.Location  = New-Object System.Drawing.Point($x,$y)
    $b.Size      = New-Object System.Drawing.Size($w,$h)
    $b.FlatStyle = "Flat"
    $b.BackColor = $accent
    $b.ForeColor = [System.Drawing.Color]::White
    $b.Font      = New-Object System.Drawing.Font("Segoe UI", 10, "Bold")
    $b.FlatAppearance.BorderSize = 0
    $b.Cursor    = [System.Windows.Forms.Cursors]::Hand
    $b
}

# ══════════════════════════════════════════════════════════════════════════════
# Panel 1 — Welcome
# ══════════════════════════════════════════════════════════════════════════════
$pWelcome = New-Panel
$pWelcome.Visible = $true

$pWelcome.Controls.Add((New-Lbl "⚡" 40 50 60 60 36 $false $accent))
$pWelcome.Controls.Add((New-Lbl "Uplinx Meta Manager" 100 58 340 38 18 $true))
$pWelcome.Controls.Add((New-Lbl "AI-powered Meta advertising manager" 100 96 340 24 10 $false $txtDim))

$pWelcome.Controls.Add((New-Lbl "This installer will:" 40 155 440 24 10 $true))
$pWelcome.Controls.Add((New-Lbl "  • Download the latest version from GitHub" 40 180 440 22 10))
$pWelcome.Controls.Add((New-Lbl "  • Set up Python and all dependencies automatically" 40 202 440 22 10))
$pWelcome.Controls.Add((New-Lbl "  • Create a launch shortcut on your Desktop" 40 224 440 22 10))

$pWelcome.Controls.Add((New-Lbl "Requirements: Windows 10+, Python 3.10+, internet connection" 40 268 440 20 9 $false $txtDim))

$btnWelcomeNext = New-Btn "Next →" 370 305
$pWelcome.Controls.Add($btnWelcomeNext)
$btnWelcomeNext.Add_Click({ $pWelcome.Visible=$false; $pDir.Visible=$true })

# ══════════════════════════════════════════════════════════════════════════════
# Panel 2 — Directory selection
# ══════════════════════════════════════════════════════════════════════════════
$pDir = New-Panel

$pDir.Controls.Add((New-Lbl "Choose Install Location" 40 50 440 32 16 $true))
$pDir.Controls.Add((New-Lbl "Select the folder where Uplinx will be installed:" 40 88 440 22 10 $false $txtDim))

$txtDir = New-Object System.Windows.Forms.TextBox
$txtDir.Location  = New-Object System.Drawing.Point(40,125)
$txtDir.Size      = New-Object System.Drawing.Size(330,30)
$txtDir.Text      = $DefaultDir
$txtDir.BackColor = [System.Drawing.Color]::FromArgb(13,13,20)
$txtDir.ForeColor = $txtLight
$txtDir.BorderStyle = "FixedSingle"
$txtDir.Font      = New-Object System.Drawing.Font("Segoe UI",10)
$pDir.Controls.Add($txtDir)

$btnBrowse = New-Object System.Windows.Forms.Button
$btnBrowse.Text      = "Browse…"
$btnBrowse.Location  = New-Object System.Drawing.Point(378,124)
$btnBrowse.Size      = New-Object System.Drawing.Size(88,32)
$btnBrowse.FlatStyle = "Flat"
$btnBrowse.BackColor = [System.Drawing.Color]::FromArgb(37,37,64)
$btnBrowse.ForeColor = $txtLight
$btnBrowse.Font      = New-Object System.Drawing.Font("Segoe UI",10)
$btnBrowse.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(37,37,64)
$pDir.Controls.Add($btnBrowse)
$btnBrowse.Add_Click({
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select install folder"
    $dlg.SelectedPath = $txtDir.Text
    if ($dlg.ShowDialog() -eq "OK") { $txtDir.Text = $dlg.SelectedPath }
})

$pDir.Controls.Add((New-Lbl "Disk space needed: ~200 MB" 40 168 440 20 9 $false $txtDim))

$chkDesktop = New-Object System.Windows.Forms.CheckBox
$chkDesktop.Text      = "Create Desktop shortcut"
$chkDesktop.Location  = New-Object System.Drawing.Point(40,210)
$chkDesktop.Size      = New-Object System.Drawing.Size(300,24)
$chkDesktop.Checked   = $true
$chkDesktop.ForeColor = $txtLight
$chkDesktop.Font      = New-Object System.Drawing.Font("Segoe UI",10)
$pDir.Controls.Add($chkDesktop)

$btnDirBack = New-Btn "← Back" 240 305 110
$btnDirBack.BackColor = [System.Drawing.Color]::FromArgb(37,37,64)
$pDir.Controls.Add($btnDirBack)
$btnDirBack.Add_Click({ $pDir.Visible=$false; $pWelcome.Visible=$true })

$btnInstall = New-Btn "Install" 370 305
$pDir.Controls.Add($btnInstall)

# ══════════════════════════════════════════════════════════════════════════════
# Panel 3 — Progress
# ══════════════════════════════════════════════════════════════════════════════
$pProgress = New-Panel

$pProgress.Controls.Add((New-Lbl "Installing…" 40 50 440 32 16 $true))

$lblStep = New-Lbl "Starting…" 40 95 440 22 10 $false $txtDim
$pProgress.Controls.Add($lblStep)

$progBar = New-Object System.Windows.Forms.ProgressBar
$progBar.Location = New-Object System.Drawing.Point(40,130)
$progBar.Size     = New-Object System.Drawing.Size(430,22)
$progBar.Minimum  = 0
$progBar.Maximum  = 100
$progBar.Style    = "Continuous"
$pProgress.Controls.Add($progBar)

$lblLog = New-Lbl "" 40 165 430 120 9 $false $txtDim
$lblLog.AutoSize = $false
$pProgress.Controls.Add($lblLog)

# ══════════════════════════════════════════════════════════════════════════════
# Panel 4 — Finish
# ══════════════════════════════════════════════════════════════════════════════
$pFinish = New-Panel

$pFinish.Controls.Add((New-Lbl "✓" 40 50 60 60 36 $false $green))
$pFinish.Controls.Add((New-Lbl "Installation Complete!" 100 58 340 38 18 $true))
$pFinish.Controls.Add((New-Lbl "Uplinx Meta Manager is ready to use." 100 96 340 24 10 $false $txtDim))

$pFinish.Controls.Add((New-Lbl "Next steps:" 40 155 440 24 10 $true))
$pFinish.Controls.Add((New-Lbl "  1. Launch the app — it will open in your browser" 40 180 440 22 10))
$pFinish.Controls.Add((New-Lbl "  2. Enter your API keys in the Setup Wizard" 40 202 440 22 10))
$pFinish.Controls.Add((New-Lbl "  3. Paste your Meta access token to connect" 40 224 440 22 10))

$btnLaunch = New-Btn "Launch App 🚀" 260 305 160
$pFinish.Controls.Add($btnLaunch)
$btnLaunch.Add_Click({
    $startBat = Join-Path $script:InstallDir "start.bat"
    if (Test-Path $startBat) { Start-Process $startBat }
    else { [System.Windows.Forms.MessageBox]::Show("start.bat not found in $($script:InstallDir)") }
    $form.Close()
})

$btnClose = New-Btn "Close" 390 305 86
$btnClose.BackColor = [System.Drawing.Color]::FromArgb(37,37,64)
$pFinish.Controls.Add($btnClose)
$btnClose.Add_Click({ $form.Close() })

# ══════════════════════════════════════════════════════════════════════════════
# Install logic (runs in background job, updates UI via timer)
# ══════════════════════════════════════════════════════════════════════════════
$script:InstallDir = $DefaultDir
$script:JobDone    = $false
$script:JobError   = $null
$script:JobSteps   = [System.Collections.Queue]::new()

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 200
$timer.Add_Tick({
    while ($script:JobSteps.Count -gt 0) {
        $step = $script:JobSteps.Dequeue()
        Set-Label $lblStep $step.msg
        Set-Progress $progBar $step.pct
        $lblLog.Text = $step.log
    }
    if ($script:JobDone) {
        $timer.Stop()
        if ($script:JobError) {
            $pProgress.Visible = $false
            [System.Windows.Forms.MessageBox]::Show(
                "Installation failed:`n`n$($script:JobError)",
                "Error", "OK", "Error")
            $form.Close()
        } else {
            $pProgress.Visible = $false
            $pFinish.Visible   = $true
        }
    }
})

function Push-Step($msg, $pct, $log="") {
    $script:JobSteps.Enqueue(@{msg=$msg; pct=$pct; log=$log})
}

$btnInstall.Add_Click({
    $script:InstallDir = $txtDir.Text.Trim()
    $createShortcut    = $chkDesktop.Checked
    $pDir.Visible      = $false
    $pProgress.Visible = $true
    $timer.Start()

    $job = Start-Job -ScriptBlock {
        param($installDir, $createShortcut, $zipUrl)
        function Emit($msg, $pct, $log="") {
            [System.Console]::WriteLine("STEP|$pct|$msg|$log")
            [System.Console]::Out.Flush()
        }

        try {
            # 1 — Create directory
            Emit "Creating install directory…" 5
            New-Item -ItemType Directory -Force -Path $installDir | Out-Null

            # 2 — Download zip
            Emit "Downloading Uplinx from GitHub…" 10 "URL: $zipUrl"
            $zipPath = Join-Path $env:TEMP "uplinx_install.zip"
            Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

            # 3 — Extract
            Emit "Extracting files…" 35
            $tmpDir = Join-Path $env:TEMP "uplinx_extracted"
            if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
            Expand-Archive -Force $zipPath $tmpDir

            # 4 — Copy (preserve .env and DB)
            Emit "Copying files to install directory…" 50
            $srcDir = Join-Path $tmpDir "ad-upload-main"
            Get-ChildItem $srcDir | Where-Object {
                $_.Name -notin @('.env','uplinx.db','update.bat')
            } | Copy-Item -Destination $installDir -Recurse -Force
            Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
            Remove-Item $tmpDir  -Recurse -Force -ErrorAction SilentlyContinue

            # 5 — Find Python
            Emit "Locating Python…" 60
            $py = $null
            foreach ($cmd in @("py","python","python3")) {
                try {
                    $ver = & $cmd --version 2>&1
                    if ($ver -match "Python 3\.(1[0-9]|[89])") { $py = $cmd; break }
                } catch {}
            }
            if (-not $py) { throw "Python 3.10+ not found. Install from python.org or Microsoft Store." }

            # 6 — Create venv
            Emit "Creating virtual environment…" 70 "Using: $py"
            $venvPath = Join-Path $installDir "venv"
            if (-not (Test-Path $venvPath)) {
                & $py -m venv $venvPath 2>&1 | Out-Null
            }

            # 7 — Install dependencies
            Emit "Installing Python packages (may take 1-2 min)…" 78
            $pip = Join-Path $venvPath "Scripts\pip.exe"
            $req = Join-Path $installDir "requirements.txt"
            if (Test-Path $req) {
                & $pip install -r $req --quiet 2>&1 | Out-Null
            }

            # 8 — Create .env if missing
            Emit "Creating config file…" 92
            $envFile = Join-Path $installDir ".env"
            if (-not (Test-Path $envFile)) {
                @"
AI_PROVIDER=claude
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
META_APP_ID=
META_APP_SECRET=
"@ | Set-Content $envFile -Encoding UTF8
            }

            # 9 — Desktop shortcut
            if ($createShortcut) {
                Emit "Creating Desktop shortcut…" 95
                $startBat = Join-Path $installDir "start.bat"
                $lnkPath  = "$env:USERPROFILE\Desktop\Uplinx Meta Manager.lnk"
                $wsh = New-Object -ComObject WScript.Shell
                $lnk = $wsh.CreateShortcut($lnkPath)
                $lnk.TargetPath       = $startBat
                $lnk.WorkingDirectory = $installDir
                $lnk.Description      = "Uplinx Meta Manager"
                $lnk.IconLocation     = "%SystemRoot%\System32\SHELL32.dll,14"
                $lnk.Save()
            }

            Emit "Done!" 100
        } catch {
            [System.Console]::WriteLine("ERROR|$_")
            [System.Console]::Out.Flush()
        }
    } -ArgumentList $script:InstallDir, $createShortcut, $GithubZip

    # Poll job output
    $pollTimer = New-Object System.Windows.Forms.Timer
    $pollTimer.Interval = 300
    $pollTimer.Add_Tick({
        $output = Receive-Job $job -ErrorAction SilentlyContinue
        foreach ($line in ($output -split "`n")) {
            $line = $line.Trim()
            if ($line.StartsWith("STEP|")) {
                $parts = $line -split "\|", 4
                Push-Step $parts[2] ([int]$parts[1]) (if($parts.Count -gt 3){$parts[3]}else{""})
            } elseif ($line.StartsWith("ERROR|")) {
                $script:JobError = $line.Substring(6)
                $script:JobDone  = $true
                $pollTimer.Stop()
            }
        }
        if ($job.State -in "Completed","Failed","Stopped") {
            # Drain remaining output
            $final = Receive-Job $job -ErrorAction SilentlyContinue
            foreach ($line in ($final -split "`n")) {
                $line = $line.Trim()
                if ($line.StartsWith("STEP|")) {
                    $parts = $line -split "\|", 4
                    Push-Step $parts[2] ([int]$parts[1]) (if($parts.Count -gt 3){$parts[3]}else{""})
                } elseif ($line.StartsWith("ERROR|")) {
                    $script:JobError = $line.Substring(6)
                }
            }
            Remove-Job $job -Force
            $script:JobDone = $true
            $pollTimer.Stop()
        }
    })
    $pollTimer.Start()
})

# ── Show form ─────────────────────────────────────────────────────────────────
try {
    [System.Windows.Forms.Application]::EnableVisualStyles()
    $form.ShowDialog() | Out-Null
} catch {
    [System.Windows.Forms.MessageBox]::Show(
        "Installer error:`n`n$_",
        "Uplinx Installer", "OK", "Error")
}
