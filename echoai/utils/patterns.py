#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: pii_patterns.py
# Author: Wadih Khairallah
# Description: 
# Created: 2024-12-02 22:52:20
# Modified: 2025-04-28 11:24:00

# CREDIT CARD NUMBERS
CREDIT_CARD_PATTERNS = [
    # Matches Visa, MasterCard, Amex, Discover, etc.
    r"(?P<credit_card>\b(?:\d[ -]*?){13,16}\b)",

    # Optional: stricter match by known BIN prefixes (Visa starts with 4, MasterCard 51-55 or 2221–2720, etc.)
    r"(?P<credit_card>\b(?:4[0-9]{12}(?:[0-9]{3})?)\b)",  # Visa
    r"(?P<credit_card>\b(?:5[1-5][0-9]{14})\b)",          # MasterCard
    r"(?P<credit_card>\b(?:3[47][0-9]{13})\b)",           # Amex
    r"(?P<credit_card>\b(?:6(?:011|5[0-9]{2})[0-9]{12})\b)", # Discover
]

# PHONE NUMBER PATTERNS (strict, international-aware, no bare digits)
PHONE_PATTERNS = [
    # International (e.g. +44 20 7946 0958, +91-9876543210)
    r"(?P<phone_number>\b\+\d{1,3}[ -.]?\(?\d{1,4}\)?[ -.]?\d{1,4}[ -.]?\d{2,4}[ -.]?\d{2,4}\b)",

    # US/Canada with country code (e.g. 1-123-456-7890, +1 (123) 456-7890)
    r"(?P<phone_number>\b(?:\+?1)[ -.]?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}\b)",

    # US/Canada local (e.g. (123) 456-7890, 123-456-7890, 123.456.7890)
    r"(?P<phone_number>\b\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}\b)"
]


PHONE_PATTERNS = [
    r"(?P<phone_number>\+?\d{1,3}[ -.]*\(?\d{2,4}\)?[ -.]*\d{3,4}[ -.]*\d{4})",
    r"(?P<phone_number>1[ -.]*\(?\d{3}\)?[ -.]*\d{3}[ -.]*\d{4})",
    r"(?P<phone_number>\(?\d{3}\)?[ -.]*\d{3}[ -.]*\d{4})"
    # Removed fallback 10–12 digit pattern
]



# MONTHS
MONTH_PATTERNS = [
    r"\b(?P<month>(?i:January|February|March|April|May|June|July|August|September|October|November|December))\b",
    r"\b(?P<month>(?i:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\b",
]

# WEEKS
WEEK_PATTERNS = [
    r"(?P<week>(?i:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))",
    r"(?P<week>\b(?i:Mon|Tue(s)|Wed|Thu(rs)|Fri|Sat|Sun)\b)",
]

# COMMON DATE TIME
DATETIME_PATTERNS = [
    r"(?P<datetime>\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b)",  # ISO-8601
    r"(?P<datetime>\d{4}(/|-)(?:0[1-9]|1[0-2])(/|-)(?:0[1-9]|[12][0-9]|3[01])\b)",
    r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9](:)(?:[0-5][0-9]|60)\b)",
    r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9]\b)",
    r"(?P<datetime>\b(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\b))",  # Standard datetime
    r"(?P<datetime>\b\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\b)",  # Special datetime
    r"(?P<datetime>(?:[01][0-9]|2[0-3])(:)[0-5][0-9]\b)",
    r"(?P<datetime>(?:(\d{2}){2}\d{4} (\d{2}:){3}))",
]

# COMMON DATE
DATE_PATTERNS = [
    r"\b(?P<date>\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
    r"\b(?P<date>\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",
    r"\b(?P<date>(?i:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}(st|nd|rd|th)\s\d{4})\b",
    r"\b(?P<date>(?i:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2}(st|nd|rd|th)\s\d{4})\b",
]

# COMMON TIME
TIME_PATTERNS = [
    r"\b(?P<time>\d{2}(:|\.)\d{2}((:|\.)\d{2,4}|))\b",
    r"\b(?P<time>(\d{2}(\.|:)|)\d{1,2}(?i:am|pm))\b",
]

# IPV4
IPV4_PATTERNS = [
    r"\b(?P<ipv4>(?:(\d{1,3}\.){3}\d{1,3}(\/\d{1,2}\b|\/|)))",  # IPv4 pattern
]

# MAC ADDRESSES
MACADDRESS_PATTERNS = [
    r"\b(?P<mac_address>([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})\b",
    r"\b(?P<mac_address>[0-9a-fA-F]{12})\b",
    r"\b(?P<mac_address>([0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4})",
]

# IPV6
IPV6_PATTERNS = [
    # Fully expanded (8 groups)
    r"(?P<ipv6>\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b)",

    # Compressed (::) with 1–6 groups around it
    r"(?P<ipv6>\b(?:[A-Fa-f0-9]{1,4}:){1,7}:|:(?::[A-Fa-f0-9]{1,4}){1,7}\b)",

    # Compressed with optional embedded IPv4
    r"(?P<ipv6>\b(?:[A-Fa-f0-9]{1,4}:){6,6}(?:\d{1,3}\.){3}\d{1,3}\b)",

    # Link-local with zone index
    r"(?P<ipv6>\bfe80::[A-Fa-f0-9:%]{1,}\b)"
]

# COMMON TECH TERM CATAGORIES
TERM_PATTERNS = [
    r"\b(?P<protocol>(?i:dns|http|https|ftp|ssh|tcp|ip|udp|ssl|smtp|telnet|ipv4|ipv6|icmp|arp|pop3|imap|smb|nfs|dhcp|tftp|ldap|snmp|sctp|bgp|ospf|rsvp|rtp|rdp|lldp|sip|pim|mpls|gre|ppp|pptp|l2tp|ipsec|nat|stp|rip|eigrp|http2|spdy|quic|sctp|ntp|kerberos|radius|gopher|mqtt|coap|amqp))\b",
    r"\b(?P<language>(?i:python|javascript|java|c\+\+|c#|ruby|perl|php|swift|kotlin|go|rust|typescript|scala|r|matlab|bash|shell|powershell|html|css|sql|dart|elixir|erlang|haskell|clojure|f#|visual\s*basic|fortran|cobol|assembly|lisp|prolog|vhdl|verilog|sas|groovy|smalltalk|tcl|awk|ada|pascal|delphi|nim|julia|crystal|objective-c|postscript|apl|scratch|logo|abap|pl/sql))\b",
    r"\b(?P<file_format>(?i:txt|pdf|doc|docx|xls|xlsx|csv|json|xml|yaml|html|md|ppt|pptx|png|jpg|jpeg|gif|bmp|tiff|svg|mp3|wav|flac|aac|ogg|mp4|mkv|avi|mov|wmv))\b",
    r"\b(?P<os>(?i:windows|linux|macos|ios|android|ubuntu|debian|redhat|centos|fedora|arch|kali|alpine|unix|solaris|bsd|freebsd))\b",
    r"\b(?P<web_tech>(?i:react|angular|vue|svelte|next\.js|nuxt\.js|node\.js|django|flask|express|spring|rails|laravel|webpack|gulp|grunt|babel|eslint|graphql|rest|soap|ajax))\b",
    r"\b(?P<cloud_devops>(?i:aws|azure|gcp|digitalocean|heroku|jenkins|travis|circleci|gitlab-ci|github-actions|docker|kubernetes|helm|podman|rancher|prometheus|grafana|nagios|zabbix|ansible|terraform|puppet|chef))\b",
    r"\b(?P<database>(?i:mysql|postgresql|sqlite|oracle|mssql|mongodb|cassandra|couchdb|redis|dynamodb|influxdb|timescale|opentsdb|neo4j|janusgraph|dgraph))\b",
    r"\b(?P<cybersecurity>(?i:firewall|vpn|antivirus|malware|ransomware|phishing|zero-day|nmap|metasploit|wireshark|kali|burp|nessus|ossec|tls|ssl|ipsec|oauth|saml|fido2|nist|iso27001|cobit))\b",
    r"\b(?P<hardware>(?i:cpu|gpu|ram|ssd|hdd|motherboard|psu|intel|amd|nvidia|asus|dell|lenovo|hp|keyboard|mouse|monitor|printer|router))\b",
    r"\b(?P<networking>(?i:router|switch|modem|firewall|access point|lan|wan|vpn|dns|dhcp|nat|subnet))\b",
    r"\b(?P<ml_ai>(?i:tensorflow|keras|pytorch|sklearn|xgboost|lightgbm|cnn|rnn|gan|transformer|bert|gpt|svm|mlflow|kubeflow|airflow))\b",
    r"\b(?P<version_control>(?i:git|svn|mercurial|cvs|bitbucket|github|gitlab))\b",
    r"\b(?P<mobile_dev>(?i:swift|kotlin|objective-c|flutter|react-native|xamarin|cordova|ionic))\b",
    r"\b(?P<blockchain>(?i:bitcoin|ethereum|dogecoin|litecoin|solana|polkadot|hyperledger|cosmos|nft|smart-contract|dapp|defi))\b",
    r"\b(?P<game_dev>(?i:unity|unreal|godot|cryengine|c#|c\+\+|lua|python|panda3d|monogame))\b"
]

# MISC PATTERNS
MISC_PATTERNS = [
    r"(?P<unix_path>(?:[ \t\n]|^)/(?:[a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+)",
    r"(?P<windows_path>([a-zA-Z]:\\)[\w\\.-]+)",  # Windows file paths
    r"(?P<email>[\w.-]+@([\w-]+\.)+[\w-]+)",  # Email addresses
    r"(?P<ini>\[\w+\])",                     # INI sections
    #r"(?P<json>{.*?}|\[.*?\])",              # JSON-like objects
    r"(?P<hex_number>\b0x[0-9a-fA-F]+\b)",   # Hexadecimal numbers
    r"(?P<env_var>\$[\w]+|%[\w]+%)",         # Environment variables
    r"(?P<uuid>\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b)",  # UUIDs
    r"(?P<vin_number>\b[A-HJ-NPR-Z0-9]{17}\b)",
    r"(?P<temperature>\b-?\d+(\.\d+)?[°]?[CF]\b)"
]

# URL PATTERNS (Comprehensive RFC3986-style, all schemes)
URL_PATTERNS = [
    r"(?P<url>[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>\]\[(){}\"']+)"
]


DOCUMENT_ANALYSIS_PATTERNS = [
    # Interrogative context with surrounding words
    #r"(?P<interrogative_context>(?:\b\w+\b\s+){2,5}\b(how|why|what|when|where|who)\b(?:\s+\b\w+\b){2,5})",

    # Reporting statements with surrounding context
    #r"(?P<reporting_statement>(?:\b\w+\b\s+){2,5}\b\w+(?:\s\w+)*\s+(said|stated|reported|mentioned|claimed|explained|noted|suggested)\b(?:\s+\".*?\"|\s+\b.*?\b[.!?]))",

    # Entity names after relational prepositions with meaningful context
    #r"(?P<entity_name>(?:\b\w+\b\s+){2,5}\b(by|from|to|with|about|for)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)(?:\s+\b\w+\b){2,5})",

    # All-caps phrases with contextual information
    #r"(?P<all_caps_phrase>(?:\b\w+\b\s+){2,5}\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b(?:\s+\b\w+\b){2,5})",

    # Quoted text with nearby context
    #r"(?P<quoted_text>(?:\b\w+\b\s+){2,5}\".*?\"(?:\s+\b\w+\b){2,5})",

    # Action contexts with surrounding context
    #r"(?P<action_context>(?:\b\w+\b\s+){2,5}\b\w+(?:\s+\w+)*\s+(completed|developed|initiated|threatened|investigated)\s+\b.*?[.!?](?:\s+\b\w+\b){2,5})",

    # Possessive context with nearby context
    #r"(?P<possessive_context>(?:\b\w+\b\s+){2,5}(\b[A-Z][a-z]+(?:'s|’s)\s+\w+)|\b(owned by|reported by|handled by)\s+([A-Z][a-z]+)(?:\s+\b\w+\b){2,5})",

    # Proper nouns with meaningful surroundings
    #r"(?P<proper_noun>(?:\b\w+\b\s+){2,5}\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b(?:\s+\b\w+\b){2,5})",

    # Adjectives indicating criticality or importance with nearby context
    #r"(?P<adjective_context>(?:\b\w+\b\s+){2,5}\b(critical|urgent|significant|dangerous|illegal|fraudulent)\b\s+\w+(?:\s+\b\w+\b){2,5})",

    # Question context with sufficient surrounding words
    #r"(?P<question_context>(?:\b\w+\b\s+){2,5}\b(who|what|why|how|where|when)\b(?:\s+\b\w+\b){2,5}[?])",

    # Numbers with measurement terms and context
    #r"(?P<number_context>(?:\b\w+\b\s+){2,5}\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s+(units|percent|completion|days|weeks))?\b(?:\s+\b\w+\b){2,5})",

    # Threat-related phrases with meaningful context
    #r"(?P<threat_context>(?:\b\w+\b\s+){2,5}(threat|risk|danger|exploit)(?:\s+\b\w+\b){2,5}[.!?])",
]

# SOCIAL SECURITY NUMBERS (US)
SOCIAL_SECURITY_PATTERNS = [
    r"(?P<social_security>\b\d{3}-\d{2}-\d{4}\b)",
    r"(?P<social_security>\b\d{3} \d{2} \d{4}\b)",
    r"(?P<social_security>\b\d{9}\b)",
]

# BANK ACCOUNT NUMBERS
BANK_ACCOUNT_PATTERNS = [
    # General numeric account numbers (6–18 digits) — covers U.S., UK, India, etc.
    r"(?P<bank_account>\b\d{6,18}\b)",

    # IBAN — up to 34 alphanumeric characters, usually starting with country code
    r"(?P<bank_account>\b[A-Z]{2}[0-9A-Z]{13,32}\b)",

    # CLABE (Mexico) — 18-digit account number
    r"(?P<bank_account>\b\d{18}\b)",

    # Swiss PostFinance — 12-digit account
    r"(?P<bank_account>\b\d{12}\b)",
]

# ROUTING NUMBERS / SORT CODES / BRANCH CODES
ROUTING_NUMBER_PATTERNS = [
    r"(?P<routing_number>\b\d{6}\b)",   # UK Sort Code, Australian BSB, South African branch code
    r"(?P<routing_number>\b\d{8}\b)",   # German BLZ
    r"(?P<routing_number>\b\d{9}\b)",   # U.S. & Canadian Routing Numbers
    r"(?P<routing_number>\b\d{12}\b)",  # Indian IFSC (note: format is more complex, could refine later)
    r"(?P<routing_number>\b\d{18}\b)",  # CLABE (can also go under bank account, but included here)
    r"(?P<routing_number>\b\d{23}\b)",  # French RIB Key
]

# SWIFT / BIC CODES
SWIFT_CODE_PATTERNS = [
    r"(?P<swift_code>\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b)",  # Matches both 8 and 11 character codes
]

# PASSPORT NUMBERS (MULTI-COUNTRY)
PASSPORT_PATTERNS = [
    r"(?P<passport_number>\b[A-Z]{2}[0-9]{7}\b)",     # US, Australia, Japan
    r"(?P<passport_number>\b[A-Z]{2}[0-9]{6}\b)",     # Canada, Mexico, Brazil
    r"(?P<passport_number>\b[A-Z]{1}[0-9]{8}\b)",     # India, China, South Korea
    r"(?P<passport_number>\b[0-9]{9}\b)",             # Russia
    r"(?P<passport_number>\b[A-Z0-9]{9}\b)",          # UK, Germany, France
]

# OTHER MISC NUMBER PATTERNS
ANALYZE_PATTERNS = [
    #r"(?P<analyze>\b[A-Za-z0-9]{20,100}\b)",
    #r"\b(?P<analyze>(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6,20}\b)",
    #r"\b(?P<analyze>\d{8,20}\b)",
    #r"\b(?P<analyze>[A-Z]{8,20}\b)",
    #r"\b(?P<analyze>(?:[A-Za-z0-9]{2}[,:|.-]([A-Za-z0-9]{2}|)){4,20})\b",
]

# POSTAL / ZIP CODE PATTERNS (US + international)
POSTAL_CODE_PATTERNS = [
    r"(?P<postal_code>\b\d{5}-\d{4}\b)",                         # US ZIP+4
    r"(?P<postal_code>\b\d{5}\b)",                               # US standard ZIP
    r"(?P<postal_code>\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b)", # Canadian
    r"(?P<postal_code>\b\d{2}-\d{3}\b)",                         # Polish
    r"(?P<postal_code>\b[A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s?\d[A-Za-z]{2}\b)",  # UK
    r"(?P<postal_code>\b\d{3}-\d{4}\b)",                         # Japan/Korea
    r"(?P<postal_code>\b\d{6}\b)",                               # India
]

PATTERNS = (
    DOCUMENT_ANALYSIS_PATTERNS +
    TERM_PATTERNS +
    ANALYZE_PATTERNS +
    MONTH_PATTERNS +
    TIME_PATTERNS +
    MACADDRESS_PATTERNS +
    DATE_PATTERNS +
    WEEK_PATTERNS +
    IPV6_PATTERNS +
    IPV4_PATTERNS +
    PHONE_PATTERNS +
    DATETIME_PATTERNS +
    MISC_PATTERNS +
    SOCIAL_SECURITY_PATTERNS +
    CREDIT_CARD_PATTERNS +
    BANK_ACCOUNT_PATTERNS +
    ROUTING_NUMBER_PATTERNS +
    SWIFT_CODE_PATTERNS +
    PASSPORT_PATTERNS +
    POSTAL_CODE_PATTERNS +
    URL_PATTERNS
)

