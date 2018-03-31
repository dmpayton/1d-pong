# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import network

sta_if = network.WLAN(network.STA_IF)
sta_if.active(False)

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

gc.collect()
