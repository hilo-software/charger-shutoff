#!/usr/bin/python3

import asyncio
from kasa import Discover, SmartDevice
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import logging
import argparse
from typing import Set, Union, ForwardRef, Dict, List, Optional
from os.path import isfile
from enum import Enum
import configparser
import traceback
from math import ceil
from dataclasses import dataclass
import atexit
import signal
import sys
import inspect
import bisect

LOG_FILE = "shutoff_plug.log"
CUTOFF_POWER = 3.0
PROBE_INTERVAL_SECS = 5 * 60
PLUG_SETTLE_TIME_SECS = 10
RETRY_MAX = 3
RETRY_SLEEP_DELAY = 30

log_file = LOG_FILE
logger = None
plug: SmartDevice = None
auto_on: bool = False
cutoff_power = CUTOFF_POWER

def fn_name():
    return inspect.currentframe().f_back.f_code.co_name

async def init(target_plug: str) -> SmartDevice:
    '''
    async function.  Uses kasa library to discover and find target device matching target_plug alias.

    Returns:
        True if plug is found
    '''
    global auto_on
    found = await Discover.discover()
    for smart_device in found.values():
        await smart_device.update()
        if smart_device.alias == target_plug:
            if auto_on and not smart_device.is_on:
                if not await turn_on(smart_device):
                    return None
                logger.info(f"plug: was off, now successfully turned on so we delay {PLUG_SETTLE_TIME_SECS} seconds to allow power to settle")
                await asyncio.sleep(PLUG_SETTLE_TIME_SECS)
                await smart_device.update()
            return smart_device
    return None

async def turn_on(plug: SmartDevice) -> bool:
    await plug.turn_on()
    await plug.update()
    return plug.is_on

def get_power(plug: SmartDevice) -> float:
    return plug.emeter_realtime.power

def is_charging(plug: SmartDevice) -> bool:
    global cutoff_power
    power: float = get_power(plug)
    logger.info(f"{fn_name()}: power: {power}")
    return power > cutoff_power

async def main_loop(target_plug: str) -> bool:
    plug_found: SmartDevice = await init(target_plug)
    if not plug_found:
        return False
    logger.info(f"plug: {target_plug}, power: {plug_found.emeter_realtime.power}")
    retry_ct = 0
    normal_finish = False
    while not normal_finish and retry_ct < RETRY_MAX:
        try:
            while is_charging(plug_found):
                await asyncio.sleep(PROBE_INTERVAL_SECS)
                await plug_found.update()
            await plug_found.turn_off()
            await plug_found.update()
            normal_finish = True
            logger.info(f"plug is off: {plug_found.is_off}")
        except Exception as e:
            # Treat this as a network issue, retry after sleep up to RETRY_MAX attempts
            retry_ct = retry_ct + 1
            logger.error(f'ERROR, unexpected exit from main_loop: {e}, retry_ct: {retry_ct}')
            await asyncio.sleep(RETRY_SLEEP_DELAY)
    return normal_finish

def setup_logging_handlers(log_file: str) -> list:
    try:
        logging_file_handler = logging.FileHandler(filename=log_file, mode='w')
    except (IOError, OSError, ValueError, FileNotFoundError) as e:
        print(f'ERROR -- Could not create logging file: {log_file}, e: {str(e)}')
        logging_handlers = [
            logging.StreamHandler()
        ]
        return logging_handlers
    except Exception as e:
        print(f'ERROR -- Unexpected Exception: Could not create logging file: {log_file}, e: {str(e)}')
        logging_handlers = [
            logging.StreamHandler()
        ]
        return logging_handlers

    logging_handlers = [
        logging_file_handler,
        logging.StreamHandler()
    ]
    return logging_handlers

def init_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # Create formatter with the specified date format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging_handlers = setup_logging_handlers(log_file)
    for handler in logging_handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def init_argparse() -> argparse.ArgumentParser:
    '''
    Initializes ArgumentParser for command line args when the script
    is used in that manner.

    Returns:
        argparse.ArgumentParser: initialized argparse
    '''
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='Shut off TP-Link smart socket'
    )
    parser.add_argument('plug_name', help="TPLink Smart Plug Name")
    parser.add_argument(
        '-v', '--version', action='version',
        version=f'{parser.prog} version 1.0.0'
    )
    parser.add_argument(
        '-t', '--test_mode',
        action='store_true',
        help='test mode only, verify early stages, no real plug activity'
    )
    parser.add_argument(
        '-l', '--log_file_name', metavar='',
        help='overrides logfile name, default is battery_plug_controller.log'
    )
    parser.add_argument(
        '-c', '--cutoff_power', metavar='',
        help='overrides cutoff_power, default is 3.0'
    )
    parser.add_argument(
        '-q', '--quiet_mode',
        action='store_true',
        help='reduces logging'
    )
    parser.add_argument(
        '-a', '--auto_on', action="store_true",
        help='turn on plug at start if not yet on'
    )
    return parser


def main() -> None:
    global log_file, logger, auto_on, cutoff_power

    parser = init_argparse()
    args = parser.parse_args()

    # set up default logging
    if args.log_file_name != None:
        log_file = args.log_file_name
    # set auto_on if present
    if args.auto_on:
        auto_on = args.auto_on
    if args.cutoff_power != None:
        try:
            cutoff_power = float(
                args.cutoff_power)
            print(
                f'>>>>> OVERRIDE cutoff_power: {str(cutoff_power)}')
        except (ValueError, TypeError, OverflowError) as e:
            print(f'ERROR, Invalid cutoff_power: {str(e)}')

    logger = init_logging(log_file)

    target_plug = args.plug_name
    logger.info(f'>>>>> START plug: {args.plug_name} <<<<<')
    success = asyncio.run(main_loop(args.plug_name))
    logger.info(f'>>>>> FINI plug: {args.plug_name}, status: {success} <<<<<')

if __name__ == '__main__':
    main()