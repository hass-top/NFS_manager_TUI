#!/bin/bash
EXPORT_PATH=$1
CLIENT_IP=$2
ACCESS_MODE=$3 
SYNC_MODE=$4 
SUBTREE_OPTION=$5

INVALID_PATHS=(/proc /dev /run /sys /etc  )

if [[ "$SUBTREE_OPTION" != "no_subtree_check" && "$SUBTREE_OPTION" != "subtree_check" ]]; then
    echo "Error: SUBTREE_OPTION must be 'no_subtree_check' or 'subtree_check'. Got '$SUBTREE_OPTION'." >&2
    exit 1
fi

if [[ "$ACCESS_MODE" != "rw" && "$ACCESS_MODE" != "ro" ]]; then
    echo "Error: ACCESS_MODE must be 'rw' or 'ro'. Got '$ACCESS_MODE'." >&2
    exit 1
fi

if [[ "$SYNC_MODE" != "sync" && "$SYNC_MODE" != "async" ]]; then
    echo "Error: SYNC_MODE must be 'sync' or 'async'. Got '$SYNC_MODE'." >&2
    exit 1
fi

if [ "$CLIENT_IP" != "*" ]; then
    # Check if it's a valid IPv4 format
    if [[ ! "$CLIENT_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9]{1,2})?$ ]]; then
        echo "Error: CLIENT_IP '$CLIENT_IP' is not a valid IPv4 or subnet." >&2
        exit 1
    fi


    # Extract base IP if subnet is not provided
    if [[ "$CLIENT_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        # Test if host is reachable
        if ! ping -c1 -W1 "$CLIENT_IP" >/dev/null 2>&1; then
            echo "Error: CLIENT_IP '$CLIENT_IP' is not reachable on the network." >&2
            exit 1
        fi
    fi
fi
# Check if export path is provided
if [ -z "$EXPORT_PATH" ]; then
    echo "Error: Export path not provided." >&2
    exit 1
fi

# Check if export path exists
if [ ! -d "$EXPORT_PATH" ]; then
    echo "Error: Directory $EXPORT_PATH does not exist." >&2
    exit 1
fi

# Check if export path is invalid
for path in "${INVALID_PATHS[@]}"; do
    if [[ "$EXPORT_PATH" == "$path"* ]]; then
        echo "Error: Export path $EXPORT_PATH is invalid." >&2
        exit 1
    fi
done 

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)." >&2
    exit 1
fi

## Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID=$ID
else
    echo "Error: Cannot detect OS." >&2
    exit 1
fi

# Install NFS server packages
case "$OS_ID" in
    ubuntu|debian)
        pkg="nfs-kernel-server"
        if ! dpkg -s $pkg >/dev/null 2>&1; then
            echo "Installing $pkg..."
            apt update && apt install -y $pkg || exit 1
        fi
        nfs_service="nfs-kernel-server"
        ;;
    centos|rhel|fedora|rocky)
        pkg="nfs-utils"
        if ! rpm -q $pkg >/dev/null 2>&1; then
            echo "Installing $pkg..."
            yum install -y $pkg || exit 1
        fi
        nfs_service="nfs-server"
        ;;
    arch)
        pkg="nfs-utils"
        if ! pacman -Qs $pkg >/dev/null; then
            echo "Installing $pkg..."
            pacman -S --noconfirm $pkg || exit 1
        fi
        nfs_service="nfs-server"
        ;;
    suse|opensuse)
        pkg="nfs-kernel-server"
        if ! rpm -q $pkg >/dev/null 2>&1; then
            echo "Installing $pkg..."
            zypper install -y $pkg || exit 1
        fi
        nfs_service="nfsserver"
        ;;
    *)
        echo "Error: Unsupported OS $OS_ID" >&2
        exit 1
        ;;
esac


# Check if export path is already in /etc/exports
if ! grep -q "^$EXPORT_PATH " /etc/exports 2>/dev/null; then
    echo "$EXPORT_PATH $CLIENT_IP($ACCESS_MODE,$SYNC_MODE,$SUBTREE_OPTION)" >> /etc/exports || {
        echo "Error: Failed to update /etc/exports." >&2
        exit 1
    }
else
    echo "[i] $EXPORT_PATH already exists in /etc/exports"
fi


# Refresh exports
exportfs -ra || {
    echo "Error: Failed to refresh exports." >&2
    exit 1
}

# Enable and start NFS services
systemctl enable --now nfs-server.service || {
    echo "Error: Failed to enable or start nfs-server.service." >&2
    exit 1
}

# Verify service is running
if systemctl is-active --quiet nfs-server.service; then
    echo "NFS server configured successfully for $EXPORT_PATH"
else
    echo "Error: NFS server is not running." >&2
    exit 1
fi
