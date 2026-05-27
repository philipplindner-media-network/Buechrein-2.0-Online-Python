# ==============================================================================
# Start-Script for Buecherei 2.0 Online
# Checks dependencies, configuration and network connection.
# ==============================================================================

$PYTHON_CMD = "python"

# Parallel arrays: MODULE_NAMES (Import-Name) to PACKAGE_NAMES (pip Install-Name)
# NOTE: PIL is imported, but Pillow must be installed.
$MODULE_NAMES = @("requests", "PIL", "mysql.connector")
$PACKAGE_NAMES = @("requests", "Pillow", "mysql-connector-python")

# --- 1. Check and install critical Python dependencies ---
Write-Host "[PYTHON] Checking and installing critical Python dependencies..."

$MISSING_DEPS = $false
$NUM_DEPS = $MODULE_NAMES.Length

for ($i = 0; $i -lt $NUM_DEPS; $i++) {
    $MODULE = $MODULE_NAMES[$i]
    $PACKAGE = $PACKAGE_NAMES[$i]

    # Try to import the module to check existence
    # Output of Python command is suppressed.
    & $PYTHON_CMD -c "import $MODULE" 2>$null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Critical dependency '$MODULE' (Package: $PACKAGE) is missing. Trying installation..."
        # Try installation
        & python -m pip install $PACKAGE 2>$null

        # Check again after installation
        & $PYTHON_CMD -c "import $MODULE" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Error: '$MODULE' could NOT be installed or found."
            $MISSING_DEPS = $true
        }
    }
}

if ($MISSING_DEPS) {
    Write-Host "[ERROR] The program cannot start due to missing critical dependencies."
    Write-Host "Please fix the pip errors."
    exit 1
}

Write-Host "[OK] All critical Python dependencies are present."

# --- 2. Check configuration files and start setup if necessary ---
Write-Host "[CONFIG] Checking for necessary configuration files..."

$CONFIG_FILES = @("config.json", "db_config.json", "users.json")
$MISSING_FILE = $false

foreach ($file in $CONFIG_FILES) {
    if (!(Test-Path $file)) {
        Write-Host "[ERROR] Error: Configuration file '$file' is missing."
        $MISSING_FILE = $true
    }
}

if ($MISSING_FILE) {
    Write-Host "[WARNING] Starting setup routine (setup.py)..."
    & $PYTHON_CMD setup.py

    # NEW CHECK: If setup ran, everything must be successful.
    foreach ($file in $CONFIG_FILES) {
        if (!(Test-Path $file)) {
            Write-Host "[ERROR] Setup completed, but '$file' is still missing. Aborting."
            exit 1
        }
    }

    Write-Host "[OK] Setup completed successfully. Configuration is present."
}

# --- 3. Check internet connection ---

Write-Host "[NETWORK] Checking internet connection..."

# Try to ping Google DNS (8.8.8.8). Timeout 5 seconds.
if (!(Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet)) {
    Write-Host "[ERROR] Error: No active internet connection found."
    Write-Host "The online program cannot start without network connection. Aborting."
    exit 1
}

Write-Host "[OK] Internet connection is stable."

# --- 4. Start main program ---

Write-Host "[START] Starting main program all.py..."
& $PYTHON_CMD all.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] all.py ended with an error."
    exit 1
}

Write-Host "Program ended successfully."
exit 0