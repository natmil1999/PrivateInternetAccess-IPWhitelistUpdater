# PIA IP White-list Updater

### Problem

This tool was created to manage bypasses certain websites using the desktop Private Internet Application, instead of 
needing to use the PIA web extension. 
The Private Internet Access web extension has the functionality of bypasses certain websites, but the web extension 
does not have the same level of granular control over settings like what protocol to use or support for using dedicated IPs, 
but the desktop version of Private Internet Access does not have good support for bypassing certain websites. 
The desktop version of Private Internet Access only allows for bypassing entire applications or bypassing certain 
individually defined IP addresses. It does not support bypassing by domain names. 


### Solution

The solution created to allow for individual domain names to be bypassed by the PIA VPN is to create a txt file 
of domain names to be bypassed—separate from PIA settings—and then continuously fetch the IP addresses for the 
whitelisted domain names and update the PIA settings to bypass those IP addresses.


A command line tool was created to fetch the IP addresses for the domain names in the txt file and update the PIA 
settings to bypass those IP addresses. The command line tool allows for domain names to be added and removed
from the domain name text file, and will list the current whitelisted domain names and IP addresses with commands.

```
CLI Commands:
- start [--interval <seconds>]
    - Starts the IP whitelist updater to run continously based on the interval provided, defaulting to every 15 seconds.
- add <domain name || domainName1,domainName2,domainName3,...>
- remove <domain name || domainName1,domainName2,domainName3,...>
- list-domains
- list-ips
```

### Prerequisites
- Linux OS, tested on POP~OS 20.04 LTS
- PIA VPN Desktop client installed
- Python 3 or greater

### Limitations

The whitelisted IPs are not an ideal way of bypassing websites, as many large websites such as youtube will have
a large number of IP addresses, and the IP addresses will change frequently. This issue can be limited by setting the 
updater to an interval of 1 second, but will still likely cause issues and may result in the domains not being bypassed
constantly.

**This tool in its current form does not guarantee that the whitelisted domains will always be bypassed because of the issue 
with rotating IP addresses used by large websites.**

**There are likely vulnerabilities with this tool, as it is not a secure way of bypassing websites. 
This tool is not intended to be used for sensitive information and should not be used if you need to use the PIA VPN
without any possibility of leaking packets outside the PIA VPN.**