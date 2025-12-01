@echo off
echo Packaging Tandy 1000 EX Display Driver...

    echo Error: TNDY16.DRV not found! Please run build_driver.bat first.
    goto end
)

if not exist DISK1 mkdir DISK1
copy TNDY16.DRV DISK1\
copy oemsetup.inf DISK1\

echo Package created in DISK1 directory.
echo You can now use this directory as the driver disk during Windows 3.0 Setup.
:end
