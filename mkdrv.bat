rem Link the Tandy 16-color driver using Windows 3.0 libraries
rem Include LIBENTRY to route startup through LibMain/WEP instead of WinMain
link dllentry.obj enable.obj tgavid.obj, tndy16.drv,, libw sdllcew gdi kernel user, tndy16.def
