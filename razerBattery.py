#!/bin/env python3
from re import S
import time
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator, GObject
from plyer import notification
import threading
from openrazer.client import DeviceManager
import os

LOW_POWER = 46
REFRESH_TIME_INTERVAL = 3


class RazerStatus(threading.Thread):
    stopthread = threading.Event()

    def __init__(self):
        threading.Thread.__init__(self)
        self.battery_level = -1
        self.is_charging = False
        self.name = ""
        self.haveNotification = False

    def run(self):
        while not self.stopthread.is_set():
            battery_level_before = self.battery_level
            self.getBatteryStatus()
            global RAZER_STATUS_LABEL
            RAZER_STATUS_LABEL.set_label(
                "{} {}% {}".format(
                    self.name,
                    str(self.battery_level),
                    "charging" if self.is_charging else "not charging",
                )
            )
            # If you charge the mouse, the driver does not recognize it immediately.
            if abs(battery_level_before - self.battery_level) > 10:
                time.sleep(3)
                continue
            # print(
            #     "{} {}% {}".format(
            #         self.name,
            #         str(self.battery_level),
            #         "charging" if self.is_charging else "not charging",
            #     )
            # )
            self.sendNotification()
            time.sleep(2)

    def sendNotification(self):
        if (
            not self.is_charging
            and self.battery_level >= 0
            and self.battery_level < LOW_POWER
            and not self.haveNotification
        ):
            notification.notify(
                title="Razer Mouse Low Battery",
                message="{}%".format(self.battery_level),
                app_icon=r"/home/icespite/Work/PycharmProjects/RazerViperUltimate-Battery-Status/razer-logo.png",
                timeout=60,
            )
            self.haveNotification = True

    def getBatteryStatus(self):
        try:
            device_manager = DeviceManager()
            # print(device_manager.devices)
            tmp_is_charging = False
            tmp_battery_level = -1
            tmp_name = ""
            for device in device_manager.devices:
                tmp_name = device.name
                tmp_is_charging = device.is_charging | tmp_is_charging
                tmp_battery_level = max(device.battery_level, tmp_battery_level)
            self.is_charging = tmp_is_charging
            self.battery_level = tmp_battery_level
            self.name = tmp_name
        except Exception as e:
            print(e)

    def stop(self):
        self.stopthread.set()


razerStatus = RazerStatus()
RAZER_STATUS_LABEL = None


def quit(_):
    print("Quitting...")
    razerStatus.stop()
    gtk.main_quit()


def menu():
    menu = gtk.Menu()

    razer_status_label = gtk.MenuItem()
    razer_status_label.set_label("loading...")
    menu.append(razer_status_label)

    exittray = gtk.MenuItem()
    exittray.set_label("Exit Tray")
    exittray.connect("activate", quit)
    menu.append(exittray)

    menu.show_all()
    return (menu, razer_status_label)


def main():
    print("Running Razer Tray...")
    indicator = appindicator.Indicator.new(
        "myrazertray",
        r"/home/icespite/Work/PycharmProjects/RazerViperUltimate-Battery-Status/razer-logo.png",
        appindicator.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    global RAZER_STATUS_LABEL
    (myMenu, RAZER_STATUS_LABEL) = menu()
    indicator.set_menu(myMenu)
    razerStatus.start()
    gtk.main()
    return


def clearOldDaemon():
    f = os.popen("ps -ef |grep openrazer-daemon")
    print(f.read())
    f = os.popen("ps -ef |grep openrazer-daemon |wc -l")
    old_daemon_num = int(f.read())
    if old_daemon_num > 2:
        print("clear old daemon which number is {}".format(old_daemon_num))
        os.system("killall openrazer-daemon")
        time.sleep(2)
    f = os.popen("ps -ef |grep openrazer-daemon")
    print(f.read())


if __name__ == "__main__":
    # Sometimes clearOldDaemon can help you solve the problem.
    # clearOldDaemon()
    main()
