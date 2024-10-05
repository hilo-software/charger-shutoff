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

log_file = LOG_FILE
logger = None
plug: SmartDevice = None

def fn_name():
    return inspect.currentframe().f_back.f_code.co_name

async def init(target_plug: str) -> SmartDevice:
    '''
    async function.  Uses kasa library to discover and find target device matching target_plug alias.

    Returns:
        True if plug is found
    '''
    found = await Discover.discover()
    for smart_device in found.values():
        await smart_device.update()
        if smart_device.alias == target_plug:
            return smart_device
    return None

def get_power(plug: SmartDevice) -> float:
    return plug.emeter_realtime.power

def is_charging(plug: SmartDevice) -> bool:
    power: float = get_power(plug)
    logger.info(f"{fn_name()}: power: {power}")
    return power > CUTOFF_POWER

async def main_loop(target_plug: str) -> bool:
    plug_found: SmartDevice = await init(target_plug)
    if not plug_found:
        return False
    logger.info(f"plug: {target_plug}, power: {plug_found.emeter_realtime.power}")
    while is_charging(plug_found):
        await asyncio.sleep(PROBE_INTERVAL_SECS)
        await plug_found.update()
    await plug_found.turn_off()
    await plug_found.update()
    logger.info(f"plug is off: {plug_found.is_off}")
    return True

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
        '-q', '--quiet_mode',
        action='store_true',
        help='reduces logging'
    )
    return parser


def main() -> None:
    global log_file, logger

    parser = init_argparse()
    args = parser.parse_args()

    # set up default logging
    if args.log_file_name != None:
        log_file = args.log_file_name

    logger = init_logging(log_file)

    target_plug = args.plug_name
    logger.info(f'>>>>> START plug: {args.plug_name} <<<<<')
    success = asyncio.run(main_loop(args.plug_name))
    logger.info(f'>>>>> FINI plug: {args.plug_name}, status: {success} <<<<<')

if __name__ == '__main__':
    main()