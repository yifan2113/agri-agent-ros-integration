#!/usr/bin/env bash

set -Eeuo pipefail

readonly ROS_KEY_URL="https://raw.githubusercontent.com/ros/rosdistro/master/ros.key"
readonly ROS_KEY_FINGERPRINT="C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654"
readonly ROS_KEYRING="/usr/share/keyrings/ros-archive-keyring.gpg"
readonly ROS_SOURCE_FILE="/etc/apt/sources.list.d/ros1-noetic.list"

if [[ ${EUID} -ne 0 ]]; then
  printf 'Run this script with sudo:\n  sudo bash %q\n' "$0" >&2
  exit 1
fi

source /etc/os-release
if [[ ${ID:-} != "ubuntu" || ${VERSION_CODENAME:-} != "focal" ]]; then
  printf 'Refusing to install: Ubuntu 20.04 (focal) is required.\n' >&2
  exit 1
fi

if [[ "$(dpkg --print-architecture)" != "amd64" ]]; then
  printf 'Refusing to install: this script was validated for amd64 only.\n' >&2
  exit 1
fi

install_root="$(mktemp -d /tmp/agri_ros_install.XXXXXX)"
cleanup() {
  if [[ ${install_root} == /tmp/agri_ros_install.* && -d ${install_root} ]]; then
    rm -rf -- "${install_root}"
  fi
}
trap cleanup EXIT

install -d -m 0755 \
  "${install_root}/lists/partial" \
  "${install_root}/archives/partial"

curl -fL --retry 3 --connect-timeout 20 \
  -o "${install_root}/ros-archive-keyring.gpg" \
  "${ROS_KEY_URL}"

downloaded_fingerprint="$(gpg --show-keys --with-colons "${install_root}/ros-archive-keyring.gpg" 2>/dev/null \
  | awk -F: '$1 == "fpr" { print $10; exit }')"
if [[ ${downloaded_fingerprint} != "${ROS_KEY_FINGERPRINT}" ]]; then
  printf 'Refusing to install: ROS key fingerprint mismatch.\n' >&2
  exit 1
fi

install -d -m 0755 /usr/share/keyrings /etc/apt/sources.list.d
install -m 0644 "${install_root}/ros-archive-keyring.gpg" "${ROS_KEYRING}"

printf '%s\n' \
  "deb [arch=amd64 signed-by=${ROS_KEYRING}] http://packages.ros.org/ros/ubuntu focal main" \
  > "${install_root}/ros1-noetic.list"
install -m 0644 "${install_root}/ros1-noetic.list" "${ROS_SOURCE_FILE}"

# This source set intentionally excludes focal-proposed and all third-party
# repositories, especially ubuntu-toolchain-r/test. It prevents unrelated GCC
# runtime upgrades while ROS is installed.
printf '%s\n' \
  'deb http://repo.huaweicloud.com/ubuntu/ focal main restricted universe multiverse' \
  'deb http://repo.huaweicloud.com/ubuntu/ focal-security main restricted universe multiverse' \
  'deb http://repo.huaweicloud.com/ubuntu/ focal-updates main restricted universe multiverse' \
  'deb http://repo.huaweicloud.com/ubuntu/ focal-backports main restricted universe multiverse' \
  "deb [arch=amd64 signed-by=${ROS_KEYRING}] http://packages.ros.org/ros/ubuntu focal main" \
  > "${install_root}/safe-sources.list"

apt_options=(
  -o "Dir::Etc::sourcelist=${install_root}/safe-sources.list"
  -o 'Dir::Etc::sourceparts=-'
  -o "Dir::State::lists=${install_root}/lists"
  -o "Dir::Cache::archives=${install_root}/archives"
  -o "Dir::Cache::pkgcache=${install_root}/pkgcache.bin"
  -o "Dir::Cache::srcpkgcache=${install_root}/srcpkgcache.bin"
)

packages=(
  ros-noetic-ros-base
  python3-rosdep
  python3-catkin-tools
  build-essential
)

apt-get "${apt_options[@]}" update

simulation="$(LC_ALL=C apt-get --simulate "${apt_options[@]}" install "${packages[@]}")"
printf '%s\n' "${simulation}" \
  | grep -E 'upgraded,|Need to get|After this operation|not upgraded' || true

if ! grep -Eq '^0 upgraded, [0-9]+ newly installed, 0 to remove' <<< "${simulation}"; then
  printf 'Refusing to install: simulation would upgrade or remove existing packages.\n' >&2
  exit 1
fi

if grep '^Inst ' <<< "${simulation}" \
  | grep -Eiq 'nvidia|cuda|linux-image|linux-headers|libc6([ :]|$)|systemd([ :]|$)|libgcc-s1|libstdc\+\+6|docker|tailscale'; then
  printf 'Refusing to install: protected system/GPU packages appeared in the plan.\n' >&2
  exit 1
fi

DEBIAN_FRONTEND=noninteractive apt-get -y "${apt_options[@]}" install "${packages[@]}"

if [[ ! -e /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  /usr/bin/rosdep init
fi

# ROS Noetic's generated setup scripts probe variables before assigning them,
# so nounset must be disabled while the environment is sourced.
set +u
source /opt/ros/noetic/setup.bash
set -u
printf 'ROS distribution: %s\n' "$(rosversion -d)"
printf 'ROS Noetic minimal installation completed.\n'
