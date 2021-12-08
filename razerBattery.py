#!/bin/env python3
import time

from plyer import notification
import threading
import asyncio
from openrazer.client import DeviceManager
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator

LOW_POWER = 46
REFRESH_TIME_INTERVAL = 3


class TrackStatus:
    def __init__(self):
        self.isRunning = True
        self.isWarned = False

    def getIsRunning(self):
        return self.isRunning

    def setNotRunning(self):
        self.isRunning = False

    def setIsWarned(self, isWarned):
        self.isWarned = isWarned

    def getIsWarned(self):
        return self.isWarned


status = TrackStatus()


def getBatteryStats():
    device_manager = DeviceManager()
    viper = None
    try:
        for device in device_manager.devices:
            # print(device,device.name,device.battery_level)
            if "Razer Viper Ultimate (Wired)" == device.name:
                viper = device
                break
            elif "Razer Viper Ultimate (Wireless)" == device.name:
                viper = device
        # print("-"*20)
        # fix power equal zero when change to wired
        if viper.battery_level ==0:
            time.sleep(3)
            device_manager = DeviceManager()
            for device in device_manager.devices:
                if "Razer Viper Ultimate (Wired)" == device.name:
                    viper = device
                    break
                elif "Razer Viper Ultimate (Wireless)" == device.name:
                    viper = device

        if None == viper:
            return False, -1, "not found viper"

        isCharging = False
        if viper.is_charging:
            isCharging = True
        if viper.is_charging and viper.battery_level > LOW_POWER:
            status.setIsWarned(False)

        return isCharging, viper.battery_level, None
    except Exception as e:
        print(e)
        return False, -1, e


def sendNotification(isCharging, percentage):
    if not isCharging and percentage < LOW_POWER and not status.getIsWarned():
        notification.notify(
                # title of the notification,
                title="Razer Mouse Low Battery",
                # the body of the notification
                message="{}%".format(percentage),
                # creating icon for the notification
                # we need to download a icon of ico file format
                app_icon=r"/home/icespite/Work/PycharmProjects/RazerViperUltimate-Battery-Status/razer-logo.png",
                # the notification stays for 10sec
                timeout=60
            )
        status.setIsWarned(True)


async def refreshBatteryStatus(razer_command):
    while status.getIsRunning():
        (isCharging, percentage, errMsg) = getBatteryStats()
        if errMsg == None:
            chargeText = "Charging" if isCharging else "Not Charging"
            new_label = "Razer Mouse: {} {}%".format(chargeText, str(percentage))
            razer_command.set_label(new_label)
            sendNotification(isCharging, percentage)
            await asyncio.sleep(REFRESH_TIME_INTERVAL)
        else:
            new_label = "{}".format(errMsg)
            razer_command.set_label(new_label)
            await asyncio.sleep(REFRESH_TIME_INTERVAL)


def quit(_):
    status.setNotRunning()
    print('Quitting...')
    gtk.main_quit()


def menu():
    menu = gtk.Menu()

    razer_command = gtk.MenuItem()
    razer_command.set_label(str(getBatteryStats()[1]))
    menu.append(razer_command)

    exittray = gtk.MenuItem()
    exittray.set_label('Exit Tray')
    exittray.connect('activate', quit)
    menu.append(exittray)

    menu.show_all()
    return (menu, razer_command)


def runGtk():
    gtk.main()


async def main():
    print('Running Razer Tray...')

    indicator = appindicator.Indicator.new(
        "myrazertray",
        r"/home/icespite/Work/PycharmProjects/RazerViperUltimate-Battery-Status/razer-logo.png",
        appindicator.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    (myMenu, razer_command) = menu()
    indicator.set_menu(myMenu)

    x = threading.Thread(target=runGtk)
    x.start()
    await refreshBatteryStatus(razer_command)

    print('Closing Razer Tray...')


if __name__ == '__main__':
    asyncio.run(main())
