{ config, pkgs, lib, ... }:

{
  imports = [ ../modules/tetris-recorder.nix ];

  # Boot configuration for Raspberry Pi 4
  boot = {
    kernelPackages = pkgs.linuxKernel.packages.linux_rpi4;
    initrd.availableKernelModules = [ "xhci_pci" "usbhid" "usb_storage" ];
    loader = {
      grub.enable = false;
      generic-extlinux-compatible.enable = true;
    };
  };

  # Filesystem
  fileSystems."/" = {
    device = "/dev/disk/by-label/NIXOS_SD";
    fsType = "ext4";
    options = [ "noatime" ];
  };

  # Networking
  networking.hostName = "nix-tetris-recorder";

  # Tetris Recorder service
  services.tetris-recorder = {
    enable = true;
    videoDevice = "/dev/video0";
    fps = 10;
    secretsFile = "/run/keys/bot-secrets.toml";
  };

  # System services
  services = {
    openssh.enable = true;
    tailscale.enable = true;
  };

  # User configuration
  users = {
    mutableUsers = false;
    users.technodzik = {
      isNormalUser = true;
      hashedPasswordFile = "/run/keys/user-password";
      extraGroups = [ "wheel" "video" ];
      shell = pkgs.fish;
    };
  };

  # Packages
  programs.fish.enable = true;

  environment.systemPackages = with pkgs; [
    vim
    htop
    git
    usbutils
  ];

  # Hardware
  hardware.enableRedistributableFirmware = true;

  # Passwordless sudo for wheel group (needed for Colmena deployments)
  security.sudo.wheelNeedsPassword = false;

  # Nix settings
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  system.stateVersion = "24.11";
}
