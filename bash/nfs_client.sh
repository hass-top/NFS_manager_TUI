#!/bin/bash

SERVER_IP="$1"
EXPORT_PATH="$2"
MOUNT_POINT="$3"

# Function to validate IPv4
validate_ip() {
    local ip=$1
    local stat=1

    # IPv4 regex
    if [[ $ip =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        # Check each octet <= 255
        IFS='.' read -r -a octets <<< "$ip"
        for octet in "${octets[@]}"; do
            if (( octet < 0 || octet > 255 )); then
                return 1
            fi
        done
        stat=0
    fi
    return $stat
}

# Validate inputs
if [ -z "$SERVER_IP" ] || [ -z "$EXPORT_PATH" ] || [ -z "$MOUNT_POINT" ]; then
    echo "Error: All fields (server_ip, export_path, mount_point) are required." >&2
    exit 1
fi

# Validate IP format
if ! validate_ip "$SERVER_IP"; then
    echo "Error: '$SERVER_IP' is not a valid IPv4 address. Example: 192.168.1.13" >&2
    exit 1
fi

echo "[+] IP format valid: $SERVER_IP"

# Check if IP is reachable
if ping -c 1 -W 1 "$SERVER_IP" &>/dev/null; then
    echo "[+] Server $SERVER_IP is reachable."
else
    echo "Error: Server $SERVER_IP is not reachable." >&2
    exit 1
fi

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run with sudo." >&2
    exit 1
fi

# Validate MOUNT_POINT path
if [[ ! "$MOUNT_POINT" =~ ^/.* ]] || [[ "$MOUNT_POINT" =~ [[:space:]] ]]; then
    echo "Error: Invalid mount point '$MOUNT_POINT'. It must be an absolute path without spaces." >&2
    exit 1
fi

# Validate EXPORT_PATH format
if [[ ! "$EXPORT_PATH" =~ ^/.* ]]; then
    echo "Error: Invalid export path '$EXPORT_PATH'. It must be an absolute path." >&2
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    os=$ID
else
    echo "Error: Unable to detect the OS." >&2
    exit 1
fi

# Install NFS client
install_nfs_client() {
    case "$os" in
        arch)
            if ! pacman -Qi nfs-utils &>/dev/null; then
                pacman -S --noconfirm nfs-utils || {
                    echo "Error: Failed to install nfs-utils." >&2
                    exit 1
                }
            else
                echo "[+] nfs-utils already installed, skipping..."
            fi
            ;;
        ubuntu|debian)
            apt-get update && apt-get install -y nfs-common || {
                echo "Error: Failed to install nfs-common." >&2
                exit 1
            }
            ;;
        centos|rhel|fedora|rocky)
            dnf install -y nfs-utils || yum install -y nfs-utils || {
                echo "Error: Failed to install nfs-utils." >&2
                exit 1
            }
            ;;
        *)
            echo "Error: Unsupported OS '$os'. Please add support for your OS." >&2
            exit 1
            ;;
    esac
}

install_nfs_client

# Ensure NFS services are running
systemctl is-active --quiet nfs-server && systemctl is-active --quiet rpcbind || {
    echo "Warning: NFS server or rpcbind service is not running. Starting services..." >&2
    systemctl start nfs-server rpcbind || {
        echo "Error: Failed to start NFS services." >&2
        exit 1
    }
}

# Check NFS ports
if ! ss -tuln | grep -q ":2049"; then
    echo "Error: NFS port 2049 is not open. Check firewall or NFS service." >&2
    exit 1
fi
if ! ss -tuln | grep -q ":111"; then
    echo "Error: RPC port 111 is not open. Check firewall or rpcbind service." >&2
    exit 1
fi

# Verify export path exists on server
if ! showmount -e "$SERVER_IP" | grep -q "$EXPORT_PATH"; then
    echo "Error: Export path '$EXPORT_PATH' not found on server $SERVER_IP. Available exports:" >&2
    showmount -e "$SERVER_IP" >&2
    exit 1
fi

# Create and validate mount point
echo "[+] Creating mount point at $MOUNT_POINT"
if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT" || {
        echo "Error: Failed to create mount point $MOUNT_POINT." >&2
        exit 1
    }
    chmod 755 "$MOUNT_POINT" || {
        echo "Error: Failed to set permissions on $MOUNT_POINT." >&2
        exit 1
    }
else
    if [ -n "$(ls -A "$MOUNT_POINT")" ] && ! mountpoint -q "$MOUNT_POINT"; then
        echo "Warning: Mount point $MOUNT_POINT exists and is non-empty. Ensure it is safe to use." >&2
    else
        echo "[+] Mount point already exists at $MOUNT_POINT"
    fi
fi

# Mount NFS share
if mountpoint -q "$MOUNT_POINT"; then
    if mount | grep -q "$SERVER_IP:$EXPORT_PATH on $MOUNT_POINT"; then
        echo "[+] $SERVER_IP:$EXPORT_PATH already mounted on $MOUNT_POINT"
    else
        echo "Error: $MOUNT_POINT is mounted but not with $SERVER_IP:$EXPORT_PATH" >&2
        exit 1
    fi
else
    # Attempt to mount with NFSv4.2
    mount -t nfs -o vers=4.2 "$SERVER_IP:$EXPORT_PATH" "$MOUNT_POINT" || {
        echo "Error: Failed to mount $SERVER_IP:$EXPORT_PATH to $MOUNT_POINT. Check server IP, export path, permissions, or firewall." >&2
        exit 1
    }
    echo "[+] Successfully mounted $SERVER_IP:$EXPORT_PATH to $MOUNT_POINT"
fi

# Update /etc/fstab
fstab_entry="$SERVER_IP:$EXPORT_PATH $MOUNT_POINT nfs defaults,vers=4.2 0 0"
if ! grep -Fx "$fstab_entry" /etc/fstab >/dev/null 2>&1; then
    echo "$fstab_entry" >> /etc/fstab || {
        echo "Error: Failed to update /etc/fstab." >&2
        exit 1
    }
    echo "[+] Added to /etc/fstab for auto-mount at boot"
else
    echo "[+] Mount already exists in /etc/fstab"
fi
