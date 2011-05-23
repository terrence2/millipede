'''
Copyright (c) 2011, Terrence Cole.
All rights reserved.
'''
import os
import sys


####
# Some modules only get installed on some platforms.  When not installed, don't expect them;
#		presumably, code that uses these on other platforms is guarded and won't execute at runtime.
####
MISSING_QUIRKS = {
			'sets': ['ImmutableSet']
			}
if os.name != 'java': #FIXME: how do we detect java for real?
	MISSING_QUIRKS.update({
			'java': ['lang'],
			'java.lang': ['System'],
			'org': ['python'],
			'org.python': ['core'],
			'org.python.core': ['PyStringMap'],
			})
if sys.platform != 'darwin':
	MISSING_QUIRKS.update({
			'_gestalt': ['gestalt'],
			'_scproxy': ['_get_proxy_settings', '_get_proxies'],
			'EasyDialogs': ['AskPassword'],
			})
if os.name != 'ce':
	MISSING_QUIRKS.update({
			'ce': ['_exit'],
			})
if os.name != 'nt':
	MISSING_QUIRKS.update({
			'nt': ['_exit', '_getfullpathname', '_getfileinformation', '_getfinalpathname'],
			})
if os.name not in ('nt', 'ce'):
	MISSING_QUIRKS.update({
			'_subprocess': ['CREATE_NEW_CONSOLE'],
			'win32api': ['RegOpenKeyEx', 'RegQueryValueEx', 'GetVersionEx', 'RegCloseKey'],
			'win32con': ['VER_PLATFORM_WIN32_NT', 'VER_PLATFORM_WIN32_WINDOWS', 'HKEY_LOCAL_MACHINE', 'VER_NT_WORKSTATION'],
			})
if os.name != 'os2':
	MISSING_QUIRKS.update({
			'_emx_link': ['link'],
			'os2': ['_exit'],
			})
if sys.version_info.minor < 2:
	MISSING_QUIRKS.update({
			'sysconfig': ['get_platform'],
			})


####
# Extend builtin missing quirks with installed extra quirks.
####
import json
extradir = os.path.join('data', 'quirks', 'missing')
for filename in os.listdir(extradir):
	with open(os.path.join(extradir, filename), 'r') as fp:
		quirks = json.load(fp)
		MISSING_QUIRKS.update(quirks)


####
# Some modules only export certain symbols on some platforms.
####
MODULE_QUIRKS = {}
if os.name not in ('nt', 'ce'):
	MODULE_QUIRKS.update({
			'_ctypes': ['FUNCFLAG_STDCALL', 'get_last_error', 'set_last_error', 'LoadLibrary', 'FormatError', '_check_HRESULT'],
			'_multiprocessing': ['PipeConnection', 'win32'],
			#'_subprocess': ['win32'],
			})

def remove_expected_missing(missing):
	skips = set()
	for qualified_sym in missing:
		pkg, _, sym = qualified_sym.rpartition('.')
		for quirk_pkg, quirk_syms in MODULE_QUIRKS.items():
			for quirk_sym in quirk_syms:
				if pkg == quirk_pkg and sym == quirk_sym:
					skips.add(qualified_sym)

	return missing - skips
